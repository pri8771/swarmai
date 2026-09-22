"""V2B-004b / ART-V17 — consequential ToolGateway pipeline.

Order: normalize → authorize → policy/risk → exact approval → reserve effect →
execute adapter → pre/post evidence → reconcile → expose authorized artifacts only.

Unknown external outcome enters reconciliation; never blind-retry.
"""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any

from swarm.contracts.actions import (
    ActionEnvelope,
    ActionReceiptV17,
    ApprovalGrant,
)
from swarm.contracts.common import new_id, payload_hash, utc_now
from swarm.db.lease_fencing import LeaseClaimError
from swarm.tools.adapters.base import (
    ADAPTER_OUTCOMES,
    AdapterDeniedError,
    AdapterNotSentError,
    IntegrationAdapter,
)
from swarm.tools.effects import (
    DurableEffectRepository,
    EffectConflictError,
    EffectStoreError,
    InMemoryEffectStore,
    check_effect_binding,
)
from swarm.tools.fences import ActorContext, FenceProvider, PolicyProvider


class ToolAuthorizationError(PermissionError):
    pass


class ApprovalInvalidError(PermissionError):
    pass


class StaleLeaseError(PermissionError):
    pass


class CancellationFenceError(PermissionError):
    pass


class PolicyDeniedError(PermissionError):
    pass


class ReconciliationRequiredError(RuntimeError):
    pass


class ConsequentialToolGateway:
    """V1.7 ToolGateway over ActionEnvelope + IntegrationAdapter + EffectStore."""

    def __init__(
        self,
        *,
        adapter: IntegrationAdapter,
        store: InMemoryEffectStore | DurableEffectRepository,
        fences: FenceProvider,
        policy: PolicyProvider,
        max_risk_without_approval: str = "low",
        orphan_grace_seconds: int = 30,
    ) -> None:
        if orphan_grace_seconds < 0:
            raise ValueError("invalid_recovery_window")
        self.orphan_grace_seconds = orphan_grace_seconds
        self.adapter = adapter
        self.fences = fences
        self.policy = policy
        self.store = store
        self.max_risk_without_approval = max_risk_without_approval
        self._risk_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}

    def put_approval(self, grant: ApprovalGrant, *, context: ActorContext) -> ApprovalGrant:
        if grant.project_id != context.project_id:
            raise ApprovalInvalidError("approval_project_mismatch")
        return self.store.put_approval(grant)

    def revoke_approval(self, approval_id: str, *, context: ActorContext, reason: str) -> bool:
        return self.store.revoke_approval(
            project_id=context.project_id,
            approval_id=approval_id,
            revoked_by=context.actor,
            reason=reason,
        )

    def make_approval(
        self,
        envelope: ActionEnvelope,
        *,
        context: ActorContext,
        grantor: str = "operator",
        expires_in_seconds: int = 300,
        max_effect_count: int = 1,
    ) -> ApprovalGrant:
        self._authorize_context(envelope, context)
        envelope.ensure_hashes()
        now = utc_now()
        grant = ApprovalGrant(
            project_id=envelope.project_id,
            grantor=grantor,
            actor=envelope.actor,
            integration_id=envelope.integration_id,
            integration_version=envelope.integration_version,
            operation=envelope.operation,
            destination=envelope.destination,
            payload_hash=envelope.payload_hash,
            effect_key=envelope.effect_key,
            max_effect_count=max_effect_count,
            expires_at=now + timedelta(seconds=expires_in_seconds),
            policy_version=envelope.policy_version,
        )
        return self.put_approval(grant, context=context)

    async def execute_request(
        self, request: dict[str, Any], *, context: ActorContext
    ) -> ActionReceiptV17:
        # 1) normalize
        envelope = self.adapter.normalize(request)
        return await self.execute_envelope(envelope, context=context)

    async def execute_envelope(
        self, envelope: ActionEnvelope, *, context: ActorContext
    ) -> ActionReceiptV17:
        self._authorize_context(envelope, context)
        envelope = self._effective_envelope(envelope)
        envelope.ensure_hashes()
        self.adapter.validate(envelope)

        # 2) authorize project/resource
        self._authorize_policy(envelope, context)
        self._require_fence_fields(envelope)

        # 3) evaluate policy/risk
        self._require_durable_store(envelope)
        self._evaluate_policy(envelope)

        # lease / cancel fences
        self._check_generations(envelope)

        # Read-only replay/unknown short-circuit BEFORE approval validation, so a
        # succeeded effect replays even after its approval expired (R27c).
        existing = self.store.get(project_id=envelope.project_id, effect_key=envelope.effect_key)
        if existing is not None:
            check_effect_binding(existing, envelope)
            if existing["state"] == "executing":
                if existing.get("timeout_seconds") is None:
                    raise ReconciliationRequiredError("effect_recovery_timeout_unavailable")
                recovered = self.store.recover_orphaned(
                    project_id=envelope.project_id,
                    effect_key=envelope.effect_key,
                    grace_seconds=self.orphan_grace_seconds,
                    timeout_seconds=envelope.timeout_seconds,
                )
                if not recovered:
                    raise EffectConflictError("effect_already_executing")
                existing = self.store.get(
                    project_id=envelope.project_id, effect_key=envelope.effect_key
                )
                if existing is None:
                    raise EffectConflictError("effect_not_found")
            if existing.get("state_reason") == "irreversible_requires_operator_disposition":
                raise ReconciliationRequiredError("irreversible_requires_operator_disposition")
            if existing["state"] == "succeeded":
                return self._terminal_or_fail(envelope)
            if existing["state"] == "unknown":
                return await self._reconcile_unknown(envelope, existing, context=context)

        # 4) exact approval is validated before any durable row exists; a denied
        # request leaves nothing behind.
        self._require_exact_approval(envelope, existing)

        # 5) reserve, then the committed admission point (fences + approval
        # consumption + single-winner CAS in one transaction).
        self.store.reserve(envelope)
        try:
            effect = self.store.begin_execution(
                envelope,
                executor_id=new_id("exe_"),
                fence_reader=self.fences.reader(**self._fence_identity(envelope)),
            )
        except LeaseClaimError as exc:
            raise EffectConflictError(f"fence_changed_before_execute:{exc}") from exc
        except EffectConflictError as exc:
            if "unknown" in str(exc):
                raise ReconciliationRequiredError(str(exc)) from exc
            if "succeeded" in str(exc):
                return self._terminal_or_fail(envelope)
            raise
        except EffectStoreError as exc:
            if str(exc) == "approval_not_consumable":
                raise ApprovalInvalidError("approval_expired_or_revoked_or_exhausted") from exc
            raise

        # 6-7) adapter calls leave the event loop responsive and have deadlines.
        pre: dict[str, Any] = {}
        started = utc_now()

        def finish(
            state: str,
            reason: str | None,
            post: dict[str, Any],
            external_id: str | None = None,
        ) -> ActionReceiptV17:
            uncertain = state == "unknown"
            return self._finalize(
                envelope,
                effect,
                state=state,
                outcome=state,
                state_reason=reason,
                pre=pre,
                post=post,
                started=started,
                external_id=external_id,
                reconciliation={"status": "pending"} if uncertain else None,
                reconciliation_state="pending" if uncertain else "none",
                artifacts=self._authorized_artifacts(envelope, post)
                if state == "succeeded"
                else None,
            )

        try:
            pre = await asyncio.wait_for(
                asyncio.to_thread(self.adapter.observe_pre_state, envelope),
                timeout=envelope.timeout_seconds,
            )
            if not isinstance(pre, dict):
                pre = {}
                raise TypeError("invalid_pre_observation")
        except asyncio.CancelledError as cancelled:
            try:
                finish("unknown", "cancelled_during_execute", {})
            finally:
                raise cancelled
        except TimeoutError:
            return finish("unknown", "timeout", {})
        except Exception as exc:  # noqa: BLE001
            return finish("unknown", f"exception:{type(exc).__name__}", {})

        effect = self.store.attach_pre_observation(
            project_id=envelope.project_id,
            effect_key=envelope.effect_key,
            pre_observation=pre,
            expected_execution=(effect.get("executor_id"), effect["attempt_count"], "executing"),
        )
        try:
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(self.adapter.execute, envelope),
                    timeout=envelope.timeout_seconds,
                )
            except AdapterNotSentError:
                return finish("failed", "not_applied", {})
            except AdapterDeniedError as exc:
                return finish("denied", str(exc), {})
            except TimeoutError:
                return finish("unknown", "timeout", {})
            except Exception as exc:  # noqa: BLE001
                return finish("unknown", f"exception:{type(exc).__name__}", {})

            value = result.get("outcome") if isinstance(result, dict) else None
            outcome = value if isinstance(value, str) and value in ADAPTER_OUTCOMES else "unknown"
            reason = None
            state = outcome
            if outcome == "unknown":
                reason = "unrecognized_outcome"
            elif outcome == "not_applied":
                state, reason = "failed", "not_applied"
            elif outcome == "denied":
                reason = str(result.get("detail") or result.get("reason") or "adapter_denied")

            if isinstance(result, dict):
                try:
                    post = await asyncio.wait_for(
                        asyncio.to_thread(self.adapter.observe_post_state, envelope, result),
                        timeout=envelope.timeout_seconds,
                    )
                    if not isinstance(post, dict):
                        raise TypeError("invalid_post_observation")
                except Exception as exc:  # noqa: BLE001
                    post = {"post_observation_error": type(exc).__name__}
            else:
                post = {"unrecognized_result_type": type(result).__name__}
            external_id = result.get("external_id") if isinstance(result, dict) else None
            if not isinstance(external_id, str):
                external_id = None
            return finish(state, reason, post, external_id)
        except asyncio.CancelledError as cancelled:
            try:
                finish("unknown", "cancelled_during_execute", {})
            finally:
                raise cancelled

    def _terminal_or_fail(self, envelope: ActionEnvelope) -> ActionReceiptV17:
        """R27a: a replay returns the original immutable receipt, never a re-mint."""
        terminal = self.store.terminal_receipt(
            project_id=envelope.project_id, effect_key=envelope.effect_key
        )
        if terminal is None:
            raise ReconciliationRequiredError("succeeded_effect_missing_receipt")
        return terminal

    def _finalize(
        self,
        envelope: ActionEnvelope,
        effect: dict[str, Any],
        *,
        state: str,
        outcome: str,
        pre: dict[str, Any],
        post: dict[str, Any],
        started: Any = None,
        external_id: str | None = None,
        reconciliation: dict[str, Any] | None = None,
        reconciliation_state: str = "none",
        artifacts: list[str] | None = None,
        state_reason: str | None = None,
    ) -> ActionReceiptV17:
        receipt = self._build_receipt(
            envelope,
            effect_id=effect["effect_id"],
            outcome=outcome,
            pre=pre,
            post=post,
            started=started,
            reconciliation_state=reconciliation_state,
            external_id=external_id,
            artifacts=artifacts,
        )
        return self.store.finalize_with_receipt(
            project_id=envelope.project_id,
            effect_key=envelope.effect_key,
            state=state,
            state_reason=state_reason,
            post_observation=post,
            external_id=external_id,
            reconciliation=reconciliation,
            receipt=receipt,
            expected_execution=(
                effect.get("executor_id"),
                effect["attempt_count"],
                effect["state"],
            ),
        )

    async def reconcile(
        self, envelope: ActionEnvelope, *, context: ActorContext
    ) -> ActionReceiptV17:
        self._authorize_context(envelope, context)
        envelope = self._effective_envelope(envelope)
        envelope.ensure_hashes()
        self.adapter.validate(envelope)
        self._authorize_policy(envelope, context)
        self._require_fence_fields(envelope)
        self._require_durable_store(envelope)
        self._evaluate_policy(envelope)
        self._check_generations(envelope)
        effect = self.store.get(project_id=envelope.project_id, effect_key=envelope.effect_key)
        if effect is None:
            raise EffectConflictError("effect_not_found")
        check_effect_binding(effect, envelope)
        if effect["state"] != "unknown":
            raise EffectConflictError("effect_not_unknown")
        return await self._reconcile_unknown(envelope, effect, context=context)

    async def _reconcile_unknown(
        self, envelope: ActionEnvelope, effect: dict[str, Any], *, context: ActorContext
    ) -> ActionReceiptV17:
        prior = self.store.list_receipts(
            project_id=envelope.project_id, effect_key=envelope.effect_key
        )
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(self.adapter.reconcile, envelope, prior),
                timeout=envelope.timeout_seconds,
            )
        except asyncio.CancelledError as cancelled:
            try:
                self._finalize(
                    envelope,
                    effect,
                    state="unknown",
                    outcome="unknown",
                    state_reason="cancelled_during_execute",
                    pre=effect.get("pre_observation") or {},
                    post={},
                    reconciliation={"status": "pending"},
                    reconciliation_state="pending",
                )
            finally:
                raise cancelled
        except TimeoutError:
            result = {"state": "unknown", "reason": "timeout"}
        except Exception as exc:  # noqa: BLE001
            result = {"state": "unknown", "reason": f"exception:{type(exc).__name__}"}
        if not isinstance(result, dict):
            result = {"state": "unknown", "invalid_result_type": type(result).__name__}
        state = str(result.get("state", "unknown"))
        if state == "succeeded":
            return self._finalize(
                envelope,
                effect,
                state="succeeded",
                outcome="succeeded",
                pre=effect.get("pre_observation") or {},
                post=result,
                started=effect.get("started_at"),
                external_id=result.get("external_id"),
                reconciliation={"status": "reconciled", "result": result},
                reconciliation_state="reconciled",
            )
        if state == "not_applied":
            irreversible = effect.get("side_effect_class") != "consequential"
            reason = "irreversible_requires_operator_disposition" if irreversible else "not_applied"
            self._finalize(
                envelope,
                effect,
                state="failed",
                outcome="failed",
                state_reason=reason,
                pre=effect.get("pre_observation") or {},
                post=result,
                started=effect.get("started_at"),
                reconciliation={"status": "reconciled", "result": result},
                reconciliation_state="reconciled",
            )
            if irreversible:
                raise ReconciliationRequiredError("irreversible_requires_operator_disposition")
            return await self.execute_envelope(envelope, context=context)
        self._finalize(
            envelope,
            effect,
            state="unknown",
            outcome="unknown",
            state_reason=result.get("reason", effect.get("state_reason")),
            pre=effect.get("pre_observation") or {},
            post=result,
            started=effect.get("started_at"),
            reconciliation={"status": "pending", "result": result},
            reconciliation_state="pending",
        )
        raise ReconciliationRequiredError("external_outcome_still_unknown")

    def _effective_envelope(self, envelope: ActionEnvelope) -> ActionEnvelope:
        declaration = self.adapter.manifest.operations.get(envelope.operation)
        if declaration is None:
            raise ToolAuthorizationError("operation_not_declared")
        effect_rank = {"none": 0, "idempotent": 1, "consequential": 2, "irreversible": 3}
        return envelope.model_copy(
            update={
                "side_effect_class": max(
                    envelope.side_effect_class,
                    declaration.side_effect_class,
                    key=effect_rank.__getitem__,
                ),
                "risk_class": max(
                    envelope.risk_class, declaration.risk_class, key=self._risk_rank.__getitem__
                ),
            }
        )

    @staticmethod
    def _require_fence_fields(envelope: ActionEnvelope) -> None:
        if envelope.side_effect_class in {"consequential", "irreversible"} and (
            any(
                not value or not value.strip()
                for value in (envelope.mission_id, envelope.task_id, envelope.attempt_id)
            )
            or envelope.lease_generation is None
            or envelope.cancellation_generation is None
        ):
            raise StaleLeaseError("fence_missing")

    @staticmethod
    def _authorize_context(envelope: ActionEnvelope, context: ActorContext) -> None:
        if envelope.project_id != context.project_id:
            raise ToolAuthorizationError("wrong_project")
        if envelope.actor != context.actor:
            raise ToolAuthorizationError("actor_mismatch")

    def _authorize_policy(self, envelope: ActionEnvelope, context: ActorContext) -> None:
        if envelope.policy_version != self.policy.current_policy_version(
            project_id=context.project_id
        ):
            raise PolicyDeniedError("policy_version_stale")
        scopes = self.policy.effective_scopes(
            project_id=context.project_id,
            actor=context.actor,
            integration_id=envelope.integration_id,
            integration_version=envelope.integration_version,
        )
        required = set(self.adapter.manifest.operations[envelope.operation].scopes)
        required.update(envelope.requested_scopes)
        missing = required - scopes
        if missing:
            raise ToolAuthorizationError(f"denied_scopes:{sorted(missing)}")

    def _evaluate_policy(self, envelope: ActionEnvelope) -> None:
        if envelope.side_effect_class in {"consequential", "irreversible"}:
            if self._risk_rank.get(envelope.risk_class, 99) > self._risk_rank.get(
                self.max_risk_without_approval, 0
            ):
                if not envelope.approval_id:
                    raise PolicyDeniedError("approval_required")

    def _require_exact_approval(
        self, envelope: ActionEnvelope, existing: dict[str, Any] | None = None
    ) -> None:
        needs = envelope.side_effect_class in {"consequential", "irreversible"} or (
            self._risk_rank.get(envelope.risk_class, 0)
            > self._risk_rank.get(self.max_risk_without_approval, 0)
        )
        if not needs:
            return
        if not envelope.approval_id:
            raise ApprovalInvalidError("approval_required")
        grant = self.store.get_approval(envelope.approval_id, project_id=envelope.project_id)
        if grant is None:
            # Unknown, other-project, or legacy non-operational row: no existence signal.
            raise ApprovalInvalidError("unknown_approval")
        # Revocation and expiry always deny. Usage is consumed exactly once per effect
        # at admission (begin_execution); a re-attempt of the same effect that already
        # consumed this grant is not a second use. The durable UPDATE remains the
        # authority; this is the read-only pre-check.
        consumed_by_this_effect = existing is not None and (
            grant.approval_id in existing.get("consumed_approval_ids", [])
            or (
                existing.get("approval_consumed_at") is not None
                and existing.get("approval_id") == grant.approval_id
            )
        )
        if not grant.is_active(ignore_usage=consumed_by_this_effect):
            raise ApprovalInvalidError("approval_expired_or_revoked_or_exhausted")
        if grant.integration_id != envelope.integration_id:
            raise ApprovalInvalidError("approval_integration_mismatch")
        if grant.integration_version != envelope.integration_version:
            raise ApprovalInvalidError("approval_version_mismatch")
        if grant.operation != envelope.operation:
            raise ApprovalInvalidError("approval_operation_mismatch")
        if grant.destination != envelope.destination:
            raise ApprovalInvalidError("approval_destination_mismatch")
        if grant.payload_hash != envelope.payload_hash:
            raise ApprovalInvalidError("approval_payload_mismatch")
        if grant.effect_key and grant.effect_key != envelope.effect_key:
            raise ApprovalInvalidError("approval_effect_key_mismatch")
        if grant.policy_version != envelope.policy_version:
            raise ApprovalInvalidError("approval_policy_version_mismatch")

    def _check_generations(self, envelope: ActionEnvelope) -> None:
        current = self.fences.current(**self._fence_identity(envelope))
        if envelope.lease_generation != current.lease_generation:
            raise StaleLeaseError("stale_lease_generation")
        if envelope.cancellation_generation != current.cancellation_generation:
            raise CancellationFenceError("cancellation_generation_mismatch")

    @staticmethod
    def _fence_identity(envelope: ActionEnvelope) -> dict[str, Any]:
        return {
            "project_id": envelope.project_id,
            "mission_id": envelope.mission_id,
            "task_id": envelope.task_id,
            "attempt_id": envelope.attempt_id,
        }

    def _require_durable_store(self, envelope: ActionEnvelope) -> None:
        if (
            envelope.side_effect_class in {"consequential", "irreversible"}
            and getattr(self.store, "durable", False) is not True
        ):
            raise PolicyDeniedError("durable_store_required")

    @staticmethod
    def _authorized_artifacts(envelope: ActionEnvelope, post: dict[str, Any]) -> list[str]:
        # Only non-secret artifact refs.
        arts: list[str] = []
        result = post.get("result") if isinstance(post.get("result"), dict) else post
        if isinstance(result, dict):
            if result.get("path"):
                arts.append(f"file:{result['path']}")
            if result.get("external_id"):
                arts.append(f"ext:{result['external_id']}")
            if result.get("navigated_to"):
                arts.append(f"url:{result['navigated_to']}")
        return arts

    def _build_receipt(
        self,
        envelope: ActionEnvelope,
        *,
        effect_id: str,
        outcome: str,
        pre: dict[str, Any],
        post: dict[str, Any],
        started: Any = None,
        reconciliation_state: str = "none",
        external_id: str | None = None,
        artifacts: list[str] | None = None,
    ) -> ActionReceiptV17:
        finished = utc_now()
        digest = payload_hash({"pre": pre, "post": post, "outcome": outcome})
        return ActionReceiptV17(
            action_id=envelope.action_id,
            effect_key=envelope.effect_key,
            effect_id=effect_id,
            approval_id=envelope.approval_id,
            project_id=envelope.project_id,
            integration_id=envelope.integration_id,
            integration_version=envelope.integration_version,
            operation=envelope.operation,
            destination=envelope.destination,
            pre_observation=pre,
            post_observation=post,
            started_at=started,
            finished_at=finished,
            external_id=external_id,
            outcome=outcome,  # type: ignore[arg-type]
            effective_side_effect_class=envelope.side_effect_class,
            effective_risk_class=envelope.risk_class,
            reconciliation_state=reconciliation_state,
            attempt_refs=[new_id("aat_")],
            evidence_digest=digest,
            authorized_artifacts=list(artifacts or []),
        )

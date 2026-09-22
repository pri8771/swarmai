"""V2B-004b / ART-V17 — consequential ToolGateway pipeline.

Order: normalize → authorize → policy/risk → exact approval → reserve effect →
execute adapter → pre/post evidence → reconcile → expose authorized artifacts only.

Unknown external outcome enters reconciliation; never blind-retry.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from swarm.contracts.actions import (
    ActionEnvelope,
    ActionReceiptV17,
    ApprovalGrant,
)
from swarm.contracts.common import new_id, payload_hash, utc_now
from swarm.db.lease_fencing import LeaseRenewError, effect_fence_reader
from swarm.tools.adapters.base import IntegrationAdapter
from swarm.tools.effects import (
    DurableEffectRepository,
    EffectConflictError,
    EffectStoreError,
    InMemoryEffectStore,
    check_effect_binding,
)


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
        adapter: IntegrationAdapter,
        *,
        project_id: str,
        allowed_scopes: set[str],
        current_lease_generation: int,
        current_cancellation_generation: int = 0,
        store: InMemoryEffectStore | DurableEffectRepository | None = None,
        max_risk_without_approval: str = "low",
        orphan_grace_seconds: int = 30,
    ) -> None:
        if orphan_grace_seconds < 0:
            raise ValueError("invalid_recovery_window")
        self.orphan_grace_seconds = orphan_grace_seconds
        self.adapter = adapter
        self.project_id = project_id
        self.allowed_scopes = allowed_scopes
        self.current_lease_generation = current_lease_generation
        self.current_cancellation_generation = current_cancellation_generation
        self.store = store or InMemoryEffectStore()
        self.max_risk_without_approval = max_risk_without_approval
        self._risk_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}

    def put_approval(self, grant: ApprovalGrant) -> ApprovalGrant:
        if grant.project_id != self.project_id:
            raise ApprovalInvalidError("approval_project_mismatch")
        return self.store.put_approval(grant)

    def revoke_approval(self, approval_id: str, *, revoked_by: str, reason: str) -> bool:
        return self.store.revoke_approval(
            project_id=self.project_id,
            approval_id=approval_id,
            revoked_by=revoked_by,
            reason=reason,
        )

    def make_approval(
        self,
        envelope: ActionEnvelope,
        *,
        grantor: str = "operator",
        expires_in_seconds: int = 300,
        max_effect_count: int = 1,
    ) -> ApprovalGrant:
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
        return self.put_approval(grant)

    async def execute_request(self, request: dict[str, Any]) -> ActionReceiptV17:
        # 1) normalize
        envelope = self.adapter.normalize(request)
        return await self.execute_envelope(envelope)

    async def execute_envelope(self, envelope: ActionEnvelope) -> ActionReceiptV17:
        envelope.ensure_hashes()
        self.adapter.validate(envelope)

        # 2) authorize project/resource
        self._authorize_project(envelope)

        # 3) evaluate policy/risk
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
                return await self._reconcile_unknown(envelope, existing)

        # 4) exact approval is validated before any durable row exists; a denied
        # request leaves nothing behind.
        self._require_exact_approval(envelope, existing)

        # 5) reserve, then the committed admission point (fences + approval
        # consumption + single-winner CAS in one transaction).
        self.store.reserve(envelope)
        try:
            # Standalone actions have no mission lease. Any linked action must
            # re-read its complete durable authority inside committed admission.
            reader = None
            if isinstance(self.store, DurableEffectRepository) and any(
                (envelope.mission_id, envelope.task_id, envelope.attempt_id)
            ):
                reader = effect_fence_reader(envelope)
            effect = self.store.begin_execution(
                envelope, executor_id=new_id("exe_"), fence_reader=reader
            )
        except LeaseRenewError as exc:
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

        # 6-7) pre observe, execute, post observe
        pre = self.adapter.observe_pre_state(envelope)
        effect = self.store.attach_pre_observation(
            project_id=envelope.project_id,
            effect_key=envelope.effect_key,
            pre_observation=pre,
            expected_execution=(effect.get("executor_id"), effect["attempt_count"], "executing"),
        )
        started = utc_now()
        try:
            result = self.adapter.execute(envelope)
        except Exception as exc:  # noqa: BLE001
            post = {"error": str(exc)}
            return self._finalize(
                envelope,
                effect,
                state="failed",
                outcome="failed",
                pre=pre,
                post=post,
                started=started,
            )

        post = self.adapter.observe_post_state(envelope, result)
        outcome = self._outcome_from_result(result)

        if outcome == "unknown":
            # 8) reconcile path — do not mark succeeded; never blind retry later.
            return self._finalize(
                envelope,
                effect,
                state="unknown",
                outcome="unknown",
                pre=pre,
                post=post,
                started=started,
                external_id=result.get("external_id"),
                reconciliation={"status": "pending", "steps": ["poll_external", "confirm"]},
                reconciliation_state="pending",
            )
        if outcome in {"denied", "cancelled"}:
            return self._finalize(
                envelope,
                effect,
                state=outcome,
                outcome=outcome,
                pre=pre,
                post=post,
                started=started,
            )
        # succeeded — approval use was consumed at admission (begin_execution), never here.
        return self._finalize(
            envelope,
            effect,
            state="succeeded",
            outcome="succeeded",
            pre=pre,
            post=post,
            started=started,
            external_id=result.get("external_id"),
            artifacts=self._authorized_artifacts(envelope, post),
        )

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

    async def reconcile(self, envelope: ActionEnvelope) -> ActionReceiptV17:
        envelope.ensure_hashes()
        self.adapter.validate(envelope)
        self._authorize_project(envelope)
        self._evaluate_policy(envelope)
        self._check_generations(envelope)
        effect = self.store.get(project_id=envelope.project_id, effect_key=envelope.effect_key)
        if effect is None:
            raise EffectConflictError("effect_not_found")
        check_effect_binding(effect, envelope)
        if effect["state"] != "unknown":
            raise EffectConflictError("effect_not_unknown")
        return await self._reconcile_unknown(envelope, effect)

    async def _reconcile_unknown(
        self, envelope: ActionEnvelope, effect: dict[str, Any]
    ) -> ActionReceiptV17:
        prior = self.store.list_receipts(
            project_id=envelope.project_id, effect_key=envelope.effect_key
        )
        try:
            result = self.adapter.reconcile(envelope, prior)
        except Exception as exc:  # noqa: BLE001
            result = {"state": "unknown", "error_type": type(exc).__name__}
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
            return await self.execute_envelope(envelope)
        self._finalize(
            envelope,
            effect,
            state="unknown",
            outcome="unknown",
            state_reason=effect.get("state_reason"),
            pre=effect.get("pre_observation") or {},
            post=result,
            started=effect.get("started_at"),
            reconciliation={"status": "pending", "result": result},
            reconciliation_state="pending",
        )
        raise ReconciliationRequiredError("external_outcome_still_unknown")

    def _authorize_project(self, envelope: ActionEnvelope) -> None:
        if envelope.project_id != self.project_id:
            raise ToolAuthorizationError("wrong_project")
        missing = set(envelope.requested_scopes) - self.allowed_scopes
        if missing:
            raise ToolAuthorizationError(f"denied_scopes:{sorted(missing)}")
        man = self.adapter.manifest
        if not set(man.scopes).issubset(self.allowed_scopes | set(envelope.requested_scopes)):
            # Allow if all manifest scopes are in the gateway allow-list.
            if not set(man.scopes).issubset(self.allowed_scopes):
                raise ToolAuthorizationError("adapter_scope_denied")

    def _evaluate_policy(self, envelope: ActionEnvelope) -> None:
        if envelope.side_effect_class in {"consequential", "irreversible"}:
            if self._risk_rank.get(envelope.risk_class, 99) > self._risk_rank.get(
                self.max_risk_without_approval, 0
            ):
                if not envelope.approval_id:
                    raise PolicyDeniedError("consequential_requires_approval")

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
        if envelope.lease_generation != self.current_lease_generation:
            raise StaleLeaseError("stale_lease_generation")
        if envelope.cancellation_generation != self.current_cancellation_generation:
            raise CancellationFenceError("cancellation_generation_mismatch")

    @staticmethod
    def _outcome_from_result(result: dict[str, Any]) -> str:
        if "outcome" in result:
            return str(result["outcome"])
        if result.get("written") or result.get("submitted") or result.get("navigated_to"):
            return "succeeded"
        return "succeeded"

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
            reconciliation_state=reconciliation_state,
            attempt_refs=[new_id("aat_")],
            evidence_digest=digest,
            authorized_artifacts=list(artifacts or []),
        )

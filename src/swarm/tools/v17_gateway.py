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
from swarm.tools.adapters.base import IntegrationAdapter
from swarm.tools.effects import (
    DurableEffectRepository,
    EffectConflictError,
    InMemoryEffectStore,
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
    ) -> None:
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

    def make_approval(
        self,
        envelope: ActionEnvelope,
        *,
        grantor: str = "operator",
        expires_in_seconds: int = 300,
        max_effect_count: int = 1,
        revoked: bool = False,
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
            revoked_at=now if revoked else None,
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

        # Reserve early so succeeded effects short-circuit without re-consuming approval.
        effect = self.store.reserve(envelope)
        if effect["state"] == "succeeded":
            prior = self.store.get_receipt(envelope.action_id)
            if prior is not None:
                return prior
            return self._receipt_from_effect(envelope, effect, outcome="succeeded")
        if effect["state"] == "unknown":
            return await self._reconcile_unknown(envelope, effect)

        # 4) require exact approval if needed (only for new execution)
        self._require_exact_approval(envelope)

        try:
            self.store.mark_executing(
                project_id=envelope.project_id, effect_key=envelope.effect_key
            )
        except EffectConflictError as exc:
            if "unknown" in str(exc):
                raise ReconciliationRequiredError(str(exc)) from exc
            if "succeeded" in str(exc):
                row = self.store.get(project_id=envelope.project_id, effect_key=envelope.effect_key)
                assert row is not None
                return self._receipt_from_effect(envelope, row, outcome="succeeded")
            raise

        # 6-7) pre observe, execute, post observe
        pre = self.adapter.observe_pre_state(envelope)
        effect = self.store.attach_pre_observation(
            project_id=envelope.project_id,
            effect_key=envelope.effect_key,
            pre_observation=pre,
        )
        started = utc_now()
        try:
            result = self.adapter.execute(envelope)
        except Exception as exc:  # noqa: BLE001
            post = {"error": str(exc)}
            self.store.finalize(
                project_id=envelope.project_id,
                effect_key=envelope.effect_key,
                state="failed",
                post_observation=post,
            )
            receipt = self._build_receipt(
                envelope,
                effect_id=effect["effect_id"],
                outcome="failed",
                pre=pre,
                post=post,
                started=started,
            )
            return self.store.store_receipt(receipt)

        post = self.adapter.observe_post_state(envelope, result)
        outcome = self._outcome_from_result(result)

        if outcome == "unknown":
            # 8) reconcile path — do not mark succeeded; never blind retry later.
            self.store.finalize(
                project_id=envelope.project_id,
                effect_key=envelope.effect_key,
                state="unknown",
                post_observation=post,
                external_id=result.get("external_id"),
                reconciliation={"status": "pending", "steps": ["poll_external", "confirm"]},
            )
            receipt = self._build_receipt(
                envelope,
                effect_id=effect["effect_id"],
                outcome="unknown",
                pre=pre,
                post=post,
                started=started,
                reconciliation_state="pending",
                external_id=result.get("external_id"),
            )
            return self.store.store_receipt(receipt)

        if outcome == "denied":
            self.store.finalize(
                project_id=envelope.project_id,
                effect_key=envelope.effect_key,
                state="denied",
                post_observation=post,
            )
            receipt = self._build_receipt(
                envelope,
                effect_id=effect["effect_id"],
                outcome="denied",
                pre=pre,
                post=post,
                started=started,
            )
            return self.store.store_receipt(receipt)

        if outcome == "cancelled":
            self.store.finalize(
                project_id=envelope.project_id,
                effect_key=envelope.effect_key,
                state="cancelled",
                post_observation=post,
            )
            receipt = self._build_receipt(
                envelope,
                effect_id=effect["effect_id"],
                outcome="cancelled",
                pre=pre,
                post=post,
                started=started,
            )
            return self.store.store_receipt(receipt)

        # succeeded
        self.store.finalize(
            project_id=envelope.project_id,
            effect_key=envelope.effect_key,
            state="succeeded",
            post_observation=post,
            external_id=result.get("external_id"),
        )
        if envelope.approval_id:
            self.store.record_approval_use(envelope.approval_id)
        # 9) expose only authorized artifacts
        artifacts = self._authorized_artifacts(envelope, post)
        receipt = self._build_receipt(
            envelope,
            effect_id=effect["effect_id"],
            outcome="succeeded",
            pre=pre,
            post=post,
            started=started,
            external_id=result.get("external_id"),
            artifacts=artifacts,
        )
        return self.store.store_receipt(receipt)

    async def reconcile(self, envelope: ActionEnvelope) -> ActionReceiptV17:
        envelope.ensure_hashes()
        effect = self.store.get(project_id=envelope.project_id, effect_key=envelope.effect_key)
        if effect is None:
            raise EffectConflictError("effect_not_found")
        return await self._reconcile_unknown(envelope, effect)

    async def _reconcile_unknown(
        self, envelope: ActionEnvelope, effect: dict[str, Any]
    ) -> ActionReceiptV17:
        prior = [
            r
            for r in self.store.receipts.values()
            if r.effect_key == envelope.effect_key and r.project_id == envelope.project_id
        ]
        result = self.adapter.reconcile(envelope, prior)
        state = str(result.get("state", "unknown"))
        if state == "succeeded":
            self.store.finalize(
                project_id=envelope.project_id,
                effect_key=envelope.effect_key,
                state="succeeded",
                post_observation=result,
                external_id=result.get("external_id"),
                reconciliation={"status": "reconciled", "result": result},
            )
            receipt = self._build_receipt(
                envelope,
                effect_id=effect["effect_id"],
                outcome="succeeded",
                pre=effect.get("pre_observation") or {},
                post=result,
                started=effect.get("started_at"),
                reconciliation_state="reconciled",
                external_id=result.get("external_id"),
            )
            return self.store.store_receipt(receipt)
        if state == "failed":
            self.store.finalize(
                project_id=envelope.project_id,
                effect_key=envelope.effect_key,
                state="failed",
                post_observation=result,
                reconciliation={"status": "reconciled", "result": result},
            )
            receipt = self._build_receipt(
                envelope,
                effect_id=effect["effect_id"],
                outcome="failed",
                pre=effect.get("pre_observation") or {},
                post=result,
                reconciliation_state="reconciled",
            )
            return self.store.store_receipt(receipt)
        # Still unknown — do not execute again.
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

    def _require_exact_approval(self, envelope: ActionEnvelope) -> None:
        needs = envelope.side_effect_class in {"consequential", "irreversible"} or (
            self._risk_rank.get(envelope.risk_class, 0)
            > self._risk_rank.get(self.max_risk_without_approval, 0)
        )
        if not needs:
            return
        if not envelope.approval_id:
            raise ApprovalInvalidError("approval_required")
        grant = self.store.get_approval(envelope.approval_id)
        if grant is None:
            raise ApprovalInvalidError("unknown_approval")
        if grant.project_id != envelope.project_id:
            raise ApprovalInvalidError("approval_project_mismatch")
        if not grant.is_active():
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

    def _receipt_from_effect(
        self, envelope: ActionEnvelope, effect: dict[str, Any], *, outcome: str
    ) -> ActionReceiptV17:
        return self._build_receipt(
            envelope,
            effect_id=effect["effect_id"],
            outcome=outcome,
            pre=effect.get("pre_observation") or {},
            post=effect.get("post_observation") or {},
            started=effect.get("started_at"),
            external_id=effect.get("external_id"),
            artifacts=self._authorized_artifacts(envelope, effect.get("post_observation") or {}),
        )

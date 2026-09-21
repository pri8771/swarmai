"""V2B-004a / ART-V17 — durable action effect reservation store."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from swarm.contracts.actions import ActionEnvelope, ActionReceiptV17, ApprovalGrant
from swarm.contracts.common import new_id, payload_hash, utc_now
from swarm.db.models import ActionEffectRow, ApprovalRow


class EffectStoreError(ValueError):
    pass


class EffectConflictError(EffectStoreError):
    pass


def _effect_dict_from_row(row: ActionEffectRow) -> dict[str, Any]:
    return {
        "effect_id": row.effect_id,
        "effect_key": row.effect_key,
        "project_id": row.project_id,
        "action_id": row.action_id,
        "approval_id": row.approval_id,
        "integration_id": row.integration_id,
        "integration_version": row.integration_version,
        "operation": row.operation,
        "destination_digest": row.destination_digest,
        "payload_hash": row.payload_hash,
        "state": row.state,
        "lease_generation": row.lease_generation,
        "cancellation_generation": row.cancellation_generation,
        "pre_observation": dict(row.pre_observation or {}),
        "post_observation": dict(row.post_observation or {}),
        "reconciliation": dict(row.reconciliation or {}),
        "created_at": row.created_at,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
        "reconciled_at": row.reconciled_at,
        "external_id": row.external_id,
    }


class InMemoryEffectStore:
    """Process-local effect store used by tests and single-host loops."""

    def __init__(self) -> None:
        self.effects: dict[tuple[str, str], dict[str, Any]] = {}
        self.receipts: dict[str, ActionReceiptV17] = {}
        self.approvals: dict[str, ApprovalGrant] = {}

    def put_approval(self, grant: ApprovalGrant) -> ApprovalGrant:
        self.approvals[grant.approval_id] = grant
        return grant

    def get_approval(self, approval_id: str) -> ApprovalGrant | None:
        return self.approvals.get(approval_id)

    def record_approval_use(self, approval_id: str) -> None:
        grant = self.approvals.get(approval_id)
        if grant is not None:
            grant.used_count += 1

    def reserve(self, envelope: ActionEnvelope) -> dict[str, Any]:
        envelope.ensure_hashes()
        key = (envelope.project_id, envelope.effect_key)
        existing = self.effects.get(key)
        if existing is not None:
            return existing
        row: dict[str, Any] = {
            "effect_id": new_id("aef_"),
            "effect_key": envelope.effect_key,
            "project_id": envelope.project_id,
            "action_id": envelope.action_id,
            "approval_id": envelope.approval_id,
            "integration_id": envelope.integration_id,
            "integration_version": envelope.integration_version,
            "operation": envelope.operation,
            "destination_digest": payload_hash({"destination": envelope.destination}),
            "payload_hash": envelope.payload_hash,
            "state": "reserved",
            "lease_generation": envelope.lease_generation,
            "cancellation_generation": envelope.cancellation_generation,
            "pre_observation": {},
            "post_observation": {},
            "reconciliation": {},
            "created_at": utc_now(),
            "external_id": None,
        }
        self.effects[key] = row
        return row

    def mark_executing(self, *, project_id: str, effect_key: str) -> dict[str, Any]:
        row = self._require(project_id, effect_key)
        if row["state"] == "succeeded":
            raise EffectConflictError("effect_already_succeeded")
        if row["state"] == "unknown":
            raise EffectConflictError("effect_unknown_requires_reconcile")
        if row["state"] == "executing":
            raise EffectConflictError("effect_already_executing")
        if row["state"] in {"denied", "cancelled"}:
            raise EffectConflictError(f"effect_terminal:{row['state']}")
        row["state"] = "executing"
        row["started_at"] = utc_now()
        return row

    def attach_pre_observation(
        self, *, project_id: str, effect_key: str, pre_observation: dict[str, Any]
    ) -> dict[str, Any]:
        row = self._require(project_id, effect_key)
        row["pre_observation"] = dict(pre_observation)
        return row

    def finalize(
        self,
        *,
        project_id: str,
        effect_key: str,
        state: str,
        post_observation: dict[str, Any] | None = None,
        external_id: str | None = None,
        reconciliation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        row = self._require(project_id, effect_key)
        row["state"] = state
        row["finished_at"] = utc_now()
        if post_observation is not None:
            row["post_observation"] = dict(post_observation)
        if external_id is not None:
            row["external_id"] = external_id
        if reconciliation is not None:
            row["reconciliation"] = dict(reconciliation)
            row["reconciled_at"] = utc_now()
        return row

    def get(self, *, project_id: str, effect_key: str) -> dict[str, Any] | None:
        return self.effects.get((project_id, effect_key))

    def store_receipt(self, receipt: ActionReceiptV17) -> ActionReceiptV17:
        self.receipts[receipt.action_id] = receipt
        return receipt

    def get_receipt(self, action_id: str) -> ActionReceiptV17 | None:
        return self.receipts.get(action_id)

    def _require(self, project_id: str, effect_key: str) -> dict[str, Any]:
        row = self.effects.get((project_id, effect_key))
        if row is None:
            raise EffectStoreError("effect_not_found")
        return row


class DurableEffectRepository:
    """SQLAlchemy-backed effect/approval persistence (ART-V17-DURABLE-EFFECT-SCHEMA).

    Returns the same dict shape as InMemoryEffectStore so ConsequentialToolGateway
    can use either backend.
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self.receipts: dict[str, ActionReceiptV17] = {}

    def put_approval(self, grant: ApprovalGrant) -> ApprovalGrant:
        row = ApprovalRow(
            id=grant.approval_id,
            payload_hash=grant.payload_hash,
            permitted_operation=f"{grant.integration_id}.{grant.operation}",
            destination=grant.destination,
            grantor=grant.grantor,
            expires_at=grant.expires_at,
            revoked_at=grant.revoked_at,
            payload=dict(grant.constraints),
            project_id=grant.project_id,
            actor=grant.actor,
            integration_id=grant.integration_id,
            integration_version=grant.integration_version,
            operation=grant.operation,
            effect_key=grant.effect_key,
            max_effect_count=grant.max_effect_count,
            used_count=grant.used_count,
            policy_version=grant.policy_version,
            created_at=grant.created_at,
            constraints=dict(grant.constraints),
        )
        self.session.merge(row)
        self.session.flush()
        return grant

    def get_approval(self, approval_id: str) -> ApprovalGrant | None:
        row = self.session.get(ApprovalRow, approval_id)
        if row is None or row.project_id is None:
            return None
        return ApprovalGrant(
            approval_id=row.id,
            project_id=row.project_id,
            actor=row.actor,
            grantor=row.grantor,
            integration_id=row.integration_id or "",
            integration_version=row.integration_version or "",
            operation=row.operation or row.permitted_operation,
            destination=row.destination,
            payload_hash=row.payload_hash,
            effect_key=row.effect_key,
            max_effect_count=int(row.max_effect_count or 1),
            used_count=int(row.used_count or 0),
            expires_at=row.expires_at,
            revoked_at=row.revoked_at,
            policy_version=row.policy_version or "v17-policy-1",
            constraints=dict(row.constraints or row.payload or {}),
            created_at=row.created_at or utc_now(),
        )

    def record_approval_use(self, approval_id: str) -> None:
        row = self.session.get(ApprovalRow, approval_id)
        if row is not None:
            row.used_count = int(row.used_count or 0) + 1
            self.session.flush()

    def reserve(self, envelope: ActionEnvelope) -> dict[str, Any]:
        envelope.ensure_hashes()
        existing = self.session.scalar(
            select(ActionEffectRow).where(
                ActionEffectRow.project_id == envelope.project_id,
                ActionEffectRow.effect_key == envelope.effect_key,
            )
        )
        if existing is not None:
            return _effect_dict_from_row(existing)
        row = ActionEffectRow(
            effect_id=new_id("aef_"),
            effect_key=envelope.effect_key,
            project_id=envelope.project_id,
            mission_id=envelope.mission_id,
            task_id=envelope.task_id,
            attempt_id=envelope.attempt_id,
            action_id=envelope.action_id,
            approval_id=envelope.approval_id,
            integration_id=envelope.integration_id,
            integration_version=envelope.integration_version,
            operation=envelope.operation,
            destination_digest=payload_hash({"destination": envelope.destination}),
            payload_hash=envelope.payload_hash,
            state="reserved",
            lease_generation=envelope.lease_generation,
            cancellation_generation=envelope.cancellation_generation,
        )
        self.session.add(row)
        self.session.flush()
        return _effect_dict_from_row(row)

    def mark_executing(self, *, project_id: str, effect_key: str) -> dict[str, Any]:
        row = self._require_row(project_id, effect_key)
        if row.state == "succeeded":
            raise EffectConflictError("effect_already_succeeded")
        if row.state == "unknown":
            raise EffectConflictError("effect_unknown_requires_reconcile")
        if row.state == "executing":
            raise EffectConflictError("effect_already_executing")
        if row.state in {"denied", "cancelled"}:
            raise EffectConflictError(f"effect_terminal:{row.state}")
        row.state = "executing"
        row.started_at = utc_now()
        self.session.flush()
        return _effect_dict_from_row(row)

    def attach_pre_observation(
        self, *, project_id: str, effect_key: str, pre_observation: dict[str, Any]
    ) -> dict[str, Any]:
        row = self._require_row(project_id, effect_key)
        row.pre_observation = dict(pre_observation)
        self.session.flush()
        return _effect_dict_from_row(row)

    def finalize(
        self,
        *,
        project_id: str,
        effect_key: str,
        state: str,
        post_observation: dict[str, Any] | None = None,
        external_id: str | None = None,
        reconciliation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        row = self._require_row(project_id, effect_key)
        row.state = state
        row.finished_at = utc_now()
        if post_observation is not None:
            row.post_observation = dict(post_observation)
        if external_id is not None:
            row.external_id = external_id
        if reconciliation is not None:
            row.reconciliation = dict(reconciliation)
            row.reconciled_at = utc_now()
        self.session.flush()
        return _effect_dict_from_row(row)

    def get(self, *, project_id: str, effect_key: str) -> dict[str, Any] | None:
        row = self.session.scalar(
            select(ActionEffectRow).where(
                ActionEffectRow.project_id == project_id,
                ActionEffectRow.effect_key == effect_key,
            )
        )
        if row is None:
            return None
        return _effect_dict_from_row(row)

    def store_receipt(self, receipt: ActionReceiptV17) -> ActionReceiptV17:
        self.receipts[receipt.action_id] = receipt
        return receipt

    def get_receipt(self, action_id: str) -> ActionReceiptV17 | None:
        return self.receipts.get(action_id)

    def _require_row(self, project_id: str, effect_key: str) -> ActionEffectRow:
        row = self.session.scalar(
            select(ActionEffectRow).where(
                ActionEffectRow.project_id == project_id,
                ActionEffectRow.effect_key == effect_key,
            )
        )
        if row is None:
            raise EffectStoreError("effect_not_found")
        return row

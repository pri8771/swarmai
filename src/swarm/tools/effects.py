"""V2B-004a / ART-V17 — durable action effect reservation store."""

from __future__ import annotations

import threading
from typing import Any

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from swarm.contracts.actions import ActionEnvelope, ActionReceiptV17, ApprovalGrant
from swarm.contracts.common import new_id, payload_hash, utc_now
from swarm.db.models import ActionEffectRow, ActionReceiptRow, ApprovalRow


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
        "state_reason": row.state_reason,
        "attempt_count": int(row.attempt_count or 0),
        "executor_id": row.executor_id,
        "approval_consumed_at": row.approval_consumed_at,
    }


# States from which a new execution attempt may be admitted (R27b). `failed` is
# re-executable only when the prior attempt provably did not apply.
def _executable(state: str, state_reason: str | None) -> bool:
    return state == "reserved" or (state == "failed" and state_reason == "not_applied")


def _not_executable(state: str, state_reason: str | None) -> EffectConflictError:
    if state == "succeeded":
        return EffectConflictError("effect_already_succeeded")
    if state == "unknown":
        return EffectConflictError("effect_unknown_requires_reconcile")
    if state == "executing":
        return EffectConflictError("effect_already_executing")
    return EffectConflictError(f"effect_terminal:{state}")


def _binding_of(envelope: ActionEnvelope) -> dict[str, str]:
    return {
        "integration_id": envelope.integration_id,
        "integration_version": envelope.integration_version,
        "operation": envelope.operation,
        "destination_digest": payload_hash({"destination": envelope.destination}),
        "payload_hash": envelope.payload_hash,
    }


def _check_binding(stored: dict[str, Any], envelope: ActionEnvelope) -> None:
    """An effect key identifies exactly one (integration, operation, destination, payload)."""
    for field, value in _binding_of(envelope).items():
        if str(stored.get(field)) != value:
            raise EffectConflictError("effect_key_binding_mismatch")


class InMemoryEffectStore:
    """Process-local effect store used by tests and single-host loops."""

    durable = False

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.effects: dict[tuple[str, str], dict[str, Any]] = {}
        # receipt_id -> (effect_id, attempt_number, receipt); insert-only (R27a).
        self.receipts: dict[str, tuple[str, int, ActionReceiptV17]] = {}
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
            _check_binding(existing, envelope)
            return {**existing, "created": False}
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
            "state_reason": None,
            "attempt_count": 0,
            "executor_id": None,
            "approval_consumed_at": None,
        }
        self.effects[key] = row
        return {**row, "created": True}

    def mark_executing(
        self, *, project_id: str, effect_key: str, executor_id: str
    ) -> dict[str, Any]:
        row = self._require(project_id, effect_key)
        with self._lock:
            if _executable(row["state"], row.get("state_reason")):
                row["state"] = "executing"
                row["state_reason"] = None
                row["started_at"] = utc_now()
                row["executor_id"] = executor_id
                row["attempt_count"] = int(row.get("attempt_count") or 0) + 1
                return dict(row)
        raise _not_executable(row["state"], row.get("state_reason"))

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
        """Insert-only. attempt_number = 1 + max(existing for this effect)."""
        row = self._require(receipt.project_id, receipt.effect_key)
        effect_id = str(row["effect_id"])
        if receipt.receipt_id in self.receipts:
            raise EffectConflictError("receipt_already_recorded")
        existing = [n for (eid, n, _) in self.receipts.values() if eid == effect_id]
        attempt_number = 1 + (max(existing) if existing else 0)
        if any(eid == effect_id and n == attempt_number for (eid, n, _) in self.receipts.values()):
            raise EffectConflictError("receipt_already_recorded")
        stored = receipt.model_copy(
            update={"effect_id": effect_id, "attempt_number": attempt_number}
        )
        self.receipts[stored.receipt_id] = (effect_id, attempt_number, stored)
        return stored

    def get_receipt(self, action_id: str) -> ActionReceiptV17 | None:
        matches = [r for (_, _, r) in self.receipts.values() if r.action_id == action_id]
        if not matches:
            return None
        return max(matches, key=lambda r: r.finished_at or r.started_at or utc_now())

    def list_receipts(self, *, project_id: str, effect_key: str) -> list[ActionReceiptV17]:
        rows = [
            (n, r)
            for (_, n, r) in self.receipts.values()
            if r.project_id == project_id and r.effect_key == effect_key
        ]
        return [r for _, r in sorted(rows, key=lambda t: t[0])]

    def terminal_receipt(self, *, project_id: str, effect_key: str) -> ActionReceiptV17 | None:
        ok = [
            r
            for r in self.list_receipts(project_id=project_id, effect_key=effect_key)
            if r.outcome == "succeeded"
        ]
        return ok[-1] if ok else None

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

    durable = True

    def __init__(self, session: Session) -> None:
        self.session = session

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
        """Atomic reservation: INSERT … ON CONFLICT DO NOTHING on (project_id, effect_key)."""
        envelope.ensure_hashes()
        binding = _binding_of(envelope)
        stmt = (
            pg_insert(ActionEffectRow)
            .values(
                effect_id=new_id("aef_"),
                effect_key=envelope.effect_key,
                project_id=envelope.project_id,
                mission_id=envelope.mission_id,
                task_id=envelope.task_id,
                attempt_id=envelope.attempt_id,
                action_id=envelope.action_id,
                approval_id=envelope.approval_id,
                integration_id=binding["integration_id"],
                integration_version=binding["integration_version"],
                operation=binding["operation"],
                destination_digest=binding["destination_digest"],
                payload_hash=binding["payload_hash"],
                state="reserved",
                lease_generation=envelope.lease_generation,
                cancellation_generation=envelope.cancellation_generation,
                pre_observation={},
                post_observation={},
                reconciliation={},
                payload={},
                attempt_count=0,
            )
            .on_conflict_do_nothing(constraint="uq_action_effect_project_key")
            .returning(ActionEffectRow.effect_id)
        )
        # RETURNING yields the id only for the caller whose INSERT actually landed.
        created = self.session.execute(stmt).scalar_one_or_none() is not None
        self.session.flush()
        row = self._require_row(envelope.project_id, envelope.effect_key)
        as_dict = _effect_dict_from_row(row)
        _check_binding(as_dict, envelope)
        as_dict["created"] = created
        return as_dict

    def mark_executing(
        self, *, project_id: str, effect_key: str, executor_id: str
    ) -> dict[str, Any]:
        """Single-winner compare-and-swap into `executing` (R27b)."""
        stmt = (
            update(ActionEffectRow)
            .where(
                ActionEffectRow.project_id == project_id,
                ActionEffectRow.effect_key == effect_key,
                or_(
                    ActionEffectRow.state == "reserved",
                    and_(
                        ActionEffectRow.state == "failed",
                        ActionEffectRow.state_reason == "not_applied",
                    ),
                ),
            )
            .values(
                state="executing",
                state_reason=None,
                started_at=func.now(),
                executor_id=executor_id,
                attempt_count=ActionEffectRow.attempt_count + 1,
            )
            .returning(ActionEffectRow)
        )
        row = self.session.scalars(stmt).first()
        if row is not None:
            self.session.flush()
            return _effect_dict_from_row(row)
        self.session.rollback()
        current = self._require_row(project_id, effect_key)
        raise _not_executable(current.state, current.state_reason)

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
        """Insert-only. attempt_number computed under FOR UPDATE on the effect row."""
        effect = self.session.scalar(
            select(ActionEffectRow)
            .where(
                ActionEffectRow.project_id == receipt.project_id,
                ActionEffectRow.effect_key == receipt.effect_key,
            )
            .with_for_update()
        )
        if effect is None:
            raise EffectStoreError("effect_not_found")
        if self.session.get(ActionReceiptRow, receipt.receipt_id) is not None:
            raise EffectConflictError("receipt_already_recorded")
        current_max = self.session.scalar(
            select(func.max(ActionReceiptRow.attempt_number)).where(
                ActionReceiptRow.effect_id == effect.effect_id
            )
        )
        attempt_number = 1 + int(current_max or 0)
        stored = receipt.model_copy(
            update={"effect_id": effect.effect_id, "attempt_number": attempt_number}
        )
        row = ActionReceiptRow(
            receipt_id=stored.receipt_id,
            project_id=stored.project_id,
            effect_id=effect.effect_id,
            effect_key=stored.effect_key,
            action_id=stored.action_id,
            attempt_number=attempt_number,
            outcome=stored.outcome,
            reconciliation_state=stored.reconciliation_state,
            evidence_digest=stored.evidence_digest or "",
            receipt=stored.model_dump(mode="json"),
        )
        self.session.add(row)
        try:
            self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            raise EffectConflictError("receipt_already_recorded") from exc
        return stored

    def get_receipt(self, action_id: str) -> ActionReceiptV17 | None:
        row = self.session.scalar(
            select(ActionReceiptRow)
            .where(ActionReceiptRow.action_id == action_id)
            .order_by(ActionReceiptRow.created_at.desc(), ActionReceiptRow.attempt_number.desc())
            .limit(1)
        )
        return None if row is None else ActionReceiptV17.model_validate(row.receipt)

    def list_receipts(self, *, project_id: str, effect_key: str) -> list[ActionReceiptV17]:
        rows = self.session.scalars(
            select(ActionReceiptRow)
            .where(
                ActionReceiptRow.project_id == project_id,
                ActionReceiptRow.effect_key == effect_key,
            )
            .order_by(ActionReceiptRow.attempt_number.asc())
        )
        return [ActionReceiptV17.model_validate(r.receipt) for r in rows]

    def terminal_receipt(self, *, project_id: str, effect_key: str) -> ActionReceiptV17 | None:
        row = self.session.scalar(
            select(ActionReceiptRow)
            .where(
                ActionReceiptRow.project_id == project_id,
                ActionReceiptRow.effect_key == effect_key,
                ActionReceiptRow.outcome == "succeeded",
            )
            .order_by(ActionReceiptRow.attempt_number.desc())
            .limit(1)
        )
        return None if row is None else ActionReceiptV17.model_validate(row.receipt)

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

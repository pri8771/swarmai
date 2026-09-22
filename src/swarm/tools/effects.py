"""ART-V17 — durable action effect reservation store.

R27a: immutable per-attempt receipts. R27b: atomic reservation and single-winner
compare-and-swap into ``executing``. R27c: the durable repository owns its
transactions; ``begin_execution`` is the committed admission point, so a
reservation is visible to every other process before any adapter runs and a
one-shot approval is consumed exactly once.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Mapping
from datetime import timedelta
from typing import Any

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from swarm.contracts.actions import ActionEnvelope, ActionReceiptV17, ApprovalGrant
from swarm.contracts.common import new_id, payload_hash, utc_now
from swarm.db.engine import session_scope
from swarm.db.models import ActionEffectRow, ActionReceiptRow, ApprovalRow

# A fence reader runs inside the admission transaction and returns the current
# fence generations from the module that owns them (leases, later site epochs).
FenceReader = Callable[[Any], Mapping[str, int | None]]

FINALIZABLE_STATES = ("executing", "unknown")


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
        "mission_id": row.mission_id,
        "task_id": row.task_id,
        "attempt_id": row.attempt_id,
        "approval_id": row.approval_id,
        "integration_id": row.integration_id,
        "integration_version": row.integration_version,
        "operation": row.operation,
        "destination_digest": row.destination_digest,
        "payload_hash": row.payload_hash,
        "state": row.state,
        "side_effect_class": (row.payload or {}).get("side_effect_class"),
        "timeout_seconds": (row.payload or {}).get("timeout_seconds"),
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
        "consumed_approval_ids": list((row.payload or {}).get("consumed_approval_ids", [])),
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


def _check_binding(stored: Mapping[str, Any], envelope: ActionEnvelope) -> None:
    """An effect key identifies exactly one (integration, operation, destination, payload)."""
    for field, value in _binding_of(envelope).items():
        if str(stored.get(field)) != value:
            raise EffectConflictError("effect_key_binding_mismatch")


def _check_fence(stored: Mapping[str, Any], current: Mapping[str, int | None]) -> None:
    for key, value in current.items():
        if value is None:
            continue
        if int(stored.get(key) or 0) != int(value):
            raise EffectConflictError("fence_changed_before_execute")


def check_effect_binding(stored: Mapping[str, Any], envelope: ActionEnvelope) -> None:
    _check_binding(stored, envelope)
    if stored.get("side_effect_class") not in (None, envelope.side_effect_class):
        raise EffectConflictError("effect_class_binding_mismatch")
    if stored.get("timeout_seconds") not in (None, envelope.timeout_seconds):
        raise EffectConflictError("effect_timeout_binding_mismatch")
    for field in (
        "mission_id",
        "task_id",
        "attempt_id",
        "lease_generation",
        "cancellation_generation",
    ):
        if stored.get(field) != getattr(envelope, field):
            raise EffectConflictError("effect_authority_binding_mismatch")


class InMemoryEffectStore:
    """Process-local effect store for unit tests and non-consequential local loops.

    Mirrors the durable repository's admission semantics (single winner, exact
    approval consumption) under a process lock so unit tests observe the same
    error strings. It is never a valid store for consequential effects.
    """

    durable = False

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.effects: dict[tuple[str, str], dict[str, Any]] = {}
        # receipt_id -> (effect_id, attempt_number, receipt); insert-only (R27a).
        self.receipts: dict[str, tuple[str, int, ActionReceiptV17]] = {}
        self.approvals: dict[str, ApprovalGrant] = {}

    # ---- approvals (insert-only; revocation monotonic — R27d)
    def put_approval(self, grant: ApprovalGrant) -> ApprovalGrant:
        _check_insertable(grant)
        with self._lock:
            if grant.approval_id in self.approvals:
                raise EffectConflictError("approval_already_exists")
            stored = grant.model_copy(update={"used_count": 0})
            self.approvals[stored.approval_id] = stored
            return stored

    def get_approval(self, approval_id: str, *, project_id: str) -> ApprovalGrant | None:
        grant = self.approvals.get(approval_id)
        if grant is None or grant.project_id != project_id:
            return None
        return grant

    def revoke_approval(
        self, *, project_id: str, approval_id: str, revoked_by: str, reason: str
    ) -> bool:
        with self._lock:
            grant = self.approvals.get(approval_id)
            if grant is None or grant.project_id != project_id or grant.revoked_at is not None:
                return False
            grant.revoked_at = utc_now()
            grant.constraints["revocation"] = {
                "revoked_by": revoked_by,
                "reason": reason,
                "at": grant.revoked_at.isoformat(),
            }
            return True

    # ---- effects
    def reserve(self, envelope: ActionEnvelope) -> dict[str, Any]:
        envelope.ensure_hashes()
        key = (envelope.project_id, envelope.effect_key)
        with self._lock:
            existing = self.effects.get(key)
            if existing is not None:
                _check_binding(existing, envelope)
                return {**existing, "created": False}
            row: dict[str, Any] = {
                "effect_id": new_id("aef_"),
                "effect_key": envelope.effect_key,
                "project_id": envelope.project_id,
                "action_id": envelope.action_id,
                "mission_id": envelope.mission_id,
                "task_id": envelope.task_id,
                "attempt_id": envelope.attempt_id,
                "approval_id": envelope.approval_id,
                "integration_id": envelope.integration_id,
                "integration_version": envelope.integration_version,
                "operation": envelope.operation,
                "destination_digest": payload_hash({"destination": envelope.destination}),
                "payload_hash": envelope.payload_hash,
                "state": "reserved",
                "side_effect_class": envelope.side_effect_class,
                "timeout_seconds": envelope.timeout_seconds,
                "lease_generation": envelope.lease_generation,
                "cancellation_generation": envelope.cancellation_generation,
                "pre_observation": {},
                "post_observation": {},
                "reconciliation": {},
                "created_at": utc_now(),
                "started_at": None,
                "finished_at": None,
                "reconciled_at": None,
                "external_id": None,
                "state_reason": None,
                "attempt_count": 0,
                "executor_id": None,
                "approval_consumed_at": None,
                "consumed_approval_ids": [],
            }
            self.effects[key] = row
            return {**row, "created": True}

    def begin_execution(
        self,
        envelope: ActionEnvelope,
        *,
        executor_id: str,
        fence_reader: FenceReader | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            row = self._require(envelope.project_id, envelope.effect_key)
            check_effect_binding(row, envelope)
            if fence_reader is not None:
                _check_fence(row, fence_reader(None))
            if not _executable(row["state"], row.get("state_reason")):
                raise _not_executable(row["state"], row.get("state_reason"))
            if envelope.approval_id:
                grant = self.approvals.get(envelope.approval_id)
                now = utc_now()
                if (
                    grant is None
                    or grant.project_id != envelope.project_id
                    or grant.revoked_at is not None
                    or grant.expires_at <= now
                ):
                    raise EffectStoreError("approval_not_consumable")
                consumed_ids = set(row["consumed_approval_ids"])
                if row["approval_consumed_at"] is not None and row["approval_id"]:
                    consumed_ids.add(row["approval_id"])
                if envelope.approval_id not in consumed_ids:
                    if grant.used_count >= grant.max_effect_count:
                        raise EffectStoreError("approval_not_consumable")
                    grant.used_count += 1
                    row["approval_consumed_at"] = now
                    consumed_ids.add(envelope.approval_id)
                row["approval_id"] = envelope.approval_id
                row["consumed_approval_ids"] = sorted(consumed_ids)
            row["state"] = "executing"
            row["state_reason"] = None
            row["started_at"] = utc_now()
            row["executor_id"] = executor_id
            row["attempt_count"] = int(row.get("attempt_count") or 0) + 1
            return dict(row)

    def attach_pre_observation(
        self,
        *,
        project_id: str,
        effect_key: str,
        pre_observation: dict[str, Any],
        expected_execution: tuple[str | None, int, str] | None = None,
    ) -> dict[str, Any]:
        if expected_execution is None:
            raise EffectConflictError("execution_token_required")
        with self._lock:
            row = self._require(project_id, effect_key)
            if expected_execution is not None and expected_execution != (
                row.get("executor_id"),
                row["attempt_count"],
                row["state"],
            ):
                raise EffectConflictError("pre_observation_state_conflict")
            row["pre_observation"] = dict(pre_observation)
            return dict(row)

    def finalize_with_receipt(
        self,
        *,
        project_id: str,
        effect_key: str,
        state: str,
        receipt: ActionReceiptV17,
        state_reason: str | None = None,
        post_observation: dict[str, Any] | None = None,
        external_id: str | None = None,
        reconciliation: dict[str, Any] | None = None,
        expected_execution: tuple[str | None, int, str] | None = None,
    ) -> ActionReceiptV17:
        if expected_execution is None:
            raise EffectConflictError("execution_token_required")
        with self._lock:
            row = self._require(project_id, effect_key)
            if expected_execution is not None and expected_execution != (
                row.get("executor_id"),
                row["attempt_count"],
                row["state"],
            ):
                raise EffectConflictError("finalize_state_conflict")
            if row["state"] not in FINALIZABLE_STATES:
                raise EffectConflictError("finalize_state_conflict")
            row["state"] = state
            row["state_reason"] = state_reason
            row["finished_at"] = utc_now()
            if post_observation is not None:
                row["post_observation"] = dict(post_observation)
            if external_id is not None:
                row["external_id"] = external_id
            if reconciliation is not None:
                row["reconciliation"] = dict(reconciliation)
                row["reconciled_at"] = utc_now()
            return self._store_receipt_locked(receipt)

    def recover_orphaned(
        self, *, project_id: str, effect_key: str, grace_seconds: int, timeout_seconds: int
    ) -> bool:
        _validate_recovery_window(grace_seconds, timeout_seconds)
        with self._lock:
            row = self._require(project_id, effect_key)
            cutoff = utc_now() - timedelta(seconds=timeout_seconds + grace_seconds)
            if row["state"] != "executing" or not row["started_at"] or row["started_at"] >= cutoff:
                return False
            row.update(state="unknown", state_reason="executor_lost", finished_at=utc_now())
            return True

    def rearm_irreversible(
        self, *, project_id: str, effect_key: str, operator: str, reason: str
    ) -> None:
        with self._lock:
            row = self._require(project_id, effect_key)
            note = _rearm_note(row, operator, reason)
            row["reconciliation"] = note
            row["state_reason"] = "not_applied"

    def get(self, *, project_id: str, effect_key: str) -> dict[str, Any] | None:
        row = self.effects.get((project_id, effect_key))
        return None if row is None else dict(row)

    # ---- receipts
    def store_receipt(self, receipt: ActionReceiptV17) -> ActionReceiptV17:
        """Insert-only. attempt_number = 1 + max(existing for this effect)."""
        with self._lock:
            return self._store_receipt_locked(receipt)

    def _store_receipt_locked(self, receipt: ActionReceiptV17) -> ActionReceiptV17:
        row = self._require(receipt.project_id, receipt.effect_key)
        effect_id = str(row["effect_id"])
        if receipt.receipt_id in self.receipts:
            raise EffectConflictError("receipt_already_recorded")
        existing = [n for (eid, n, _) in self.receipts.values() if eid == effect_id]
        attempt_number = 1 + (max(existing) if existing else 0)
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
    """SQLAlchemy/PostgreSQL effect + approval + receipt persistence.

    Owns its transactions (R27c): every public method opens one short
    ``session_scope`` and commits before returning. No method accepts or returns
    a live ``Session``; adapters never see one. Returns the same dict shape as
    ``InMemoryEffectStore`` so ``ConsequentialToolGateway`` can use either.
    """

    durable = True

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.factory = session_factory

    # ---- approvals (insert-only; revocation monotonic — R27d)
    def put_approval(self, grant: ApprovalGrant) -> ApprovalGrant:
        _check_insertable(grant)
        stored = grant.model_copy(update={"used_count": 0})
        with session_scope(self.factory) as session:
            session.add(
                ApprovalRow(
                    id=stored.approval_id,
                    payload_hash=stored.payload_hash,
                    permitted_operation=f"{stored.integration_id}.{stored.operation}",
                    destination=stored.destination,
                    grantor=stored.grantor,
                    expires_at=stored.expires_at,
                    revoked_at=None,
                    payload=dict(stored.constraints),
                    project_id=stored.project_id,
                    actor=stored.actor,
                    integration_id=stored.integration_id,
                    integration_version=stored.integration_version,
                    operation=stored.operation,
                    effect_key=stored.effect_key,
                    max_effect_count=stored.max_effect_count,
                    used_count=0,
                    policy_version=stored.policy_version,
                    created_at=stored.created_at,
                    constraints=dict(stored.constraints),
                )
            )
            try:
                session.flush()
            except IntegrityError as exc:
                raise EffectConflictError("approval_already_exists") from exc
        return stored

    def get_approval(self, approval_id: str, *, project_id: str) -> ApprovalGrant | None:
        with session_scope(self.factory) as session:
            row = session.scalar(
                select(ApprovalRow).where(
                    ApprovalRow.id == approval_id, ApprovalRow.project_id == project_id
                )
            )
            if row is None or not _operational(row):
                return None
            return _grant_from_row(row)

    def revoke_approval(
        self, *, project_id: str, approval_id: str, revoked_by: str, reason: str
    ) -> bool:
        with session_scope(self.factory) as session:
            row = session.scalar(
                select(ApprovalRow)
                .where(
                    ApprovalRow.id == approval_id,
                    ApprovalRow.project_id == project_id,
                    ApprovalRow.revoked_at.is_(None),
                )
                .with_for_update()
            )
            if row is None:
                return False
            constraints = dict(row.constraints or {})
            constraints["revocation"] = {
                "revoked_by": revoked_by,
                "reason": reason,
                "at": utc_now().isoformat(),
            }
            changed = session.execute(
                update(ApprovalRow)
                .where(ApprovalRow.id == approval_id, ApprovalRow.revoked_at.is_(None))
                .values(revoked_at=func.now(), constraints=constraints)
                .returning(ApprovalRow.id)
            ).scalar_one_or_none()
            return changed is not None

    # ---- effects
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
                payload={
                    "side_effect_class": envelope.side_effect_class,
                    "timeout_seconds": envelope.timeout_seconds,
                },
                attempt_count=0,
            )
            .on_conflict_do_nothing(constraint="uq_action_effect_project_key")
            .returning(ActionEffectRow.effect_id)
        )
        with session_scope(self.factory) as session:
            # RETURNING yields the id only for the caller whose INSERT actually landed.
            created = session.execute(stmt).scalar_one_or_none() is not None
            row = _require_row(session, envelope.project_id, envelope.effect_key)
            as_dict = _effect_dict_from_row(row)
            _check_binding(as_dict, envelope)
            as_dict["created"] = created
            return as_dict

    def begin_execution(
        self,
        envelope: ActionEnvelope,
        *,
        executor_id: str,
        fence_reader: FenceReader | None = None,
    ) -> dict[str, Any]:
        """Committed admission point: fences, exact approval consumption, CAS — one transaction."""
        envelope.ensure_hashes()
        with session_scope(self.factory) as session:
            row = session.scalar(
                select(ActionEffectRow)
                .where(
                    ActionEffectRow.project_id == envelope.project_id,
                    ActionEffectRow.effect_key == envelope.effect_key,
                )
                .with_for_update()
            )
            if row is None:
                raise EffectStoreError("effect_not_found")
            check_effect_binding(_effect_dict_from_row(row), envelope)
            if fence_reader is not None:
                _check_fence(_effect_dict_from_row(row), fence_reader(session))
            if envelope.approval_id:
                self._consume_approval(session, row, envelope.approval_id)
            updated = _cas_to_executing(
                session,
                project_id=envelope.project_id,
                effect_key=envelope.effect_key,
                executor_id=executor_id,
            )
            if updated is None:
                session.refresh(row)
                raise _not_executable(row.state, row.state_reason)
            return _effect_dict_from_row(updated)

    @staticmethod
    def _consume_approval(session: Session, row: ActionEffectRow, approval_id: str) -> None:
        """Consume a bounded-use approval exactly once per effect; never on revoked/expired."""
        consumed_ids = set((row.payload or {}).get("consumed_approval_ids", []))
        # Preserve attribution for effects admitted before this ledger existed.
        if row.approval_consumed_at is not None and row.approval_id:
            consumed_ids.add(row.approval_id)
        if approval_id not in consumed_ids:
            consumed = session.execute(
                update(ApprovalRow)
                .where(
                    ApprovalRow.id == approval_id,
                    ApprovalRow.project_id == row.project_id,
                    ApprovalRow.revoked_at.is_(None),
                    ApprovalRow.expires_at > func.now(),
                    ApprovalRow.used_count < ApprovalRow.max_effect_count,
                )
                .values(used_count=ApprovalRow.used_count + 1)
                .returning(ApprovalRow.id)
            ).scalar_one_or_none()
            if consumed is None:
                raise EffectStoreError("approval_not_consumable")
            consumed_ids.add(approval_id)
            row.approval_consumed_at = utc_now()
        else:
            still_valid = session.scalar(
                select(ApprovalRow.id)
                .where(
                    ApprovalRow.id == approval_id,
                    ApprovalRow.project_id == row.project_id,
                    ApprovalRow.revoked_at.is_(None),
                    ApprovalRow.expires_at > func.now(),
                )
                .with_for_update()
            )
            if still_valid is None:
                raise EffectStoreError("approval_not_consumable")
        row.approval_id = approval_id
        row.payload = {**(row.payload or {}), "consumed_approval_ids": sorted(consumed_ids)}

    def attach_pre_observation(
        self,
        *,
        project_id: str,
        effect_key: str,
        pre_observation: dict[str, Any],
        expected_execution: tuple[str | None, int, str] | None = None,
    ) -> dict[str, Any]:
        if expected_execution is None:
            raise EffectConflictError("execution_token_required")
        guards = []
        if expected_execution is not None:
            executor, attempt, prior_state = expected_execution
            guards = [
                ActionEffectRow.executor_id == executor,
                ActionEffectRow.attempt_count == attempt,
                ActionEffectRow.state == prior_state,
            ]
        with session_scope(self.factory) as session:
            row = session.scalars(
                update(ActionEffectRow)
                .where(
                    ActionEffectRow.project_id == project_id,
                    ActionEffectRow.effect_key == effect_key,
                    *guards,
                )
                .values(pre_observation=dict(pre_observation))
                .returning(ActionEffectRow)
            ).first()
            if row is None:
                raise EffectConflictError("pre_observation_state_conflict")
            return _effect_dict_from_row(row)

    def finalize_with_receipt(
        self,
        *,
        project_id: str,
        effect_key: str,
        state: str,
        receipt: ActionReceiptV17,
        state_reason: str | None = None,
        post_observation: dict[str, Any] | None = None,
        external_id: str | None = None,
        reconciliation: dict[str, Any] | None = None,
        expected_execution: tuple[str | None, int, str] | None = None,
    ) -> ActionReceiptV17:
        """CAS executing/unknown -> new state and insert the receipt, one transaction."""
        if expected_execution is None:
            raise EffectConflictError("execution_token_required")
        values: dict[str, Any] = {
            "state": state,
            "state_reason": state_reason,
            "finished_at": func.now(),
        }
        if post_observation is not None:
            values["post_observation"] = dict(post_observation)
        if external_id is not None:
            values["external_id"] = external_id
        if reconciliation is not None:
            values["reconciliation"] = dict(reconciliation)
            values["reconciled_at"] = func.now()
        guards = []
        if expected_execution is not None:
            executor, attempt, prior_state = expected_execution
            guards = [
                ActionEffectRow.executor_id == executor,
                ActionEffectRow.attempt_count == attempt,
                ActionEffectRow.state == prior_state,
            ]
        with session_scope(self.factory) as session:
            row = session.scalars(
                update(ActionEffectRow)
                .where(
                    ActionEffectRow.project_id == project_id,
                    ActionEffectRow.effect_key == effect_key,
                    ActionEffectRow.state.in_(FINALIZABLE_STATES),
                    *guards,
                )
                .values(**values)
                .returning(ActionEffectRow)
            ).first()
            if row is None:
                raise EffectConflictError("finalize_state_conflict")
            return _insert_receipt(session, row, receipt)

    def recover_orphaned(
        self, *, project_id: str, effect_key: str, grace_seconds: int, timeout_seconds: int
    ) -> bool:
        _validate_recovery_window(grace_seconds, timeout_seconds)
        cutoff = func.clock_timestamp() - timedelta(seconds=timeout_seconds + grace_seconds)
        with session_scope(self.factory) as session:
            changed = session.execute(
                update(ActionEffectRow)
                .where(
                    ActionEffectRow.project_id == project_id,
                    ActionEffectRow.effect_key == effect_key,
                    ActionEffectRow.state == "executing",
                    ActionEffectRow.started_at < cutoff,
                )
                .values(state="unknown", state_reason="executor_lost", finished_at=func.now())
                .returning(ActionEffectRow.effect_id)
            ).scalar_one_or_none()
            return changed is not None

    def rearm_irreversible(
        self, *, project_id: str, effect_key: str, operator: str, reason: str
    ) -> None:
        with session_scope(self.factory) as session:
            row = session.scalar(
                select(ActionEffectRow)
                .where(
                    ActionEffectRow.project_id == project_id,
                    ActionEffectRow.effect_key == effect_key,
                )
                .with_for_update()
            )
            if row is None:
                raise EffectStoreError("effect_not_found")
            row.reconciliation = _rearm_note(_effect_dict_from_row(row), operator, reason)
            row.state_reason = "not_applied"

    def get(self, *, project_id: str, effect_key: str) -> dict[str, Any] | None:
        with session_scope(self.factory) as session:
            row = session.scalar(
                select(ActionEffectRow).where(
                    ActionEffectRow.project_id == project_id,
                    ActionEffectRow.effect_key == effect_key,
                )
            )
            return None if row is None else _effect_dict_from_row(row)

    # ---- receipts
    def store_receipt(self, receipt: ActionReceiptV17) -> ActionReceiptV17:
        """Insert-only. attempt_number computed under FOR UPDATE on the effect row."""
        with session_scope(self.factory) as session:
            effect = session.scalar(
                select(ActionEffectRow)
                .where(
                    ActionEffectRow.project_id == receipt.project_id,
                    ActionEffectRow.effect_key == receipt.effect_key,
                )
                .with_for_update()
            )
            if effect is None:
                raise EffectStoreError("effect_not_found")
            return _insert_receipt(session, effect, receipt)

    def get_receipt(self, action_id: str) -> ActionReceiptV17 | None:
        with session_scope(self.factory) as session:
            row = session.scalar(
                select(ActionReceiptRow)
                .where(ActionReceiptRow.action_id == action_id)
                .order_by(
                    ActionReceiptRow.created_at.desc(), ActionReceiptRow.attempt_number.desc()
                )
                .limit(1)
            )
            return None if row is None else ActionReceiptV17.model_validate(row.receipt)

    def list_receipts(self, *, project_id: str, effect_key: str) -> list[ActionReceiptV17]:
        with session_scope(self.factory) as session:
            rows = session.scalars(
                select(ActionReceiptRow)
                .where(
                    ActionReceiptRow.project_id == project_id,
                    ActionReceiptRow.effect_key == effect_key,
                )
                .order_by(ActionReceiptRow.attempt_number.asc())
            )
            return [ActionReceiptV17.model_validate(r.receipt) for r in rows]

    def terminal_receipt(self, *, project_id: str, effect_key: str) -> ActionReceiptV17 | None:
        with session_scope(self.factory) as session:
            row = session.scalar(
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


# ---- transaction-internal helpers (take an open Session; never commit)


def _require_row(session: Session, project_id: str, effect_key: str) -> ActionEffectRow:
    row = session.scalar(
        select(ActionEffectRow).where(
            ActionEffectRow.project_id == project_id,
            ActionEffectRow.effect_key == effect_key,
        )
    )
    if row is None:
        raise EffectStoreError("effect_not_found")
    return row


def _cas_to_executing(
    session: Session, *, project_id: str, effect_key: str, executor_id: str
) -> ActionEffectRow | None:
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
    return session.scalars(stmt).first()


def _insert_receipt(
    session: Session, effect: ActionEffectRow, receipt: ActionReceiptV17
) -> ActionReceiptV17:
    if session.get(ActionReceiptRow, receipt.receipt_id) is not None:
        raise EffectConflictError("receipt_already_recorded")
    current_max = session.scalar(
        select(func.max(ActionReceiptRow.attempt_number)).where(
            ActionReceiptRow.effect_id == effect.effect_id
        )
    )
    attempt_number = 1 + int(current_max or 0)
    stored = receipt.model_copy(
        update={"effect_id": effect.effect_id, "attempt_number": attempt_number}
    )
    session.add(
        ActionReceiptRow(
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
    )
    try:
        session.flush()
    except IntegrityError as exc:
        raise EffectConflictError("receipt_already_recorded") from exc
    return stored


# Legacy approval rows whose V1.7 binding columns are NULL are non-operational
# until reconciled by governance; they are never defaulted into validity.
_REQUIRED_APPROVAL_BINDING = (
    "project_id",
    "integration_id",
    "integration_version",
    "operation",
    "policy_version",
)


def _operational(row: ApprovalRow) -> bool:
    return all(getattr(row, column) is not None for column in _REQUIRED_APPROVAL_BINDING)


def _check_insertable(grant: ApprovalGrant) -> None:
    if grant.revoked_at is not None:
        raise EffectStoreError("approval_insert_revoked")


def _grant_from_row(row: ApprovalRow) -> ApprovalGrant:
    assert _operational(row)
    return ApprovalGrant(
        approval_id=row.id,
        project_id=str(row.project_id),
        actor=row.actor,
        grantor=row.grantor,
        integration_id=str(row.integration_id),
        integration_version=str(row.integration_version),
        operation=str(row.operation),
        destination=row.destination,
        payload_hash=row.payload_hash,
        effect_key=row.effect_key,
        max_effect_count=int(row.max_effect_count or 1),
        used_count=int(row.used_count or 0),
        expires_at=row.expires_at,
        revoked_at=row.revoked_at,
        policy_version=str(row.policy_version),
        constraints=dict(row.constraints or {}),
        created_at=row.created_at or utc_now(),
    )


def _validate_recovery_window(grace_seconds: int, timeout_seconds: int) -> None:
    if grace_seconds < 0 or timeout_seconds <= 0:
        raise ValueError("invalid_recovery_window")


def _rearm_note(row: Mapping[str, Any], operator: str, reason: str) -> dict[str, Any]:
    if not operator.strip() or not reason.strip():
        raise EffectStoreError("operator_and_reason_required")
    if (
        row["state"] != "failed"
        or row.get("state_reason") != "irreversible_requires_operator_disposition"
    ):
        raise EffectConflictError("irreversible_rearm_not_allowed")
    note = dict(row.get("reconciliation") or {})
    notes = list(note.get("operator_rearms") or [])
    notes.append({"operator": operator, "reason": reason, "at": utc_now().isoformat()})
    note["operator_rearms"] = notes
    return note

"""PostgreSQL SchedulingStore — same semantics as InMemorySchedulingStore.

Each call is its own transaction (``session_scope``). Updates lock the row with
``SELECT … FOR UPDATE`` and compare ``version`` before writing, so two schedulers
racing on the same row get exactly one winner and one StaleVersionError.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from swarm.contracts.v23 import (
    DispatchIntent,
    DispatchIntentState,
    MissionQueueState,
    ProjectQueueState,
    SchedulingDecisionReceipt,
    StaleVersionError,
)
from swarm.db.engine import session_scope
from swarm.db.models import (
    V23DispatchIntentRow,
    V23MissionQueueStateRow,
    V23ProjectQueueStateRow,
    V23SchedulerReceiptRow,
)


def _dump(model: Any) -> dict[str, Any]:
    return model.model_dump(mode="json")  # type: ignore[no-any-return]


class SqlSchedulingStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._factory = session_factory

    # -- projects -----------------------------------------------------------
    def get_project(self, project_id: str) -> ProjectQueueState | None:
        with session_scope(self._factory) as s:
            row = s.get(V23ProjectQueueStateRow, project_id)
            return ProjectQueueState.model_validate(row.payload) if row else None

    def list_projects(self) -> list[ProjectQueueState]:
        with session_scope(self._factory) as s:
            rows = s.scalars(
                select(V23ProjectQueueStateRow).order_by(V23ProjectQueueStateRow.project_id)
            )
            return [ProjectQueueState.model_validate(r.payload) for r in rows]

    def put_project(
        self, state: ProjectQueueState, *, expected_version: int | None
    ) -> ProjectQueueState:
        with session_scope(self._factory) as s:
            row = s.scalar(
                select(V23ProjectQueueStateRow)
                .where(V23ProjectQueueStateRow.project_id == state.project_id)
                .with_for_update()
            )
            current = row.version if row else None
            new_version = _next_version(current, expected_version, state.project_id)
            stored = state.model_copy(update={"version": new_version})
            if row is None:
                s.add(
                    V23ProjectQueueStateRow(
                        project_id=stored.project_id,
                        tenant_id=stored.tenant_id,
                        version=new_version,
                        payload=_dump(stored),
                    )
                )
            else:
                row.tenant_id = stored.tenant_id
                row.version = new_version
                row.payload = _dump(stored)
            _flush_or_stale(s, state.project_id)
            return stored

    # -- missions -----------------------------------------------------------
    def get_mission(self, mission_id: str) -> MissionQueueState | None:
        with session_scope(self._factory) as s:
            row = s.get(V23MissionQueueStateRow, mission_id)
            return MissionQueueState.model_validate(row.payload) if row else None

    def list_missions(self, project_id: str | None = None) -> list[MissionQueueState]:
        with session_scope(self._factory) as s:
            stmt = select(V23MissionQueueStateRow).order_by(V23MissionQueueStateRow.mission_id)
            if project_id is not None:
                stmt = stmt.where(V23MissionQueueStateRow.project_id == project_id)
            return [MissionQueueState.model_validate(r.payload) for r in s.scalars(stmt)]

    def put_mission(
        self, state: MissionQueueState, *, expected_version: int | None
    ) -> MissionQueueState:
        with session_scope(self._factory) as s:
            row = s.scalar(
                select(V23MissionQueueStateRow)
                .where(V23MissionQueueStateRow.mission_id == state.mission_id)
                .with_for_update()
            )
            current = row.version if row else None
            new_version = _next_version(current, expected_version, state.mission_id)
            stored = state.model_copy(update={"version": new_version})
            if row is None:
                s.add(
                    V23MissionQueueStateRow(
                        mission_id=stored.mission_id,
                        project_id=stored.project_id,
                        lifecycle=stored.lifecycle.value,
                        version=new_version,
                        payload=_dump(stored),
                    )
                )
            else:
                row.project_id = stored.project_id
                row.lifecycle = stored.lifecycle.value
                row.version = new_version
                row.payload = _dump(stored)
            _flush_or_stale(s, state.mission_id)
            return stored

    # -- receipts -----------------------------------------------------------
    def next_sequence(self) -> int:
        """Max stored sequence + 1. Uniqueness is enforced by the DB constraint;
        callers hold the scheduler epoch, so collisions mean a fencing bug."""
        with session_scope(self._factory) as s:
            current = s.scalar(select(func.coalesce(func.max(V23SchedulerReceiptRow.sequence), 0)))
            return int(current or 0) + 1

    def append_receipt(self, receipt: SchedulingDecisionReceipt) -> None:
        with session_scope(self._factory) as s:
            s.add(
                V23SchedulerReceiptRow(
                    receipt_id=receipt.receipt_id,
                    sequence=receipt.sequence,
                    project_id=receipt.project_id,
                    decision=receipt.decision.value,
                    reason_code=receipt.reason_code.value,
                    digest=receipt.digest(),
                    payload=_dump(receipt),
                )
            )
            _flush_or_stale(s, f"receipt_sequence:{receipt.sequence}")

    def list_receipts(
        self, *, project_id: str | None = None, limit: int = 100
    ) -> list[SchedulingDecisionReceipt]:
        with session_scope(self._factory) as s:
            stmt = select(V23SchedulerReceiptRow).order_by(V23SchedulerReceiptRow.sequence.desc())
            if project_id is not None:
                stmt = stmt.where(V23SchedulerReceiptRow.project_id == project_id)
            rows = list(s.scalars(stmt.limit(limit)))
            rows.reverse()
            return [SchedulingDecisionReceipt.model_validate(r.payload) for r in rows]

    # -- intents ------------------------------------------------------------
    def get_intent(self, intent_id: str) -> DispatchIntent | None:
        with session_scope(self._factory) as s:
            row = s.get(V23DispatchIntentRow, intent_id)
            return DispatchIntent.model_validate(row.payload) if row else None

    def get_intent_by_attempt(self, attempt_id: str) -> DispatchIntent | None:
        with session_scope(self._factory) as s:
            row = s.scalar(
                select(V23DispatchIntentRow).where(V23DispatchIntentRow.attempt_id == attempt_id)
            )
            return DispatchIntent.model_validate(row.payload) if row else None

    def put_intent(
        self, intent: DispatchIntent, *, expected_version: int | None
    ) -> DispatchIntent:
        with session_scope(self._factory) as s:
            row = s.scalar(
                select(V23DispatchIntentRow)
                .where(V23DispatchIntentRow.intent_id == intent.intent_id)
                .with_for_update()
            )
            current = row.version if row else None
            new_version = _next_version(current, expected_version, intent.intent_id)
            stored = intent.model_copy(update={"version": new_version})
            if row is None:
                s.add(
                    V23DispatchIntentRow(
                        intent_id=stored.intent_id,
                        attempt_id=stored.attempt_id,
                        project_id=stored.project_id,
                        state=stored.state.value,
                        expires_at=stored.expires_at,
                        version=new_version,
                        payload=_dump(stored),
                    )
                )
            else:
                row.state = stored.state.value
                row.expires_at = stored.expires_at
                row.version = new_version
                row.payload = _dump(stored)
            _flush_or_stale(s, f"attempt:{intent.attempt_id}")
            return stored

    def list_intents(
        self, *, states: frozenset[DispatchIntentState] | None = None
    ) -> list[DispatchIntent]:
        with session_scope(self._factory) as s:
            stmt = select(V23DispatchIntentRow).order_by(V23DispatchIntentRow.intent_id)
            if states is not None:
                stmt = stmt.where(V23DispatchIntentRow.state.in_([x.value for x in states]))
            return [DispatchIntent.model_validate(r.payload) for r in s.scalars(stmt)]


def _next_version(current: int | None, expected: int | None, key: str) -> int:
    if expected is None:
        if current is not None:
            raise StaleVersionError(f"already_exists:{key}")
        return 1
    if current != expected:
        raise StaleVersionError(f"stale_version:{key}:expected={expected}:actual={current}")
    return expected + 1


def _flush_or_stale(session: Session, key: str) -> None:
    try:
        session.flush()
    except IntegrityError as exc:
        raise StaleVersionError(f"conflict:{key}") from exc

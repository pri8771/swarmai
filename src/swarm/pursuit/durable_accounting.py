"""V20-E04: durable goal usage holds and pursuit lessons.

``bind_durable_ledger`` restores a ledger's holds from a ``HoldStore`` and makes
every later hold change write to the store *before* it is visible in memory.
Lesson persistence follows the same DB-first rule via ``LessonPersistence``.
"""

from __future__ import annotations

from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from swarm.pursuit.accounting import GoalResourceLedger, ResourceHold, UsageAmounts
from swarm.pursuit.models import PursuitLesson


class DurableAccountingError(RuntimeError):
    pass


def _amounts(d: dict[str, Any] | None) -> UsageAmounts | None:
    if d is None:
        return None
    return UsageAmounts(
        spend_usd=float(d.get("spend_usd") or 0.0),
        model_calls=int(d.get("model_calls") or 0),
        tool_calls=int(d.get("tool_calls") or 0),
        prompt_tokens=d.get("prompt_tokens"),
        completion_tokens=d.get("completion_tokens"),
        route_id=d.get("route_id"),
        runtime=d.get("runtime"),
        usage_unknown=bool(d.get("usage_unknown", False)),
    )


def hold_from_dict(d: dict[str, Any]) -> ResourceHold:
    reserved = _amounts(d.get("reserved")) or UsageAmounts()
    return ResourceHold(
        hold_id=str(d["hold_id"]),
        goal_id=str(d["goal_id"]),
        mission_id=str(d["mission_id"]),
        reserved=reserved,
        state=d["state"],
        settled=_amounts(d.get("settled")),
        created_at=str(d["created_at"]),
        updated_at=str(d["updated_at"]),
    )


class HoldStore(Protocol):
    def put(self, hold: ResourceHold) -> None: ...

    def list_for_goal(self, goal_id: str) -> list[ResourceHold]: ...


class InMemoryHoldStore:
    def __init__(self) -> None:
        self._rows: dict[str, dict[str, Any]] = {}

    def put(self, hold: ResourceHold) -> None:
        self._rows[hold.hold_id] = hold.to_dict()

    def list_for_goal(self, goal_id: str) -> list[ResourceHold]:
        rows = [r for r in self._rows.values() if r["goal_id"] == goal_id]
        rows.sort(key=lambda r: (r["created_at"], r["hold_id"]))
        return [hold_from_dict(r) for r in rows]


class SqlHoldStore:
    """PostgreSQL ``v20_goal_usage_holds``; one transaction per change."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._factory = session_factory

    def put(self, hold: ResourceHold) -> None:
        from swarm.db.engine import session_scope
        from swarm.db.models import V20GoalUsageHoldRow

        try:
            with session_scope(self._factory) as s:
                row = s.get(V20GoalUsageHoldRow, hold.hold_id, with_for_update=True)
                if row is None:
                    s.add(
                        V20GoalUsageHoldRow(
                            hold_id=hold.hold_id,
                            goal_id=hold.goal_id,
                            mission_id=hold.mission_id,
                            state=hold.state,
                            version=1,
                            payload=hold.to_dict(),
                        )
                    )
                else:
                    row.state = hold.state
                    row.version = row.version + 1
                    row.payload = hold.to_dict()
        except Exception as exc:  # noqa: BLE001 - fail closed on any DB error
            raise DurableAccountingError(f"hold_persist_failed:{type(exc).__name__}") from exc

    def list_for_goal(self, goal_id: str) -> list[ResourceHold]:
        from swarm.db.engine import session_scope
        from swarm.db.models import V20GoalUsageHoldRow

        stmt = select(V20GoalUsageHoldRow).where(V20GoalUsageHoldRow.goal_id == goal_id)
        try:
            with session_scope(self._factory) as s:
                payloads = [dict(r.payload) for r in s.execute(stmt).scalars()]
        except Exception as exc:  # noqa: BLE001
            raise DurableAccountingError(f"hold_load_failed:{type(exc).__name__}") from exc
        payloads.sort(key=lambda r: (r["created_at"], r["hold_id"]))
        return [hold_from_dict(p) for p in payloads]


def bind_durable_ledger(ledger: GoalResourceLedger, store: HoldStore) -> GoalResourceLedger:
    """Restore holds for ``ledger.goal_id`` and persist every later change first."""
    ledger.holds = {h.hold_id: h for h in store.list_for_goal(ledger.goal_id)}
    ledger.on_change = store.put
    return ledger


class LessonPersistence(Protocol):
    def put(self, lesson: PursuitLesson) -> None: ...

    def load_all(self) -> list[PursuitLesson]: ...


class InMemoryLessonPersistence:
    def __init__(self) -> None:
        self._rows: dict[str, dict[str, Any]] = {}

    def put(self, lesson: PursuitLesson) -> None:
        self._rows[lesson.lesson_id] = lesson.model_dump(mode="json")

    def load_all(self) -> list[PursuitLesson]:
        rows = sorted(self._rows.values(), key=lambda r: (r["created_at"], r["lesson_id"]))
        return [PursuitLesson.model_validate(r) for r in rows]


class SqlLessonPersistence:
    """PostgreSQL ``v20_pursuit_lessons``."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._factory = session_factory

    def put(self, lesson: PursuitLesson) -> None:
        from swarm.db.engine import session_scope
        from swarm.db.models import V20PursuitLessonRow

        payload = lesson.model_dump(mode="json")
        try:
            with session_scope(self._factory) as s:
                row = s.get(V20PursuitLessonRow, lesson.lesson_id, with_for_update=True)
                if row is None:
                    s.add(
                        V20PursuitLessonRow(
                            lesson_id=lesson.lesson_id,
                            goal_id=lesson.goal_id,
                            state=lesson.state.value,
                            payload=payload,
                        )
                    )
                else:
                    row.state = lesson.state.value
                    row.payload = payload
        except Exception as exc:  # noqa: BLE001
            raise DurableAccountingError(f"lesson_persist_failed:{type(exc).__name__}") from exc

    def load_all(self) -> list[PursuitLesson]:
        from swarm.db.engine import session_scope
        from swarm.db.models import V20PursuitLessonRow

        try:
            with session_scope(self._factory) as s:
                rows = s.execute(select(V20PursuitLessonRow)).scalars()
                payloads = [dict(r.payload) for r in rows]
        except Exception as exc:  # noqa: BLE001
            raise DurableAccountingError(f"lesson_load_failed:{type(exc).__name__}") from exc
        payloads.sort(key=lambda r: (r["created_at"], r["lesson_id"]))
        return [PursuitLesson.model_validate(p) for p in payloads]

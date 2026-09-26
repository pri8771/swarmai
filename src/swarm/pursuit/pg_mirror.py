"""V20-E03: PostgreSQL write-through for pursuit runtime snapshots.

The whole snapshot is stored in ``pursuit_schedules.payload["snapshot"]``; cycles
and dedupe keys are also written to ``pursuit_cycles`` / ``pursuit_dedupe`` so
they can be queried. One transaction per save. Any database error becomes
``PursuitMirrorError`` so callers fail closed instead of silently diverging.
"""

from __future__ import annotations

import hashlib
from typing import Any, Protocol

from sqlalchemy.orm import Session, sessionmaker

MAX_KEY_LEN = 64


class PursuitMirrorError(RuntimeError):
    pass


class PursuitMirror(Protocol):
    def write_snapshot(self, goal_id: str, snapshot: dict[str, Any]) -> None: ...

    def load_snapshot(self, goal_id: str) -> dict[str, Any] | None: ...


def dedupe_db_key(key: str) -> str:
    """Keys longer than the column width are replaced by their sha256 hex (64 chars)."""
    if len(key) <= MAX_KEY_LEN:
        return key
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


class PursuitPgMirror:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._factory = session_factory

    def write_snapshot(self, goal_id: str, snapshot: dict[str, Any]) -> None:
        from swarm.db.engine import session_scope
        from swarm.db.models import PursuitCycleRow
        from swarm.db.repositories import PursuitStateRepository

        schedule = snapshot.get("schedule") or {}
        try:
            with session_scope(self._factory) as s:
                repo = PursuitStateRepository(s)
                repo.upsert_schedule(
                    goal_id=goal_id,
                    next_due_at=float(schedule.get("next_due_at") or 0.0),
                    backoff_seconds=float(schedule.get("backoff_seconds") or 0.0),
                    consecutive_failures=int(schedule.get("consecutive_failures") or 0),
                    consecutive_no_progress=int(schedule.get("consecutive_no_progress") or 0),
                    last_cycle_at=schedule.get("last_cycle_at"),
                    wait_reason=schedule.get("wait_reason"),
                    payload={"snapshot": snapshot},
                )
                for cycle in snapshot.get("history") or []:
                    cycle_id = str(cycle["cycle_id"])
                    if s.get(PursuitCycleRow, cycle_id) is not None:
                        continue
                    repo.append_cycle(
                        cycle_id=cycle_id,
                        goal_id=goal_id,
                        phase=str(cycle["phase"]),
                        decided_kind=cycle.get("decided_kind"),
                        payload=cycle,
                    )
                for key, proposal_id in sorted((snapshot.get("dedupe") or {}).items()):
                    repo.put_dedupe(
                        goal_id=goal_id,
                        dedupe_key=dedupe_db_key(str(key)),
                        proposal_id=str(proposal_id),
                        payload={"key": str(key)},
                    )
        except PursuitMirrorError:
            raise
        except Exception as exc:  # noqa: BLE001 - any DB failure must fail closed
            raise PursuitMirrorError(f"pursuit_mirror_write_failed:{type(exc).__name__}") from exc

    def load_snapshot(self, goal_id: str) -> dict[str, Any] | None:
        from swarm.db.engine import session_scope
        from swarm.db.models import PursuitScheduleRow

        try:
            with session_scope(self._factory) as s:
                row = s.get(PursuitScheduleRow, goal_id)
                payload = dict(row.payload or {}) if row is not None else None
        except Exception as exc:  # noqa: BLE001
            raise PursuitMirrorError(f"pursuit_mirror_read_failed:{type(exc).__name__}") from exc
        if payload is None:
            return None
        snap = payload.get("snapshot")
        return dict(snap) if isinstance(snap, dict) else None

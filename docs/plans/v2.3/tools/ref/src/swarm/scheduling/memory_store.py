"""In-memory SchedulingStore — reference semantics for the SQL store and for tests."""

from __future__ import annotations

import threading

from swarm.contracts.common import utc_now
from swarm.contracts.v23 import (
    DispatchIntent,
    DispatchIntentState,
    MissionQueueState,
    ProjectQueueState,
    SchedulingDecisionReceipt,
    StaleVersionError,
)


class InMemorySchedulingStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._projects: dict[str, ProjectQueueState] = {}
        self._missions: dict[str, MissionQueueState] = {}
        self._receipts: list[SchedulingDecisionReceipt] = []
        self._intents: dict[str, DispatchIntent] = {}
        self._intent_by_attempt: dict[str, str] = {}
        self._sequence = 0

    @staticmethod
    def _check(current_version: int | None, expected_version: int | None, key: str) -> int:
        if expected_version is None:
            if current_version is not None:
                raise StaleVersionError(f"already_exists:{key}")
            return 1
        if current_version != expected_version:
            raise StaleVersionError(
                f"stale_version:{key}:expected={expected_version}:actual={current_version}"
            )
        return expected_version + 1

    def get_project(self, project_id: str) -> ProjectQueueState | None:
        with self._lock:
            row = self._projects.get(project_id)
            return row.model_copy() if row else None

    def list_projects(self) -> list[ProjectQueueState]:
        with self._lock:
            return [self._projects[k].model_copy() for k in sorted(self._projects)]

    def put_project(
        self, state: ProjectQueueState, *, expected_version: int | None
    ) -> ProjectQueueState:
        with self._lock:
            cur = self._projects.get(state.project_id)
            version = self._check(cur.version if cur else None, expected_version, state.project_id)
            stored = state.model_copy(update={"version": version, "updated_at": utc_now()})
            self._projects[state.project_id] = stored
            return stored.model_copy()

    def get_mission(self, mission_id: str) -> MissionQueueState | None:
        with self._lock:
            row = self._missions.get(mission_id)
            return row.model_copy() if row else None

    def list_missions(self, project_id: str | None = None) -> list[MissionQueueState]:
        with self._lock:
            rows = [self._missions[k] for k in sorted(self._missions)]
            if project_id is not None:
                rows = [m for m in rows if m.project_id == project_id]
            return [m.model_copy() for m in rows]

    def put_mission(
        self, state: MissionQueueState, *, expected_version: int | None
    ) -> MissionQueueState:
        with self._lock:
            cur = self._missions.get(state.mission_id)
            version = self._check(cur.version if cur else None, expected_version, state.mission_id)
            stored = state.model_copy(update={"version": version, "updated_at": utc_now()})
            self._missions[state.mission_id] = stored
            return stored.model_copy()

    def next_sequence(self) -> int:
        with self._lock:
            self._sequence += 1
            return self._sequence

    def append_receipt(self, receipt: SchedulingDecisionReceipt) -> None:
        with self._lock:
            if any(r.sequence == receipt.sequence for r in self._receipts):
                raise StaleVersionError(f"duplicate_receipt_sequence:{receipt.sequence}")
            self._receipts.append(receipt.model_copy())

    def list_receipts(
        self, *, project_id: str | None = None, limit: int = 100
    ) -> list[SchedulingDecisionReceipt]:
        with self._lock:
            rows = sorted(self._receipts, key=lambda r: r.sequence)
            if project_id is not None:
                rows = [r for r in rows if r.project_id == project_id]
            return [r.model_copy() for r in rows[-limit:]]

    def get_intent(self, intent_id: str) -> DispatchIntent | None:
        with self._lock:
            row = self._intents.get(intent_id)
            return row.model_copy() if row else None

    def get_intent_by_attempt(self, attempt_id: str) -> DispatchIntent | None:
        with self._lock:
            intent_id = self._intent_by_attempt.get(attempt_id)
            return self.get_intent(intent_id) if intent_id else None

    def put_intent(
        self, intent: DispatchIntent, *, expected_version: int | None
    ) -> DispatchIntent:
        with self._lock:
            cur = self._intents.get(intent.intent_id)
            if expected_version is None:
                other = self._intent_by_attempt.get(intent.attempt_id)
                if other is not None:
                    raise StaleVersionError(f"attempt_already_has_intent:{intent.attempt_id}")
            version = self._check(cur.version if cur else None, expected_version, intent.intent_id)
            stored = intent.model_copy(update={"version": version, "updated_at": utc_now()})
            self._intents[intent.intent_id] = stored
            self._intent_by_attempt[intent.attempt_id] = intent.intent_id
            return stored.model_copy()

    def list_intents(
        self, *, states: frozenset[DispatchIntentState] | None = None
    ) -> list[DispatchIntent]:
        with self._lock:
            rows = [self._intents[k] for k in sorted(self._intents)]
            if states is not None:
                rows = [i for i in rows if i.state in states]
            return [i.model_copy() for i in rows]

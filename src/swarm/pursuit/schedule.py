"""Schedules, backoff, and due-time gating for pursuit cycles."""

from __future__ import annotations

import time
from collections.abc import Callable

from swarm.pursuit.models import ContributionKind, ScheduleState

# Backoff ladder (seconds). Inject clocks in tests; operational default is wall time.
_BACKOFF_STEPS = (0.0, 5.0, 15.0, 60.0, 300.0, 900.0)
_MAX_BACKOFF = 3600.0


class PursuitScheduler:
    """Event/schedule/backoff gate — prevents endless polling."""

    def __init__(self, *, clock: Callable[[], float] | None = None) -> None:
        # R20-04: wall clock by default; tests inject deterministic clocks.
        # A constant-zero clock is not an autonomous scheduler.
        self._clock = clock or time.time
        self._states: dict[str, ScheduleState] = {}

    def now(self) -> float:
        return float(self._clock())

    def load_state(self, state: ScheduleState) -> None:
        """Restore a persisted schedule for reopen / crash recovery."""
        self._states[state.goal_id] = state

    def dump_states(self) -> dict[str, ScheduleState]:
        return dict(self._states)

    def get(self, goal_id: str) -> ScheduleState:
        state = self._states.get(goal_id)
        if state is None:
            state = ScheduleState(goal_id=goal_id, next_due_at=self.now())
            self._states[goal_id] = state
        return state

    def is_due(self, goal_id: str) -> bool:
        return self.now() >= self.get(goal_id).next_due_at

    def defer(
        self, goal_id: str, *, reason: str, kind: ContributionKind = ContributionKind.WAIT
    ) -> ScheduleState:
        state = self.get(goal_id)
        backoff = max(state.backoff_seconds, 5.0)
        state = state.model_copy(
            update={
                "next_due_at": self.now() + backoff,
                "last_action": kind,
                "wait_reason": reason,
                "last_cycle_at": self.now(),
            }
        )
        self._states[goal_id] = state
        return state

    def note_success(
        self, goal_id: str, *, kind: ContributionKind, cadence_seconds: float = 1.0
    ) -> ScheduleState:
        state = self.get(goal_id)
        state = state.model_copy(
            update={
                "backoff_seconds": 0.0,
                "consecutive_failures": 0,
                "consecutive_no_progress": 0,
                "next_due_at": self.now() + max(0.0, cadence_seconds),
                "last_action": kind,
                "wait_reason": None,
                "last_cycle_at": self.now(),
            }
        )
        self._states[goal_id] = state
        return state

    def note_failure(
        self, goal_id: str, *, kind: ContributionKind, no_progress: bool = False
    ) -> ScheduleState:
        state = self.get(goal_id)
        failures = state.consecutive_failures + 1
        no_prog = state.consecutive_no_progress + (1 if no_progress else 0)
        idx = min(failures, len(_BACKOFF_STEPS) - 1)
        backoff = min(_BACKOFF_STEPS[idx] * (2 if no_prog >= 3 else 1), _MAX_BACKOFF)
        state = state.model_copy(
            update={
                "consecutive_failures": failures,
                "consecutive_no_progress": no_prog,
                "backoff_seconds": backoff,
                "next_due_at": self.now() + backoff,
                "last_action": kind,
                "wait_reason": "backoff_after_failure",
                "last_cycle_at": self.now(),
            }
        )
        self._states[goal_id] = state
        return state

    def force_due(self, goal_id: str) -> ScheduleState:
        state = self.get(goal_id)
        state = state.model_copy(update={"next_due_at": self.now()})
        self._states[goal_id] = state
        return state

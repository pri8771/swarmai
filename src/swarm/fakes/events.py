"""Deterministic event generator for later simulations."""

from __future__ import annotations

from swarm.contracts.common import new_id
from swarm.contracts.workspace import EventEnvelope
from swarm.fakes.clock import FakeClock


class FakeEventGenerator:
    def __init__(self, clock: FakeClock, project_id: str = "proj_demo") -> None:
        self.clock = clock
        self.project_id = project_id
        self._seq = 0

    def emit(
        self,
        event_type: str,
        *,
        actor: str = "system",
        mission_id: str | None = None,
        task_id: str | None = None,
        attempt_id: str | None = None,
        payload: dict[str, object] | None = None,
        causation_id: str | None = None,
    ) -> EventEnvelope:
        self._seq += 1
        return EventEnvelope(
            id=new_id("ev_"),
            occurred_at=self.clock.now(),
            project_id=self.project_id,
            actor=actor,
            type=event_type,
            mission_id=mission_id,
            task_id=task_id,
            attempt_id=attempt_id,
            payload=payload or {},
            causation_id=causation_id,
            correlation_id=mission_id,
            dedupe_key=f"{event_type}:{self._seq}",
        )

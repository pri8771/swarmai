"""Durable event log with continuation cursor and dedupe."""

from __future__ import annotations

from dataclasses import dataclass, field

from swarm.contracts.workspace import EventEnvelope


@dataclass
class EventLog:
    """Mission-local ordering via revision in payload; no global order promise."""

    _events: list[EventEnvelope] = field(default_factory=list)
    _by_id: dict[str, EventEnvelope] = field(default_factory=dict)
    _dedupe: dict[str, str] = field(default_factory=dict)  # dedupe_key -> event_id
    _seq: int = 0

    def append(self, event: EventEnvelope) -> EventEnvelope:
        if event.dedupe_key:
            existing_id = self._dedupe.get(event.dedupe_key)
            if existing_id is not None:
                return self._by_id[existing_id]
        self._seq += 1
        # Preserve caller id; cursor uses append order index encoded as after=id.
        self._events.append(event)
        self._by_id[event.id] = event
        if event.dedupe_key:
            self._dedupe[event.dedupe_key] = event.id
        return event

    def list_after(
        self,
        *,
        project_id: str | None = None,
        mission_id: str | None = None,
        after: str | None = None,
        limit: int = 50,
    ) -> tuple[list[EventEnvelope], str | None]:
        start = 0
        if after:
            # Cursor is event id; resume *after* that event in append order.
            for i, ev in enumerate(self._events):
                if ev.id == after:
                    start = i + 1
                    break
            else:
                # Unknown cursor: return from start (client should reconcile by id).
                start = 0
        out: list[EventEnvelope] = []
        for ev in self._events[start:]:
            if project_id is not None and ev.project_id != project_id:
                continue
            if mission_id is not None and ev.mission_id != mission_id:
                continue
            out.append(ev)
            if len(out) >= limit:
                break
        cursor = out[-1].id if out else after
        return out, cursor

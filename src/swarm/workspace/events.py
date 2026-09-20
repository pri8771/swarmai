"""Fine-grained event subscriptions for workspace changes."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field

from swarm.contracts.workspace import EventEnvelope

Listener = Callable[[EventEnvelope], None]


@dataclass
class Subscription:
    subscription_id: str
    project_id: str
    event_types: set[str]
    mission_id: str | None = None
    task_id: str | None = None
    scopes: set[str] = field(default_factory=set)


class EventBus:
    def __init__(self) -> None:
        self._subs: dict[str, Subscription] = {}
        self._listeners: dict[str, list[Listener]] = defaultdict(list)
        self._log: list[EventEnvelope] = []

    def subscribe(
        self,
        subscription_id: str,
        *,
        project_id: str,
        event_types: set[str],
        mission_id: str | None = None,
        task_id: str | None = None,
        scopes: set[str] | None = None,
        listener: Listener | None = None,
    ) -> Subscription:
        sub = Subscription(
            subscription_id=subscription_id,
            project_id=project_id,
            event_types=set(event_types),
            mission_id=mission_id,
            task_id=task_id,
            scopes=set(scopes or set()),
        )
        self._subs[subscription_id] = sub
        if listener is not None:
            self._listeners[subscription_id].append(listener)
        return sub

    def publish(self, event: EventEnvelope) -> list[str]:
        self._log.append(event)
        matched: list[str] = []
        for sub_id, sub in self._subs.items():
            if sub.project_id != event.project_id:
                continue
            if event.type not in sub.event_types and "*" not in sub.event_types:
                continue
            if sub.mission_id and sub.mission_id != event.mission_id:
                continue
            if sub.task_id and sub.task_id != event.task_id:
                continue
            matched.append(sub_id)
            for listener in self._listeners.get(sub_id, []):
                listener(event)
        return matched

    def history(
        self,
        *,
        project_id: str,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[EventEnvelope]:
        rows = [e for e in self._log if e.project_id == project_id]
        if event_type:
            rows = [e for e in rows if e.type == event_type]
        return rows[-limit:]

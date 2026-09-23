"""V2.3 transactional multi-resource reservation intents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from swarm.contracts.common import new_id, utc_now


class ReservationError(RuntimeError):
    pass


@dataclass
class ReservationComponent:
    kind: str  # provider|worker|tool|budget
    resource_id: str
    units: float = 1.0


@dataclass
class ReservationIntent:
    intent_id: str
    project_id: str
    mission_id: str
    attempt_id: str
    site_epoch: int
    components: list[ReservationComponent] = field(default_factory=list)
    state: str = "reserved"  # reserved|committed|released|failed
    created_at: str = field(default_factory=lambda: utc_now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "project_id": self.project_id,
            "mission_id": self.mission_id,
            "attempt_id": self.attempt_id,
            "site_epoch": self.site_epoch,
            "components": [
                {"kind": c.kind, "resource_id": c.resource_id, "units": c.units}
                for c in self.components
            ],
            "state": self.state,
            "created_at": self.created_at,
        }


class ReservationService:
    def __init__(self, *, current_epoch: int) -> None:
        self.current_epoch = current_epoch
        self._by_attempt: dict[str, ReservationIntent] = {}
        self._capacity: dict[tuple[str, str], float] = {}

    def set_capacity(self, kind: str, resource_id: str, units: float) -> None:
        self._capacity[(kind, resource_id)] = units

    def reserve(
        self,
        *,
        project_id: str,
        mission_id: str,
        attempt_id: str,
        site_epoch: int,
        components: list[ReservationComponent],
    ) -> ReservationIntent:
        if site_epoch != self.current_epoch:
            raise ReservationError(f"stale_epoch:{site_epoch}")
        if attempt_id in self._by_attempt:
            raise ReservationError(f"duplicate_attempt_reservation:{attempt_id}")
        # Fail closed if any component exceeds capacity.
        for component in components:
            key = (component.kind, component.resource_id)
            available = self._capacity.get(key)
            if available is None:
                raise ReservationError(f"unknown_resource:{key}")
            if component.units > available:
                raise ReservationError(f"insufficient_capacity:{key}")
        for component in components:
            key = (component.kind, component.resource_id)
            self._capacity[key] -= component.units
        intent = ReservationIntent(
            intent_id=new_id("rsv_"),
            project_id=project_id,
            mission_id=mission_id,
            attempt_id=attempt_id,
            site_epoch=site_epoch,
            components=list(components),
        )
        self._by_attempt[attempt_id] = intent
        return intent

    def release(self, attempt_id: str) -> ReservationIntent:
        intent = self._by_attempt.get(attempt_id)
        if intent is None:
            raise ReservationError("intent_missing")
        if intent.state == "released":
            return intent
        for component in intent.components:
            key = (component.kind, component.resource_id)
            self._capacity[key] = self._capacity.get(key, 0.0) + component.units
        intent.state = "released"
        return intent

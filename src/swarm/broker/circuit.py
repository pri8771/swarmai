"""Circuit breaker and health observations per route/provider."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from swarm.broker.errors import CircuitOpenError
from swarm.contracts.common import utc_now
from swarm.contracts.enums import ErrorClass

Clock = Callable[[], datetime]


@dataclass
class HealthObservation:
    successes: int = 0
    failures: int = 0
    auth_failures: int = 0
    overloads: int = 0
    unknown_outcomes: int = 0
    consecutive_failures: int = 0
    opened_at: datetime | None = None
    last_error_class: str | None = None
    pricing_fresh_at: datetime | None = None
    allowance_fresh_at: datetime | None = None


@dataclass
class CircuitConfig:
    failure_threshold: int = 3
    open_for: timedelta = field(default_factory=lambda: timedelta(seconds=30))
    half_open_probes: int = 1


class CircuitBreaker:
    def __init__(self, config: CircuitConfig | None = None, clock: Clock | None = None) -> None:
        self.config = config or CircuitConfig()
        self._clock: Clock = clock or utc_now
        self._health: dict[str, HealthObservation] = {}

    def _key(self, route_id: str) -> str:
        return route_id

    def health(self, route_id: str) -> HealthObservation:
        return self._health.setdefault(self._key(route_id), HealthObservation())

    def assert_closed(self, route_id: str) -> None:
        obs = self.health(route_id)
        if obs.opened_at is None:
            return
        now = self._clock()
        if now - obs.opened_at < self.config.open_for:
            raise CircuitOpenError(f"circuit_open:{route_id}")
        # Half-open: allow limited probes by clearing open stamp after window.
        obs.opened_at = None
        obs.consecutive_failures = 0

    def record_success(self, route_id: str) -> None:
        obs = self.health(route_id)
        obs.successes += 1
        obs.consecutive_failures = 0
        obs.opened_at = None
        obs.allowance_fresh_at = self._clock()

    def record_error(self, route_id: str, error_class: ErrorClass | str) -> None:
        obs = self.health(route_id)
        code = error_class.value if isinstance(error_class, ErrorClass) else error_class
        obs.last_error_class = code
        obs.failures += 1
        if code == ErrorClass.AUTHENTICATION.value:
            obs.auth_failures += 1
            # Auth failures open immediately but are not treated as overload.
            obs.opened_at = self._clock()
            obs.consecutive_failures += 1
            return
        if code == ErrorClass.RATE_LIMIT.value:
            obs.overloads += 1
        if code == ErrorClass.UNKNOWN_OUTCOME.value:
            obs.unknown_outcomes += 1
        obs.consecutive_failures += 1
        if obs.consecutive_failures >= self.config.failure_threshold:
            obs.opened_at = self._clock()

    def mark_pricing_fresh(self, route_id: str) -> None:
        self.health(route_id).pricing_fresh_at = self._clock()

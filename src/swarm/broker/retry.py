"""Single retry owner — bounded backoff, Retry-After, safe route changes."""

from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from swarm.contracts.common import utc_now
from swarm.contracts.enums import ErrorClass

Clock = Callable[[], datetime]

RETRY_AFTER_EXCEEDS_CAP = "retry_after_exceeds_cap"


@dataclass
class RetryDecision:
    should_retry: bool
    wait_seconds: float
    reason: str
    allow_route_change: bool = False


@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay_seconds: float = 0.05
    max_delay_seconds: float = 2.0
    jitter_ratio: float = 0.25
    max_retry_after_seconds: float = 30.0


class RetryOwner:
    """Only this owner may schedule retries for brokered calls."""

    def __init__(self, config: RetryConfig | None = None, clock: Clock | None = None) -> None:
        self.config = config or RetryConfig()
        self._clock: Clock = clock or utc_now
        self._attempt_counts: dict[str, int] = {}

    def note_attempt(self, logical_call_id: str) -> int:
        n = self._attempt_counts.get(logical_call_id, 0) + 1
        self._attempt_counts[logical_call_id] = n
        return n

    def attempts(self, logical_call_id: str) -> int:
        return self._attempt_counts.get(logical_call_id, 0)

    def decide(
        self,
        logical_call_id: str,
        error_class: ErrorClass | str,
        *,
        retry_after: float | None = None,
        post_send: bool = False,
    ) -> RetryDecision:
        code = error_class.value if isinstance(error_class, ErrorClass) else error_class
        attempt = self._attempt_counts.get(logical_call_id, 1)

        if post_send and code == ErrorClass.UNKNOWN_OUTCOME.value:
            return RetryDecision(
                False, 0.0, "retain_ambiguous_send", allow_route_change=False
            )
        if code == ErrorClass.AUTHENTICATION.value:
            return RetryDecision(False, 0.0, "auth_failure_no_retry")
        if code == ErrorClass.POLICY_DENIED.value:
            return RetryDecision(False, 0.0, "policy_denied")
        if code == ErrorClass.QUOTA_EXHAUSTED.value:
            return RetryDecision(
                False, 0.0, "quota_exhausted", allow_route_change=True
            )
        if attempt >= self.config.max_attempts:
            return RetryDecision(False, 0.0, "max_attempts")

        if retry_after is not None:
            wait = float(retry_after)
            # Never retry before the upstream Retry-After has elapsed: a value
            # above the cap (or not a number) is a give-up, not a clamped retry.
            if not math.isfinite(wait) or wait > self.config.max_retry_after_seconds:
                return RetryDecision(False, 0.0, RETRY_AFTER_EXCEEDS_CAP)
            wait = max(wait, 0.0)
        else:
            exp = self.config.base_delay_seconds * (2 ** max(0, attempt - 1))
            wait = min(self.config.max_delay_seconds, exp)
            jitter = wait * self.config.jitter_ratio * random.random()
            wait = wait + jitter

        allow_change = code in {
            ErrorClass.RATE_LIMIT.value,
            ErrorClass.TRANSIENT.value,
            ErrorClass.UNSUPPORTED_CAPABILITY.value,
        }
        return RetryDecision(True, wait, f"retry:{code}", allow_route_change=allow_change)

    def wake_at(self, wait_seconds: float) -> datetime:
        return self._clock() + timedelta(seconds=wait_seconds)

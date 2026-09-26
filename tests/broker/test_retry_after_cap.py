"""SW-W0-S3 / F-06: upstream Retry-After is bounded."""

from __future__ import annotations

import math

import pytest

from swarm.broker.retry import RetryConfig, RetryOwner
from swarm.contracts.enums import ErrorClass


@pytest.mark.parametrize(
    ("retry_after", "expected"),
    [
        (5.0, 5.0),
        (86_400.0, 30.0),
        (-10.0, 0.0),
        (math.inf, 30.0),
        (math.nan, 30.0),
    ],
)
def test_retry_after_is_clamped(retry_after: float, expected: float) -> None:
    owner = RetryOwner()
    owner.note_attempt("call_1")
    decision = owner.decide("call_1", ErrorClass.RATE_LIMIT, retry_after=retry_after)
    assert decision.should_retry is True
    assert decision.wait_seconds == expected


def test_cap_is_configurable() -> None:
    owner = RetryOwner(RetryConfig(max_retry_after_seconds=2.5))
    owner.note_attempt("call_2")
    decision = owner.decide("call_2", ErrorClass.TRANSIENT, retry_after=100.0)
    assert decision.wait_seconds == 2.5


def test_attempt_bound_still_applies() -> None:
    owner = RetryOwner()
    for _ in range(3):
        owner.note_attempt("call_3")
    decision = owner.decide("call_3", ErrorClass.RATE_LIMIT, retry_after=1.0)
    assert decision.should_retry is False
    assert decision.reason == "max_attempts"

"""SW-W0-S3 / F-06 + SW-FIX-RETRY: upstream Retry-After is bounded.

A Retry-After above ``max_retry_after_seconds`` is a terminal give-up: the owner
must never schedule a retry before the upstream Retry-After has elapsed.
"""

from __future__ import annotations

import math

import pytest

from swarm.broker.retry import RETRY_AFTER_EXCEEDS_CAP, RetryConfig, RetryOwner
from swarm.contracts.enums import ErrorClass


@pytest.mark.parametrize(
    ("retry_after", "expected"),
    [
        (5.0, 5.0),
        (30.0, 30.0),
        (0.0, 0.0),
        (-10.0, 0.0),
    ],
)
def test_retry_after_within_cap_is_honored(retry_after: float, expected: float) -> None:
    owner = RetryOwner()
    owner.note_attempt("call_1")
    decision = owner.decide("call_1", ErrorClass.RATE_LIMIT, retry_after=retry_after)
    assert decision.should_retry is True
    assert decision.wait_seconds == expected
    assert decision.reason == "retry:rate_limit"


@pytest.mark.parametrize("retry_after", [30.001, 31.0, 86_400.0, math.inf, math.nan])
@pytest.mark.parametrize("error_class", [ErrorClass.RATE_LIMIT, ErrorClass.TRANSIENT])
def test_retry_after_above_cap_gives_up(retry_after: float, error_class: ErrorClass) -> None:
    owner = RetryOwner()
    owner.note_attempt("call_x")
    decision = owner.decide("call_x", error_class, retry_after=retry_after)
    assert decision.should_retry is False
    assert decision.reason == RETRY_AFTER_EXCEEDS_CAP == "retry_after_exceeds_cap"
    assert decision.wait_seconds == 0.0
    assert decision.allow_route_change is False


def test_give_up_is_terminal_on_repeat() -> None:
    owner = RetryOwner()
    owner.note_attempt("call_r")
    first = owner.decide("call_r", ErrorClass.RATE_LIMIT, retry_after=120.0)
    second = owner.decide("call_r", ErrorClass.RATE_LIMIT, retry_after=120.0)
    assert (first.should_retry, second.should_retry) == (False, False)
    assert first.reason == second.reason == RETRY_AFTER_EXCEEDS_CAP


def test_cap_is_configurable() -> None:
    owner = RetryOwner(RetryConfig(max_retry_after_seconds=2.5))
    owner.note_attempt("call_2")
    at_cap = owner.decide("call_2", ErrorClass.TRANSIENT, retry_after=2.5)
    assert at_cap.should_retry is True
    assert at_cap.wait_seconds == 2.5
    over = owner.decide("call_2", ErrorClass.TRANSIENT, retry_after=100.0)
    assert over.should_retry is False
    assert over.reason == RETRY_AFTER_EXCEEDS_CAP


def test_attempt_bound_still_applies() -> None:
    owner = RetryOwner()
    for _ in range(3):
        owner.note_attempt("call_3")
    decision = owner.decide("call_3", ErrorClass.RATE_LIMIT, retry_after=1.0)
    assert decision.should_retry is False
    assert decision.reason == "max_attempts"


def test_non_retryable_classes_keep_their_reason() -> None:
    owner = RetryOwner()
    owner.note_attempt("call_4")
    decision = owner.decide("call_4", ErrorClass.AUTHENTICATION, retry_after=500.0)
    assert decision.reason == "auth_failure_no_retry"


def test_no_retry_after_uses_bounded_backoff() -> None:
    owner = RetryOwner()
    owner.note_attempt("call_5")
    decision = owner.decide("call_5", ErrorClass.TRANSIENT)
    assert decision.should_retry is True
    assert 0.0 < decision.wait_seconds <= owner.config.max_delay_seconds * (
        1 + owner.config.jitter_ratio
    )

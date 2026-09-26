"""SW-W1-S4: scheduler epoch fencing and singleton ticker (in-memory)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from swarm.scheduling.epoch import (
    EpochHeldError,
    InMemorySchedulerEpochService,
    StaleSchedulerEpochError,
)
from swarm.scheduling.singleton import SingletonTicker


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now = self.now + timedelta(seconds=seconds)


def test_second_holder_blocked_until_expiry_then_epoch_increments() -> None:
    clock = Clock()
    svc = InMemorySchedulerEpochService(ttl_seconds=15, clock=clock)
    a = svc.acquire("sched_a")
    assert a.epoch == 1
    assert svc.acquire("sched_a").epoch == 1
    with pytest.raises(EpochHeldError):
        svc.acquire("sched_b")
    clock.advance(16)
    b = svc.acquire("sched_b")
    assert b.epoch == 2
    with pytest.raises(StaleSchedulerEpochError):
        svc.require_current(epoch=1, holder_id="sched_a")
    with pytest.raises(StaleSchedulerEpochError):
        svc.renew(a)


def test_renew_extends_and_release_allows_takeover() -> None:
    clock = Clock()
    svc = InMemorySchedulerEpochService(ttl_seconds=15, clock=clock)
    a = svc.acquire("sched_a")
    clock.advance(10)
    svc.renew(a)
    clock.advance(10)
    svc.require_current(epoch=1, holder_id="sched_a")
    svc.release(a)
    assert svc.current() is None
    assert svc.acquire("sched_b").epoch == 2


def test_singleton_ticker_runs_in_one_holder_only() -> None:
    clock = Clock()
    svc = InMemorySchedulerEpochService(ttl_seconds=15, clock=clock)
    calls: list[str] = []
    t1 = SingletonTicker(svc, holder_id="proc_1")
    t2 = SingletonTicker(svc, holder_id="proc_2")
    r1 = t1.run_once(lambda lease: calls.append(f"p1:{lease.epoch}"))
    r2 = t2.run_once(lambda lease: calls.append(f"p2:{lease.epoch}"))
    assert (r1.ran, r1.reason) == (True, "ok")
    assert (r2.ran, r2.reason) == (False, "epoch_held_by_other")
    assert calls == ["p1:1"]


def test_ticker_reports_fencing_during_tick() -> None:
    clock = Clock()
    svc = InMemorySchedulerEpochService(ttl_seconds=15, clock=clock)
    ticker = SingletonTicker(svc, holder_id="proc_1")

    def slow_tick(lease: object) -> str:
        clock.advance(20)
        svc.acquire("proc_2")
        return "work"

    result = ticker.run_once(slow_tick)
    assert result.ran is True
    assert result.reason == "fenced_after_tick"

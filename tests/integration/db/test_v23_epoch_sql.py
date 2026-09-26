"""SW-W1-S4: SqlSchedulerEpochService fencing across two service instances (PostgreSQL)."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import Base
from swarm.scheduling.epoch import (
    EpochHeldError,
    SqlSchedulerEpochService,
    StaleSchedulerEpochError,
)

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture()
def factory():
    eng = create_db_engine(DATABASE_URL)
    try:
        ping(eng)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"postgres_unavailable:{type(exc).__name__}")
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        conn.execute(text("TRUNCATE v23_scheduler_epochs"))
    yield make_session_factory(eng)
    eng.dispose()


def test_two_processes_share_one_epoch_row(factory) -> None:
    clock = Clock()
    proc_a = SqlSchedulerEpochService(factory, ttl_seconds=15, clock=clock)
    proc_b = SqlSchedulerEpochService(factory, ttl_seconds=15, clock=clock)
    lease_a = proc_a.acquire("sched_a")
    assert lease_a.epoch == 1
    with pytest.raises(EpochHeldError):
        proc_b.acquire("sched_b")
    clock.now = clock.now + timedelta(seconds=16)
    lease_b = proc_b.acquire("sched_b")
    assert lease_b.epoch == 2
    with pytest.raises(StaleSchedulerEpochError):
        proc_a.require_current(epoch=1, holder_id="sched_a")
    with pytest.raises(StaleSchedulerEpochError):
        proc_a.renew(lease_a)
    proc_b.require_current(epoch=2, holder_id="sched_b")
    current = proc_a.current()
    assert current is not None and current.holder_id == "sched_b"

"""SW-W2-S1: scheduler fairness state survives a process restart on PostgreSQL."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

from swarm.contracts.v23 import SchedulableTask, SchedulerDecision
from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import Base
from swarm.scheduling.epoch import SqlSchedulerEpochService
from swarm.scheduling.service import SchedulerService
from swarm.scheduling.store import SqlSchedulingStore

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)
TABLES = (
    "v23_project_queue_state",
    "v23_mission_queue_state",
    "v23_scheduler_receipts",
    "v23_dispatch_intents",
    "v23_scheduler_epochs",
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
        conn.execute(text("TRUNCATE " + ", ".join(TABLES)))
    yield make_session_factory(eng)
    eng.dispose()


def _svc(factory, clock: Clock, holder: str, released: list[str]) -> SchedulerService:
    return SchedulerService(
        SqlSchedulingStore(factory),
        epochs=SqlSchedulerEpochService(factory, ttl_seconds=15, clock=clock),
        holder_id=holder,
        reserve=lambda intent, comp: f"r_{intent.attempt_id}_{comp.kind}",
        release=lambda intent, comp: released.append(intent.attempt_id),
        clock=clock,
    )


def _task(project: str, n: int) -> SchedulableTask:
    return SchedulableTask(
        task_id=f"{project}_t{n}",
        mission_id=f"{project}_m",
        project_id=project,
        attempt_id=f"att_{project}_{n}",
    )


def test_restart_preserves_credit_and_recovers_intents(factory) -> None:
    clock = Clock()
    released: list[str] = []
    first = _svc(factory, clock, "proc_a", released)
    for p, w in (("a", 3.0), ("b", 1.0)):
        first.register_project(p, weight=w)
        first.register_mission(f"{p}_m", p)
    for n in range(20):
        out = first.schedule_once([_task("a", n), _task("b", n)])
        assert out.intent is not None
        first.mark_dispatched(out.intent.intent_id)
        first.finish(out.intent.intent_id)
    crashed = first.schedule_once([_task("a", 99), _task("b", 99)])
    assert crashed.decision == SchedulerDecision.ADMIT and crashed.intent is not None
    credits = {q["project_id"]: q["credit"] for q in first.queues()}

    clock.now = clock.now + timedelta(seconds=60)
    second = _svc(factory, clock, "proc_b", released)
    report = second.recover()
    assert report["expired_intents"] == [crashed.intent.intent_id]
    assert crashed.intent.attempt_id in released
    after = {q["project_id"]: q for q in second.queues()}
    for p in ("a", "b"):
        assert after[p]["credit"] == pytest.approx(min(credits[p], 10.0 * (3.0 if p == "a" else 1.0)))
        assert after[p]["running"] == 0
    nxt = second.schedule_once([_task("a", 100), _task("b", 100)])
    assert nxt.decision == SchedulerDecision.ADMIT
    assert nxt.receipt is not None and nxt.receipt.scheduler_epoch == 2
    receipts = SqlSchedulingStore(factory).list_receipts(limit=1000)
    assert [r.sequence for r in receipts] == sorted(r.sequence for r in receipts)

"""SW-W1-S2: SqlSchedulingStore matches InMemorySchedulingStore semantics (PostgreSQL)."""

from __future__ import annotations

import os
import threading
from datetime import timedelta

import pytest
from sqlalchemy import text

from swarm.contracts.common import utc_now
from swarm.contracts.v23 import (
    DispatchIntent,
    DispatchIntentState,
    MissionQueueState,
    ProjectQueueState,
    ReasonCode,
    SchedulerDecision,
    SchedulingDecisionReceipt,
    StaleVersionError,
)
from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import Base
from swarm.scheduling.memory_store import InMemorySchedulingStore
from swarm.scheduling.store import SqlSchedulingStore

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)
V23_TABLES = (
    "v23_project_queue_state",
    "v23_mission_queue_state",
    "v23_scheduler_receipts",
    "v23_dispatch_intents",
)


@pytest.fixture(scope="module")
def factory():
    eng = create_db_engine(DATABASE_URL)
    try:
        ping(eng)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"postgres_unavailable:{type(exc).__name__}")
    Base.metadata.create_all(eng)
    yield make_session_factory(eng)
    eng.dispose()


@pytest.fixture(autouse=True)
def _clean(factory):
    with factory() as s:
        s.execute(text("TRUNCATE " + ", ".join(V23_TABLES)))
        s.commit()
    yield


@pytest.fixture(params=["memory", "sql"])
def store(request, factory):
    if request.param == "memory":
        return InMemorySchedulingStore()
    return SqlSchedulingStore(factory)


def test_project_versioning(store) -> None:
    first = store.put_project(ProjectQueueState(project_id="proj_a"), expected_version=None)
    assert first.version == 1
    with pytest.raises(StaleVersionError):
        store.put_project(ProjectQueueState(project_id="proj_a"), expected_version=None)
    second = store.put_project(first.model_copy(update={"credit": 4.0}), expected_version=1)
    assert second.version == 2
    with pytest.raises(StaleVersionError):
        store.put_project(first, expected_version=1)
    got = store.get_project("proj_a")
    assert got is not None and got.credit == 4.0 and got.version == 2


def test_missions_filtered_by_project(store) -> None:
    store.put_mission(MissionQueueState(mission_id="m1", project_id="p1"), expected_version=None)
    store.put_mission(MissionQueueState(mission_id="m2", project_id="p2"), expected_version=None)
    assert [m.mission_id for m in store.list_missions("p2")] == ["m2"]


def test_receipts_roundtrip_and_digest(store) -> None:
    seq = store.next_sequence()
    receipt = SchedulingDecisionReceipt(
        sequence=seq,
        decision=SchedulerDecision.ADMIT,
        reason_code=ReasonCode.ADMITTED,
        project_id="proj_a",
        scores={"proj_a": 1.5},
    )
    store.append_receipt(receipt)
    with pytest.raises(StaleVersionError):
        store.append_receipt(receipt.model_copy(update={"receipt_id": "sdr_dup"}))
    [back] = store.list_receipts(project_id="proj_a")
    assert back.digest() == receipt.digest()


def test_intent_unique_per_attempt(store) -> None:
    intent = DispatchIntent(
        attempt_id="att_1",
        project_id="proj_a",
        mission_id="m1",
        task_id="t1",
        expires_at=utc_now() + timedelta(seconds=30),
    )
    stored = store.put_intent(intent, expected_version=None)
    with pytest.raises(StaleVersionError):
        store.put_intent(intent.model_copy(update={"intent_id": "din_2"}), expected_version=None)
    moved = store.put_intent(
        stored.model_copy(update={"state": DispatchIntentState.RESERVED}), expected_version=1
    )
    assert moved.version == 2
    assert store.get_intent_by_attempt("att_1") == moved
    assert [i.intent_id for i in store.list_intents(states=frozenset({DispatchIntentState.RESERVED}))] == [
        intent.intent_id
    ]


def test_concurrent_update_has_one_winner(factory) -> None:
    store = SqlSchedulingStore(factory)
    base = store.put_project(ProjectQueueState(project_id="proj_race"), expected_version=None)
    results: list[str] = []

    def writer(credit: float) -> None:
        try:
            store.put_project(base.model_copy(update={"credit": credit}), expected_version=1)
            results.append("ok")
        except StaleVersionError:
            results.append("stale")

    threads = [threading.Thread(target=writer, args=(float(i),)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == ["ok", "stale", "stale", "stale"]

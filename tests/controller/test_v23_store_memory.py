"""SW-W0-S2: InMemorySchedulingStore versioning semantics (the SQL store must match)."""

from __future__ import annotations

from datetime import timedelta

import pytest

from swarm.contracts.common import utc_now
from swarm.contracts.v23 import (
    DispatchIntent,
    DispatchIntentState,
    ProjectQueueState,
    ReasonCode,
    SchedulerDecision,
    SchedulingDecisionReceipt,
    StaleVersionError,
)
from swarm.scheduling.memory_store import InMemorySchedulingStore


def test_project_insert_update_and_stale_version() -> None:
    store = InMemorySchedulingStore()
    stored = store.put_project(ProjectQueueState(project_id="proj_a"), expected_version=None)
    assert stored.version == 1
    with pytest.raises(StaleVersionError):
        store.put_project(ProjectQueueState(project_id="proj_a"), expected_version=None)
    updated = store.put_project(stored.model_copy(update={"credit": 2.0}), expected_version=1)
    assert updated.version == 2
    with pytest.raises(StaleVersionError):
        store.put_project(stored.model_copy(update={"credit": 3.0}), expected_version=1)
    got = store.get_project("proj_a")
    assert got is not None and got.credit == 2.0


def test_receipts_sequence_unique_and_filtered() -> None:
    store = InMemorySchedulingStore()
    s1 = store.next_sequence()
    s2 = store.next_sequence()
    assert (s1, s2) == (1, 2)
    base = {"decision": SchedulerDecision.ADMIT, "reason_code": ReasonCode.ADMITTED}
    store.append_receipt(SchedulingDecisionReceipt(sequence=s1, project_id="proj_a", **base))
    store.append_receipt(SchedulingDecisionReceipt(sequence=s2, project_id="proj_b", **base))
    with pytest.raises(StaleVersionError):
        store.append_receipt(SchedulingDecisionReceipt(sequence=s1, **base))
    assert [r.project_id for r in store.list_receipts(project_id="proj_b")] == ["proj_b"]


def test_one_intent_per_attempt() -> None:
    store = InMemorySchedulingStore()
    intent = DispatchIntent(
        attempt_id="att_1",
        project_id="proj_a",
        mission_id="msn_1",
        task_id="tsk_1",
        expires_at=utc_now() + timedelta(seconds=30),
    )
    stored = store.put_intent(intent, expected_version=None)
    assert store.get_intent_by_attempt("att_1") == stored
    dup = intent.model_copy(update={"intent_id": "din_other"})
    with pytest.raises(StaleVersionError):
        store.put_intent(dup, expected_version=None)
    done = store.put_intent(
        stored.model_copy(update={"state": DispatchIntentState.COMPLETED}), expected_version=1
    )
    assert done.version == 2
    assert store.list_intents(states=frozenset({DispatchIntentState.PREPARED})) == []

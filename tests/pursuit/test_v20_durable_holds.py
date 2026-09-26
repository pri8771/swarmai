"""SW-W1-S10 / V20-E04: holds and lessons survive restart; persistence is DB-first."""

from __future__ import annotations

import pytest

from swarm.pursuit import AccountingError, GoalResourceLedger
from swarm.pursuit.accounting import ResourceHold
from swarm.pursuit.durable_accounting import (
    InMemoryHoldStore,
    InMemoryLessonPersistence,
    bind_durable_ledger,
)
from swarm.pursuit.learning import PursuitLessonStore
from swarm.pursuit.models import LessonState, PursuitLesson

ENV = {"spend_usd_ceiling": 1.0, "allow_paid": True, "max_model_calls": 5}


def _ledger(store: InMemoryHoldStore) -> GoalResourceLedger:
    return bind_durable_ledger(GoalResourceLedger.from_envelope("goal_d", ENV), store)


def test_holds_survive_restart_including_unknown() -> None:
    store = InMemoryHoldStore()
    first = _ledger(store)
    a = first.reserve(mission_id="msn_a", spend_usd=0.3, model_calls=1)
    b = first.reserve(mission_id="msn_b", spend_usd=0.2, model_calls=1)
    first.settle(a.hold_id, spend_usd=0.1, model_calls=1)
    first.settle(b.hold_id, spend_usd=0.0, usage_unknown=True)

    cold = _ledger(store)
    assert {h.hold_id: h.state for h in cold.holds.values()} == {
        a.hold_id: "settled",
        b.hold_id: "unknown",
    }
    assert cold.remaining().spend_usd == pytest.approx(first.remaining().spend_usd)
    with pytest.raises(AccountingError, match="double_settle"):
        cold.settle(a.hold_id, spend_usd=0.1)
    with pytest.raises(AccountingError, match="unknown_hold_requires_reconciliation"):
        cold.release(b.hold_id)


class _FailingStore(InMemoryHoldStore):
    def __init__(self) -> None:
        super().__init__()
        self.fail = False

    def put(self, hold: ResourceHold) -> None:
        if self.fail:
            raise RuntimeError("db_down")
        super().put(hold)


def test_persist_failure_leaves_memory_unchanged() -> None:
    store = _FailingStore()
    ledger = _ledger(store)
    hold = ledger.reserve(mission_id="msn_a", spend_usd=0.3)
    store.fail = True
    with pytest.raises(RuntimeError, match="db_down"):
        ledger.reserve(mission_id="msn_b", spend_usd=0.1)
    assert len(ledger.holds) == 1
    with pytest.raises(RuntimeError, match="db_down"):
        ledger.settle(hold.hold_id, spend_usd=0.2)
    assert ledger.holds[hold.hold_id].state == "held"


def test_lessons_survive_restart() -> None:
    persist = InMemoryLessonPersistence()
    store = PursuitLessonStore(persist)
    lesson = store.propose(PursuitLesson(goal_id="goal_l", summary="s", strategy_delta="d"))
    store.evaluate(lesson.lesson_id, holdout_check_id="hold:1", holdout_passed=True)
    store.adopt(lesson.lesson_id, current_strategy="base")

    cold = PursuitLessonStore(persist)
    assert cold.get(lesson.lesson_id).state == LessonState.ADOPTED
    assert cold.applied_strategy("goal_l", "base") == "base | d"
    cold.rollback(lesson.lesson_id)
    assert PursuitLessonStore(persist).get(lesson.lesson_id).state == LessonState.ROLLED_BACK


def test_store_without_persistence_is_unchanged() -> None:
    store = PursuitLessonStore()
    lesson = store.propose(PursuitLesson(goal_id="g", summary="s"))
    assert store.list_for_goal("g") == [lesson]

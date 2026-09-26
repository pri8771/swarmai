"""SW-W1-S10 / V20-E04: usage holds and lessons persisted in PostgreSQL."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text

from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import Base
from swarm.pursuit import GoalResourceLedger
from swarm.pursuit.durable_accounting import (
    SqlHoldStore,
    SqlLessonPersistence,
    bind_durable_ledger,
)
from swarm.pursuit.learning import PursuitLessonStore
from swarm.pursuit.models import LessonState, PursuitLesson

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)


@pytest.fixture(scope="module")
def factory():
    eng = create_db_engine(DATABASE_URL)
    try:
        ping(eng)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"postgres_unavailable:{type(exc).__name__}")
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        conn.execute(text("TRUNCATE v20_goal_usage_holds, v20_pursuit_lessons"))
    yield make_session_factory(eng)
    eng.dispose()


def test_holds_restore_from_postgres(factory) -> None:
    env = {"spend_usd_ceiling": 1.0, "allow_paid": True}
    first = bind_durable_ledger(GoalResourceLedger.from_envelope("goal_sql", env), SqlHoldStore(factory))
    hold = first.reserve(mission_id="msn_1", spend_usd=0.4)
    first.settle(hold.hold_id, spend_usd=0.0, usage_unknown=True)

    cold = bind_durable_ledger(GoalResourceLedger.from_envelope("goal_sql", env), SqlHoldStore(factory))
    assert cold.holds[hold.hold_id].state == "unknown"
    assert cold.remaining().spend_usd == pytest.approx(0.6)
    with factory() as s:
        version = s.execute(
            text("SELECT version FROM v20_goal_usage_holds WHERE hold_id = :h"), {"h": hold.hold_id}
        ).scalar_one()
    assert version == 2


def test_lessons_restore_from_postgres(factory) -> None:
    store = PursuitLessonStore(SqlLessonPersistence(factory))
    lesson = store.propose(PursuitLesson(goal_id="goal_sql", summary="s"))
    store.evaluate(lesson.lesson_id, holdout_check_id="hold:1", holdout_passed=False)
    cold = PursuitLessonStore(SqlLessonPersistence(factory))
    assert cold.get(lesson.lesson_id).state == LessonState.REJECTED

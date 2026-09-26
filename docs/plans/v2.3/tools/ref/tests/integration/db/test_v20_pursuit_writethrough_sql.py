"""SW-W1-S9 / V20-E03: pursuit snapshot write-through to PostgreSQL survives volume loss."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import text

from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import Base
from swarm.goals.models import Goal, GoalStore
from swarm.pursuit import PursuitEngine, PursuitScheduler, RecordingExecutor
from swarm.pursuit.pg_mirror import PursuitPgMirror
from swarm.pursuit.state_store import DurablePursuitStateStore

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
    yield make_session_factory(eng)
    eng.dispose()


def test_pursuit_state_restored_from_postgres(factory, tmp_path: Path) -> None:
    with factory() as s:
        s.execute(text("TRUNCATE pursuit_cycles, pursuit_schedules, pursuit_dedupe"))
        s.commit()
    goals = GoalStore(tmp_path / "goals")
    goal = goals.create(
        Goal(
            project_id="proj_wt_sql",
            desired_outcome="write through sql",
            verification_criteria=["one", "two"],
            resource_envelope={"spend_usd_ceiling": 0.0},
            authority_envelope={"tools": ["workspace.read"], "providers": ["fake"]},
        )
    )

    def engine(volume: str) -> PursuitEngine:
        return PursuitEngine(
            goals,
            executor=RecordingExecutor(default_success=True),
            scheduler=PursuitScheduler(clock=lambda: 10.0),
            state_store=DurablePursuitStateStore(
                tmp_path / volume, mirror=PursuitPgMirror(factory)
            ),
        )

    first = engine("vol_a")
    first.tick(goal.id, force=True)
    first.tick(goal.id, force=True)
    history = [c.cycle_id for c in first.history(goal.id)]

    cold = engine("vol_b_empty")
    assert [c.cycle_id for c in cold.history(goal.id)] == history
    assert cold.satisfied_criteria(goal.id) == first.satisfied_criteria(goal.id)
    with factory() as s:
        n_cycles = s.execute(
            text("SELECT count(*) FROM pursuit_cycles WHERE goal_id = :g"), {"g": goal.id}
        ).scalar_one()
    assert n_cycles == len(history)

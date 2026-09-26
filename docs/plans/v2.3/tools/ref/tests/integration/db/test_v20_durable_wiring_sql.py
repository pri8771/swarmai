"""SW-W3-S2: with SWARM_V23_DURABLE=1 ProductStore persists pursuit state in PostgreSQL."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import text

from swarm.api.store import ProductStore
from swarm.db.engine import create_db_engine, ping
from swarm.db.models import Base
from swarm.goals.models import Goal
from swarm.pursuit.pg_mirror import PursuitPgMirror

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)
TABLES = (
    "pursuit_cycles",
    "pursuit_schedules",
    "pursuit_dedupe",
    "v20_goal_usage_holds",
    "v20_pursuit_lessons",
    "v23_scheduler_epochs",
)


@pytest.fixture()
def durable_env(monkeypatch: pytest.MonkeyPatch):
    eng = create_db_engine(DATABASE_URL)
    try:
        ping(eng)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"postgres_unavailable:{type(exc).__name__}")
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        conn.execute(text("TRUNCATE " + ", ".join(TABLES)))
    monkeypatch.setenv("SWARM_DATABASE_URL", DATABASE_URL)
    monkeypatch.setenv("SWARM_V23_DURABLE", "1")
    yield
    eng.dispose()


def _store(root: Path) -> ProductStore:
    store = ProductStore(repo_root=root, db_reachable=True)
    store.fixture_mode = True
    return store


def test_holds_restore_and_ticker_is_singleton(durable_env, tmp_path: Path) -> None:
    first = _store(tmp_path)
    goal = first.goal_store().create(
        Goal(
            project_id="proj_pg",
            desired_outcome="durable wiring",
            verification_criteria=["done"],
            resource_envelope={"spend_usd_ceiling": 1.0, "allow_paid": True},
            authority_envelope={"tools": ["workspace.read"], "providers": ["fake"]},
        )
    )
    engine = first.pursuit_engine()
    assert isinstance(engine.state_store.mirror, PursuitPgMirror)
    hold = engine.resource_ledger(goal.id).reserve(mission_id="msn_pg", spend_usd=0.25)

    second = _store(tmp_path)
    assert hold.hold_id in second.pursuit_engine().resource_ledger(goal.id).holds

    ran = first.run_pursuit_tick()
    blocked = second.run_pursuit_tick()
    assert ran.ran and ran.reason == "ok"
    assert not blocked.ran and blocked.reason == "epoch_held_by_other"

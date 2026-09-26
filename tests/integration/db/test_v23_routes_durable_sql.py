"""SW-W3-S1: with SWARM_V23_DURABLE=1 scheduler, pack and ops state survive an app restart."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from swarm.api.app import create_app
from swarm.db.engine import create_db_engine, ping
from swarm.db.models import Base

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
    "v23_pack_installs",
    "v23_ops_events",
)
DEMO = {"Authorization": "Bearer atk_policy_demo"}


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


def _app(root: Path):
    return create_app(require_auth=True, db_reachable=True, seed_fixtures=True, repo_root=root)


def test_scheduler_and_ops_state_survive_restart(durable_env, tmp_path: Path) -> None:
    first = _app(tmp_path)
    assert first.state.v23.durable is True
    with TestClient(first) as c:
        c.post("/v1/scheduler/projects/proj_demo", json={}, headers=DEMO)
        c.post("/v1/scheduler/projects/proj_demo/weight", json={"weight": 2.5}, headers=DEMO)
    second = _app(tmp_path)
    with TestClient(second) as c:
        rows = c.get("/v1/scheduler/queues", headers=DEMO).json()["projects"]
        events = c.get("/v1/ops/events", params={"project_id": "proj_demo"}, headers=DEMO)
    assert [(r["project_id"], r["weight"]) for r in rows] == [("proj_demo", 2.5)]
    actions = [e["detail"]["action"] for e in events.json()["events"]]
    assert actions == ["scheduler.register", "scheduler.weight"]

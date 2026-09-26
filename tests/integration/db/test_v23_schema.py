"""SW-W0-S2: migration a23opsplatform0001 round-trip (PostgreSQL)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from swarm.db.engine import create_db_engine, ping
from swarm.db.models import Base

pytestmark = pytest.mark.integration

REPO = Path(__file__).resolve().parents[3]
DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)
V23_TABLES = {
    "v23_project_queue_state",
    "v23_mission_queue_state",
    "v23_scheduler_receipts",
    "v23_dispatch_intents",
    "v23_scheduler_epochs",
    "v23_pack_installs",
    "v23_ops_events",
    "v20_goal_usage_holds",
    "v20_pursuit_lessons",
}


def _alembic_config(url: str) -> Config:
    cfg = Config(str(REPO / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


@pytest.fixture(scope="module")
def engine():
    eng = create_db_engine(DATABASE_URL)
    try:
        ping(eng)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"postgres_unavailable:{type(exc).__name__}")
    Base.metadata.drop_all(eng)
    with eng.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
    yield eng
    Base.metadata.drop_all(eng)
    with eng.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
    eng.dispose()


def test_upgrade_downgrade_upgrade(engine) -> None:
    cfg = _alembic_config(DATABASE_URL)
    command.upgrade(cfg, "head")
    names = set(inspect(engine).get_table_names())
    assert V23_TABLES <= names
    command.downgrade(cfg, "a20pursuitpersist0001")
    names = set(inspect(engine).get_table_names())
    assert not (V23_TABLES & names)
    command.upgrade(cfg, "head")
    names = set(inspect(engine).get_table_names())
    assert V23_TABLES <= names
    with engine.begin() as conn:
        head = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert head == "a23opsplatform0001"

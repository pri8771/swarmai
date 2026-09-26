"""SW-W4-S1 / F-14, F-16: candidate schema revision tracks the Alembic head; freeze is admin-only."""

from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient

from swarm.api.app import create_app
from swarm.release.candidate import CURRENT_SCHEMA_REVISION

ROOT = Path(__file__).resolve().parents[2]


def test_constant_matches_single_alembic_head() -> None:
    script = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))
    assert script.get_heads() == [CURRENT_SCHEMA_REVISION]


def test_no_hardcoded_schema_literals_remain() -> None:
    for rel in ("src/swarm/cli.py", "src/swarm/api/routes_v1.py"):
        assert "a18tov30schema0001" not in (ROOT / rel).read_text(encoding="utf-8"), rel


def test_candidate_freeze_requires_admin() -> None:
    app = create_app(require_auth=True, db_reachable=False, seed_fixtures=True)
    with TestClient(app) as client:
        res = client.post(
            "/v1/release/candidate-freeze", headers={"Authorization": "Bearer atk_policy_demo"}
        )
    assert res.status_code == 403
    assert res.json()["code"] == "forbidden_admin"

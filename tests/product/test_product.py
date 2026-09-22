"""V0.8 product experience tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from swarm.api.app import create_app
from swarm.db.engine import create_db_engine
from swarm.db.models import Base
from swarm.product.contracts import public_product_contract, strip_internal
from swarm.product.history import HistoryIndex
from swarm.product.journey import run_product_journey
from swarm.product.projects import ProjectStore, scrub_config


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "sandbox" / "selfdev_issue").mkdir(parents=True)
    (tmp_path / "sandbox" / "selfdev_issue" / "parser_helper.py").write_text(
        "def add(a, b):\n    return a + b\n", encoding="utf-8"
    )
    (tmp_path / "pyproject.toml").write_text("[project]\nname='tmp'\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "swarm").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def durable_schema():
    engine = create_db_engine()
    Base.metadata.create_all(engine)
    try:
        yield
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_project_store_scrubs_secrets(repo: Path) -> None:
    store = ProjectStore(repo / "var" / "projects")
    cfg = store.create(
        name="Safe",
        repo_path=repo,
        project_id="proj_demo",
        provider_policy={"allow_paid": False, "api_key": "sk-should-not-persist"},
    )
    raw = (repo / "var" / "projects" / "proj_demo.json").read_text()
    assert "sk-should-not-persist" not in raw
    assert "api_key" not in cfg.to_dict().get("provider_policy", {})
    assert cfg.provider_policy.get("allow_paid") is False


def test_scrub_config_redacts_values() -> None:
    cleaned = scrub_config({"note": "Bearer sk-abcdefghijklmnop", "env_refs": ["SWARM_ALLOW_PAID"]})
    assert cleaned["note"] == "[redacted]"
    assert cleaned["env_refs"] == ["SWARM_ALLOW_PAID"]


def test_public_contract_lists_resources() -> None:
    contract = public_product_contract()
    assert "project" in contract["resources"]
    assert "mission" in contract["resources"]
    assert contract["spend_policy_default"] == "zero"


def test_strip_internal_fields() -> None:
    cleaned = strip_internal({"mission_id": "m1", "runtime_client": "x", "_workers": []})
    assert "runtime_client" not in cleaned
    assert "_workers" not in cleaned
    assert cleaned["mission_id"] == "m1"


def test_history_search_and_reopen(repo: Path) -> None:
    from swarm.mission.store import MissionRecord, MissionStore

    store = MissionStore(repo / "var" / "missions")
    store.save(
        MissionRecord(
            mission_id="mission_hist_1",
            goal="product journey reopen test",
            status="completed",
            created_at="2026-09-20T00:00:00Z",
            updated_at="2026-09-20T00:01:00Z",
            plan={"project_id": "proj_demo"},
            artifacts={"note": {"id": "art_1", "kind": "text", "summary": "hi"}},
            cost={"total_usd": 0.0},
        )
    )
    idx = HistoryIndex(repo)
    hits = idx.search("journey")
    assert any(h["mission_id"] == "mission_hist_1" for h in hits)
    reopened = idx.reopen("mission_hist_1")
    assert reopened["mission"]["mission_id"] == "mission_hist_1"
    assert reopened["artifacts"]


def test_api_projects_and_contract(repo: Path) -> None:
    app = create_app(require_auth=True, db_reachable=True, repo_root=repo, seed_loopback_token="atk_loopback_demo", seed_fixtures=True)
    client = TestClient(app)
    headers = {"Authorization": "Bearer atk_loopback_demo"}
    created = client.post(
        "/v1/projects",
        headers={**headers, "Idempotency-Key": "proj-create-1"},
        json={"name": "API Project", "repo_path": str(repo), "project_id": "proj_demo"},
    )
    assert created.status_code == 200, created.text
    listed = client.get("/v1/projects", headers=headers)
    assert listed.status_code == 200
    assert any(p["project_id"] == "proj_demo" for p in listed.json()["projects"])
    contract = client.get("/v1/product/contract", headers=headers)
    assert contract.status_code == 200
    assert "mission" in contract.json()["resources"]
    blob = json.dumps(created.json())
    assert "sk-" not in blob


@pytest.mark.integration
def test_product_journey_proof(repo: Path, durable_schema) -> None:
    proof = run_product_journey(repo)
    assert proof["ok"], proof
    assert proof["cost_usd"] == 0.0
    assert (repo / "var" / "reports" / "product" / "latest_journey_proof.json").exists()

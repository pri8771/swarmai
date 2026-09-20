"""FIX-002 negative regressions: auth, project isolation, idempotency.

These tests must fail before the security fix and pass afterward.
They do not satisfy live acceptance; they prove containment regressions.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from swarm.api.app import create_app
from swarm.api.auth import AuthRegistry
from swarm.contracts.fixtures import sample_mission
from swarm.mission.store import MissionRecord, MissionStore
from swarm.product.history import HistoryIndex
from swarm.product.projects import ProjectStore


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _write_history_mission(repo: Path, *, mid: str, project_id: str, goal: str) -> None:
    store = MissionStore(repo / "var" / "missions")
    store.save(
        MissionRecord(
            mission_id=mid,
            goal=goal,
            status="accepted",
            created_at="2026-09-20T00:00:00+00:00",
            updated_at="2026-09-20T00:00:00+00:00",
            plan={"project_id": project_id},
            result={"accepted": True},
            cost={"total_usd": 0.0},
        )
    )

def test_operational_app_has_no_seeded_demo_tokens() -> None:
    """Installed/default API must not ship known demo bearer identities."""
    app = create_app(require_auth=True, db_reachable=True, seed_loopback_token=None)
    auth: AuthRegistry = app.state.auth
    assert "atk_loopback_demo" not in auth.tokens
    assert "atk_policy_demo" not in auth.tokens
    assert "atk_other_project" not in auth.tokens
    assert auth.loopback_mock_token is None
    with TestClient(app) as client:
        denied = client.get(
            "/v1/missions/x",
            headers=_auth("atk_loopback_demo"),
        )
        assert denied.status_code == 401
        assert denied.json()["code"] == "unauthorized"


def test_bootstrap_token_does_not_seed_fixed_demo_principals() -> None:
    """Private bootstrap issues only the provided token — not fixed demo identities."""
    app = create_app(
        require_auth=True,
        db_reachable=True,
        seed_loopback_token="atk_private_bootstrap",
        seed_fixtures=False,
    )
    auth: AuthRegistry = app.state.auth
    assert "atk_private_bootstrap" in auth.tokens
    assert "atk_policy_demo" not in auth.tokens
    assert "atk_other_project" not in auth.tokens
    assert "atk_loopback_demo" not in auth.tokens


def test_known_demo_token_rejected_from_non_loopback() -> None:
    """Even if a demo token exists for local tests, non-loopback must not use it."""
    app = create_app(
        require_auth=True,
        db_reachable=True,
        seed_loopback_token="atk_loopback_demo",
        seed_fixtures=True,
    )
    auth: AuthRegistry = app.state.auth
    with pytest.raises(Exception) as excinfo:
        auth.resolve(
            "Bearer atk_loopback_demo",
            client_host="203.0.113.10",
        )
    err = excinfo.value
    assert getattr(err, "status_code", None) == 401
    assert getattr(err, "code", None) in {
        "unauthorized",
        "auth_required",
        "demo_token_forbidden",
    }


def test_history_and_report_deny_cross_project(tmp_path: Path) -> None:
    """History-backed records must authorize on owning project before return."""
    repo = tmp_path / "repo"
    (repo / "var" / "missions").mkdir(parents=True)
    (repo / "var" / "projects").mkdir(parents=True)
    _write_history_mission(
        repo, mid="mission_hist_a", project_id="proj_demo", goal="alpha secret goal"
    )
    _write_history_mission(
        repo, mid="mission_hist_b", project_id="proj_other", goal="beta secret goal"
    )
    ProjectStore(repo / "var" / "projects").create(
        name="demo", repo_path=repo, project_id="proj_demo"
    )
    ProjectStore(repo / "var" / "projects").create(
        name="other", repo_path=repo, project_id="proj_other"
    )
    HistoryIndex(repo).rebuild()

    app = create_app(
        require_auth=True,
        db_reachable=True,
        seed_loopback_token="atk_loopback_demo",
        seed_fixtures=True,
        repo_root=repo,
    )
    with TestClient(app) as client:
        denied = client.get(
            "/v1/history/mission_hist_a",
            headers=_auth("atk_other_project"),
        )
        assert denied.status_code == 403
        assert denied.json()["code"] == "forbidden_project"
        blob = json.dumps(denied.json())
        assert "alpha secret goal" not in blob

        denied_report = client.get(
            "/v1/missions/mission_hist_a/report",
            headers=_auth("atk_other_project"),
        )
        assert denied_report.status_code == 403
        assert "alpha secret goal" not in json.dumps(denied_report.json())

        ok = client.get(
            "/v1/history/mission_hist_a",
            headers=_auth("atk_loopback_demo"),
        )
        assert ok.status_code == 200
        assert "alpha secret goal" in json.dumps(ok.json())


def test_idempotency_scoped_and_rejects_body_mismatch() -> None:
    """Idempotency keys are scoped by actor/project/operation and digest."""
    app = create_app(
        require_auth=True,
        db_reachable=True,
        seed_loopback_token="atk_loopback_demo",
        seed_fixtures=True,
    )
    with TestClient(app) as client:
        mission_a = sample_mission().model_copy(
            update={"id": "mission_idem_scope_a", "project_id": "proj_demo"}
        )
        payload_a = {"mission": mission_a.model_dump(mode="json")}
        headers_demo = {
            **_auth("atk_loopback_demo"),
            "Idempotency-Key": "shared-key-1",
        }
        first = client.post("/v1/missions", headers=headers_demo, json=payload_a)
        assert first.status_code == 200

        mission_b = sample_mission().model_copy(
            update={"id": "mission_idem_scope_b", "project_id": "proj_demo"}
        )
        payload_b = {"mission": mission_b.model_dump(mode="json")}
        mismatch = client.post("/v1/missions", headers=headers_demo, json=payload_b)
        assert mismatch.status_code == 409
        assert mismatch.json()["code"] == "idempotency_payload_mismatch"

        headers_other = {
            **_auth("atk_other_project"),
            "Idempotency-Key": "shared-key-1",
        }
        mission_other = sample_mission().model_copy(
            update={"id": "mission_idem_scope_c", "project_id": "proj_other"}
        )
        other = client.post(
            "/v1/missions",
            headers=headers_other,
            json={"mission": mission_other.model_dump(mode="json")},
        )
        assert other.status_code == 200
        assert other.json()["mission"]["id"] == "mission_idem_scope_c"
        assert other.json()["mission"]["id"] != first.json()["mission"]["id"]


def test_history_search_filters_by_principal_projects(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "var" / "missions").mkdir(parents=True)
    _write_history_mission(
        repo, mid="mission_s_a", project_id="proj_demo", goal="goal-mission_s_a"
    )
    _write_history_mission(
        repo, mid="mission_s_b", project_id="proj_other", goal="goal-mission_s_b"
    )
    idx = HistoryIndex(repo)
    assert len(idx.search("")) >= 2

    app = create_app(
        require_auth=True,
        db_reachable=True,
        seed_loopback_token="atk_loopback_demo",
        seed_fixtures=True,
        repo_root=repo,
    )
    with TestClient(app) as client:
        rows = client.get("/v1/history", headers=_auth("atk_other_project")).json()[
            "entries"
        ]
        ids = {r["mission_id"] for r in rows}
        assert "mission_s_b" in ids
        assert "mission_s_a" not in ids

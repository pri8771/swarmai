"""FIX-002: worker/approval project ownership + install-local bootstrap."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from swarm.api.app import create_app, resolve_install_project_id


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_operational_bootstrap_uses_install_local_not_demo_projects(tmp_path: Path) -> None:
    app = create_app(
        require_auth=True,
        db_reachable=True,
        seed_loopback_token="atk_private_bootstrap",
        seed_fixtures=False,
        repo_root=tmp_path,
        install_project_id="proj_install_local_a",
    )
    auth = app.state.auth
    principal = auth.tokens["atk_private_bootstrap"]
    assert "proj_demo" not in principal.project_ids
    assert "proj_other" not in principal.project_ids
    assert principal.project_ids == frozenset({"proj_install_local_a"})
    assert principal.subject == "install-operator"
    assert app.state.install_project_id == "proj_install_local_a"


def test_resolve_install_project_id_persists(tmp_path: Path) -> None:
    first = resolve_install_project_id(tmp_path)
    second = resolve_install_project_id(tmp_path)
    assert first == second
    assert first.startswith("proj_install_")
    assert first not in {"proj_demo", "proj_other"}
    identity = tmp_path / "var" / "install" / "identity.json"
    assert identity.is_file()


def test_workers_and_approvals_isolated_across_projects() -> None:
    app = create_app(
        require_auth=True,
        db_reachable=True,
        seed_loopback_token="atk_loopback_demo",
        seed_fixtures=True,
    )
    with TestClient(app) as client:
        # Enroll worker on proj_demo
        demo = client.post(
            "/v1/workers/enroll",
            headers=_auth("atk_loopback_demo"),
            json={
                "project_id": "proj_demo",
                "capabilities": ["chat"],
                "capacity_units": 1.0,
                "privacy_classes": ["local"],
            },
        )
        assert demo.status_code == 200
        demo_worker = demo.json()["worker"]["worker_id"]

        # Enroll worker on proj_other as other-project user
        other = client.post(
            "/v1/workers/enroll",
            headers=_auth("atk_other_project"),
            json={
                "project_id": "proj_other",
                "capabilities": ["chat"],
                "capacity_units": 1.0,
                "privacy_classes": ["local"],
            },
        )
        assert other.status_code == 200
        other_worker = other.json()["worker"]["worker_id"]

        # other-project user must not see demo workers
        listed = client.get("/v1/workers", headers=_auth("atk_other_project"))
        assert listed.status_code == 200
        ids = {w["worker_id"] for w in listed.json()["workers"]}
        assert other_worker in ids
        assert demo_worker not in ids

        # Create approvals owned by each project
        store = client.app.state.store
        apr_demo = store.create_approval(
            permitted_operation="tool.network",
            destination="https://example.invalid",
            grantor="loopback-operator",
            payload={"project_id": "proj_demo", "op": "tool.network"},
            project_id="proj_demo",
        )
        apr_other = store.create_approval(
            permitted_operation="tool.network",
            destination="https://example.invalid",
            grantor="other-project-user",
            payload={"project_id": "proj_other", "op": "tool.network"},
            project_id="proj_other",
        )

        listed_apr = client.get("/v1/approvals", headers=_auth("atk_other_project"))
        assert listed_apr.status_code == 200
        apr_ids = {a["id"] for a in listed_apr.json()["approvals"]}
        assert apr_other.id in apr_ids
        assert apr_demo.id not in apr_ids

        # Cross-project resolve denied
        denied = client.post(
            f"/v1/approvals/{apr_demo.id}/resolve",
            headers=_auth("atk_other_project"),
            json={
                "accept": True,
                "payload": {"project_id": "proj_demo", "op": "tool.network"},
            },
        )
        assert denied.status_code == 403
        assert denied.json()["code"] == "forbidden_project"


def test_demo_side_effect_fixture_only() -> None:
    operational = create_app(
        require_auth=True,
        db_reachable=True,
        seed_loopback_token="atk_private_bootstrap",
        seed_fixtures=False,
        install_project_id="proj_install_ops",
    )
    with TestClient(operational) as client:
        r = client.post(
            "/v1/missions/msn_x/side-effects/demo",
            headers=_auth("atk_private_bootstrap"),
        )
        assert r.status_code == 404
        assert r.json()["code"] == "fixture_only"

    fixture = create_app(
        require_auth=True,
        db_reachable=True,
        seed_loopback_token="atk_loopback_demo",
        seed_fixtures=True,
    )
    with TestClient(fixture) as client:
        assert fixture.state.store.fixture_mode is True
        # Mission missing → not_found after fixture gate (or 404 fixture_only already passed)
        # Create a mission then cancel and hit demo route for 409 — or just ensure not fixture_only 404
        from swarm.contracts.fixtures import sample_mission

        mission = sample_mission()
        created = client.post(
            "/v1/missions",
            headers=_auth("atk_loopback_demo"),
            json={"mission": mission.model_dump(mode="json")},
        )
        assert created.status_code == 200
        mid = created.json()["mission"]["id"]
        demo = client.post(
            f"/v1/missions/{mid}/side-effects/demo",
            headers=_auth("atk_loopback_demo"),
        )
        assert demo.status_code == 200

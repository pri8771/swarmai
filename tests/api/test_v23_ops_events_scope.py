"""SW-W0-S3 / F-01: GET /v1/ops/events must not leak other projects' events."""

from __future__ import annotations

from fastapi.testclient import TestClient

from swarm.api.app import create_app


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _app_with_events():
    app = create_app(require_auth=True, db_reachable=True, seed_fixtures=True)
    log = app.state.ops_events
    log.emit("scheduler.decision", "scheduler", project_id="proj_demo", detail={"n": 1})
    log.emit("scheduler.decision", "scheduler", project_id="proj_other", detail={"n": 2})
    log.emit("site.epoch", "recovery", project_id=None, detail={"n": 3})
    return app


def test_unscoped_list_only_returns_own_projects() -> None:
    app = _app_with_events()
    with TestClient(app) as client:
        res = client.get("/v1/ops/events", headers=_auth("atk_policy_demo"))
    assert res.status_code == 200
    projects = {e["project_id"] for e in res.json()["events"]}
    assert projects == {"proj_demo"}


def test_foreign_project_filter_is_forbidden() -> None:
    app = _app_with_events()
    with TestClient(app) as client:
        res = client.get(
            "/v1/ops/events", params={"project_id": "proj_other"}, headers=_auth("atk_policy_demo")
        )
    assert res.status_code == 403
    assert res.json()["code"] == "forbidden_project"


def test_admin_sees_all_events() -> None:
    app = _app_with_events()
    app.state.auth.issue(
        subject="site-admin", project_ids=set(), roles={"admin"}, token="atk_admin_test"
    )
    with TestClient(app) as client:
        res = client.get("/v1/ops/events", headers=_auth("atk_admin_test"))
    assert res.status_code == 200
    assert len(res.json()["events"]) == 3

"""P13 authenticated product API tests."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from swarm.api.app import create_app
from swarm.contracts.common import payload_hash
from swarm.contracts.fixtures import sample_mission


@pytest.fixture
def client() -> TestClient:
    app = create_app(require_auth=True, db_reachable=True, seed_loopback_token="atk_loopback_demo")
    return TestClient(app)


def _auth(token: str = "atk_loopback_demo") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_health_ready_reflects_database(client: TestClient) -> None:
    live = client.get("/health/live")
    assert live.status_code == 200
    ready = client.get("/health/ready")
    assert ready.status_code == 200
    body = ready.json()
    assert body["database"] == "up"
    assert body["runtime"] == "ok"
    assert body["status"] == "ready"
    assert body["mock_vs_live"]


def test_health_not_ready_when_db_down() -> None:
    app = create_app(require_auth=True, db_reachable=False, seed_loopback_token="atk_loopback_demo")
    with TestClient(app) as c:
        body = c.get("/health/ready").json()
        assert body["status"] == "not_ready"
        assert body["database"] == "down"


def test_auth_required_and_project_isolation(client: TestClient) -> None:
    assert client.get("/v1/missions/x").status_code == 401
    mission = sample_mission()
    r = client.post(
        "/v1/missions",
        headers=_auth(),
        json={"mission": mission.model_dump(mode="json")},
    )
    assert r.status_code == 200
    mid = r.json()["mission"]["id"]
    # Other project token cannot read.
    denied = client.get(f"/v1/missions/{mid}", headers=_auth("atk_other_project"))
    assert denied.status_code == 403
    assert denied.json()["code"] == "forbidden_project"


def test_no_secrets_in_provider_output(client: TestClient) -> None:
    r = client.get("/v1/providers", headers=_auth())
    assert r.status_code == 200
    blob = json.dumps(r.json())
    assert "sk-" not in blob
    assert "OPENROUTER_API_KEY" in blob  # ref name OK
    accounts = r.json()["accounts"]
    assert accounts
    assert "secret_ref_names" in accounts[0]
    assert not any("secret_value" in a for a in accounts)


def test_idempotent_mutation(client: TestClient) -> None:
    mission = sample_mission().model_copy(update={"id": "mission_idem_001"})
    headers = {**_auth(), "Idempotency-Key": "idem-create-1"}
    payload = {"mission": mission.model_dump(mode="json")}
    a = client.post("/v1/missions", headers=headers, json=payload)
    b = client.post("/v1/missions", headers=headers, json=payload)
    assert a.status_code == 200
    assert b.status_code == 200
    assert a.json() == b.json()


def test_event_reconnect_and_dedupe(client: TestClient) -> None:
    mission = sample_mission().model_copy(update={"id": "mission_evt_001"})
    client.post(
        "/v1/missions",
        headers=_auth(),
        json={"mission": mission.model_dump(mode="json")},
    )
    # Force duplicate publish with same dedupe_key via store.
    store = client.app.state.store
    store.publish(
        project_id="proj_demo",
        type="mission.created",
        actor="t",
        mission_id=mission.id,
        payload={"dup": True},
        dedupe_key=f"mission.created:{mission.id}",
    )
    page1 = client.get("/v1/events?project_id=proj_demo&limit=10", headers=_auth()).json()
    created = [e for e in page1["items"] if e["type"] == "mission.created"]
    assert len(created) == 1
    cursor = page1["page"]["cursor"]
    # More events after cursor.
    store.publish(
        project_id="proj_demo",
        type="graph.committed",
        actor="t",
        mission_id=mission.id,
        payload={"revision": 2},
        dedupe_key="graph.committed:mission_evt_001:2",
    )
    page2 = client.get(
        f"/v1/events?project_id=proj_demo&after={cursor}&limit=10",
        headers=_auth(),
    ).json()
    assert any(e["type"] == "graph.committed" for e in page2["items"])
    assert all(e["id"] != created[0]["id"] or e["type"] != "mission.created" for e in page2["items"])


def test_retired_and_unknown_route_statuses(client: TestClient) -> None:
    r = client.get("/v1/routes", headers=_auth()).json()
    statuses = {row.get("availability_status") or row.get("status") for row in r["routes"]}
    assert "retired" in statuses
    # Fixture routes may be unknown or available — never silently invent production-ready.
    assert "unknown" in statuses or any(
        row.get("availability_status") == "unknown" for row in r["routes"]
    )


def test_cancel_blocks_side_effects(client: TestClient) -> None:
    mission = sample_mission().model_copy(update={"id": "mission_cancel_001"})
    client.post(
        "/v1/missions",
        headers=_auth(),
        json={"mission": mission.model_dump(mode="json")},
    )
    ok = client.post(
        f"/v1/missions/{mission.id}/side-effects/demo",
        headers=_auth(),
    )
    assert ok.status_code == 200
    cancel = client.post(
        f"/v1/missions/{mission.id}/cancel",
        headers={**_auth(), "Idempotency-Key": "cancel-1"},
        json={"reason": "user"},
    )
    assert cancel.status_code == 200
    assert cancel.json()["mission"]["status"] == "cancelled"
    blocked = client.post(
        f"/v1/missions/{mission.id}/side-effects/demo",
        headers=_auth(),
    )
    assert blocked.status_code == 409
    assert blocked.json()["code"] == "mission_cancelled"
    # Replay cancel is safe.
    cancel2 = client.post(
        f"/v1/missions/{mission.id}/cancel",
        headers={**_auth(), "Idempotency-Key": "cancel-1"},
        json={"reason": "user"},
    )
    assert cancel2.json() == cancel.json()


def test_approval_verification(client: TestClient) -> None:
    store = client.app.state.store
    payload = {"project_id": "proj_demo", "op": "tool.network"}
    approval = store.create_approval(
        permitted_operation="tool.network",
        destination="https://example.invalid",
        grantor="loopback-operator",
        payload=payload,
    )
    # Mismatch payload rejected.
    bad = client.post(
        f"/v1/approvals/{approval.id}/resolve",
        headers=_auth(),
        json={"accept": True, "payload": {"project_id": "proj_demo", "op": "changed"}},
    )
    assert bad.status_code == 409
    assert bad.json()["code"] == "approval_payload_mismatch"
    good = client.post(
        f"/v1/approvals/{approval.id}/resolve",
        headers=_auth(),
        json={"accept": True, "payload": payload},
    )
    assert good.status_code == 200
    assert good.json()["accepted"] is True
    assert payload_hash(payload) == approval.payload_hash


def test_probe_and_eval_require_policy(client: TestClient) -> None:
    denied = client.post("/v1/providers/openrouter/probe", headers=_auth())
    assert denied.status_code == 403
    allowed = client.post("/v1/providers/openrouter/probe", headers=_auth("atk_policy_demo"))
    assert allowed.status_code == 200
    assert allowed.json()["status"] == "blocked"
    assert allowed.json()["mock_vs_live"] == "probe_not_live"

    eval_denied = client.post(
        "/v1/evaluations",
        headers=_auth(),
        json={"suite": "starter", "mode": "mock", "max_cases": 2},
    )
    assert eval_denied.status_code == 403
    eval_ok = client.post(
        "/v1/evaluations",
        headers=_auth("atk_policy_demo"),
        json={"suite": "starter", "mode": "mock", "max_cases": 2},
    )
    assert eval_ok.status_code == 200
    assert eval_ok.json()["mock_vs_live"] == "plan_only_not_executed_live"


def test_workers_enroll_and_heartbeat(client: TestClient) -> None:
    r = client.post(
        "/v1/workers/enroll",
        headers=_auth(),
        json={
            "project_id": "proj_demo",
            "capabilities": ["chat"],
            "capacity_units": 2.0,
            "privacy_classes": ["local"],
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert "membership_token" in body
    assert "sk-" not in json.dumps(body)
    wid = body["worker"]["worker_id"]
    token = body["membership_token"]
    hb = client.post(
        "/v1/workers/heartbeat",
        headers=_auth(),
        json={"worker_id": wid, "generation": 1, "token": token},
    )
    assert hb.status_code == 200
    listed = client.get("/v1/workers", headers=_auth()).json()
    assert any(w["worker_id"] == wid for w in listed["workers"])


def test_openapi_contains_v1_paths(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()
    paths = spec["paths"]
    for p in (
        "/v1/missions",
        "/v1/events",
        "/v1/providers",
        "/v1/routes",
        "/v1/capacity",
        "/v1/workers",
        "/v1/approvals",
    ):
        assert p in paths


def test_capacity_and_qualifications(client: TestClient) -> None:
    cap = client.get("/v1/capacity", headers=_auth())
    assert cap.status_code == 200
    assert cap.json()["mock_vs_live"] == "mock_fixtures_only"
    q = client.get("/v1/qualifications", headers=_auth())
    assert q.status_code == 200
    assert "policy_version" in q.json()


def test_sse_events_stream(client: TestClient) -> None:
    mission = sample_mission().model_copy(update={"id": "mission_sse_001"})
    client.post(
        "/v1/missions",
        headers=_auth(),
        json={"mission": mission.model_dump(mode="json")},
    )
    with client.stream(
        "GET",
        "/v1/events/stream?project_id=proj_demo",
        headers=_auth(),
    ) as resp:
        assert resp.status_code == 200
        text = "".join(resp.iter_text())
    assert "mission.created" in text
    assert "event: cursor" in text

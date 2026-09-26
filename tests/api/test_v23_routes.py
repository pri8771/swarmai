"""SW-W3-S1: V2.3 routes are project-scoped and admin-gated."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from swarm.api.app import create_app
from swarm.capabilities import CapabilityPackManifest
from swarm.capabilities.signing import sign_manifest

DEMO = "atk_policy_demo"
OTHER = "atk_other_project"
ADMIN = "atk_admin_v23"
PACK_KEY = b"test-only-pack-key"


def _h(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("SWARM_V23_DURABLE", raising=False)
    monkeypatch.setenv("SWARM_PACK_TRUSTED_PUBLISHERS", "acme")
    monkeypatch.setenv("SWARM_PACK_KEY_ACME", PACK_KEY.decode())
    app = create_app(require_auth=True, db_reachable=False, seed_fixtures=True, repo_root=tmp_path)
    app.state.auth.issue(subject="site-admin", project_ids=set(), roles={"admin"}, token=ADMIN)
    with TestClient(app) as c:
        yield c


def _manifest(signed: bool) -> dict:
    m = CapabilityPackManifest(
        pack_id="pack_demo",
        version="1.0.0",
        content_digest="sha256:abc",
        capability_declarations=["read_docs"],
        publisher="acme",
    )
    return (sign_manifest(m, key=PACK_KEY) if signed else m).model_dump(mode="json")


def test_queues_are_project_scoped(client: TestClient) -> None:
    assert client.post("/v1/scheduler/projects/proj_demo", json={}, headers=_h(DEMO)).status_code == 200
    assert client.post("/v1/scheduler/projects/proj_other", json={}, headers=_h(OTHER)).status_code == 200
    rows = client.get("/v1/scheduler/queues", headers=_h(DEMO)).json()["projects"]
    assert [r["project_id"] for r in rows] == ["proj_demo"]
    assert {"weight", "credit", "running", "max_concurrency", "paused"} <= set(rows[0])
    admin_rows = client.get("/v1/scheduler/queues", headers=_h(ADMIN)).json()["projects"]
    assert {r["project_id"] for r in admin_rows} == {"proj_demo", "proj_other"}


def test_scheduler_mutations_require_project(client: TestClient) -> None:
    res = client.post("/v1/scheduler/projects/proj_other", json={}, headers=_h(DEMO))
    assert res.status_code == 403
    client.post("/v1/scheduler/projects/proj_demo", json={}, headers=_h(DEMO))
    res = client.post("/v1/scheduler/projects/proj_demo/weight", json={"weight": 3}, headers=_h(DEMO))
    assert res.status_code == 200 and res.json()["weight"] == 3.0
    assert client.post("/v1/scheduler/projects/proj_demo/pause", headers=_h(DEMO)).json()["paused"]
    assert client.post("/v1/scheduler/projects/proj_demo/bogus", headers=_h(DEMO)).status_code == 404
    unknown = client.post("/v1/scheduler/projects/proj_demo/weight", json={"weight": 0}, headers=_h(DEMO))
    assert unknown.status_code == 422
    assert client.get("/v1/scheduler/receipts", headers=_h(DEMO)).status_code == 403
    own = client.get("/v1/scheduler/receipts", params={"project_id": "proj_demo"}, headers=_h(DEMO))
    assert own.status_code == 200 and own.json() == {"receipts": []}


def test_trace_never_leaks_foreign_projects(client: TestClient) -> None:
    log = client.app.state.ops_events  # type: ignore[attr-defined]
    log.emit("operator.action", "api", project_id="proj_other", trace_id="tr_x")
    log.emit("operator.action", "api", project_id="proj_demo", trace_id="tr_mine")
    assert client.get("/v1/ops/trace/tr_x", headers=_h(DEMO)).status_code == 404
    assert client.get("/v1/ops/trace/tr_x", headers=_h(ADMIN)).status_code == 200
    mine = client.get("/v1/ops/trace/tr_mine", headers=_h(DEMO))
    assert mine.status_code == 200 and mine.json()["projects"] == ["proj_demo"]
    assert client.get("/v1/ops/trace/tr_none", headers=_h(ADMIN)).status_code == 404


def test_pack_install_requires_admin_and_signature(client: TestClient) -> None:
    signed = {"manifest": _manifest(signed=True)}
    assert client.post("/v1/packs/install", json=signed, headers=_h(DEMO)).status_code == 403
    unsigned = client.post("/v1/packs/install", json={"manifest": _manifest(False)}, headers=_h(ADMIN))
    assert unsigned.status_code == 403 and unsigned.json()["code"] == "pack_rejected"
    assert client.post("/v1/packs/install", json=signed, headers=_h(ADMIN)).status_code == 200
    body = {"capabilities": ["read_docs"]}
    url = "/v1/projects/{p}/packs/pack_demo/1.0.0/enable"
    assert client.post(url.format(p="proj_demo"), json=body, headers=_h(DEMO)).status_code == 200
    assert client.post(url.format(p="proj_other"), json=body, headers=_h(DEMO)).status_code == 403
    assert client.post("/v1/packs/pack_demo/1.0.0/revoke", headers=_h(DEMO)).status_code == 403
    assert client.post("/v1/packs/pack_demo/1.0.0/revoke", headers=_h(ADMIN)).status_code == 200
    hist = client.get("/v1/packs/pack_demo/1.0.0/history", headers=_h(ADMIN)).json()["history"]
    assert [h["action"] for h in hist] == ["install", "revoke"]


def test_portability_export_import_scoped(client: TestClient) -> None:
    res = client.post("/v1/projects/proj_demo/export", headers=_h(DEMO))
    assert res.status_code == 200
    bundle_id = res.json()["bundle_id"]
    ok = client.post("/v1/projects/proj_demo/import", json={"bundle_id": bundle_id}, headers=_h(DEMO))
    assert ok.status_code == 200 and ok.json()["imported"] is True
    stolen = client.post(
        "/v1/projects/proj_other/import", json={"bundle_id": bundle_id}, headers=_h(OTHER)
    )
    assert stolen.status_code == 403
    bad = client.post("/v1/projects/proj_demo/import", json={"bundle_id": "../x"}, headers=_h(DEMO))
    assert bad.status_code == 422
    assert client.post("/v1/projects/proj_other/export", headers=_h(DEMO)).status_code == 403


def test_worker_drain_and_revoke_are_scoped(client: TestClient) -> None:
    enrolled = client.post("/v1/workers/enroll", json={"project_id": "proj_demo"}, headers=_h(DEMO))
    assert enrolled.status_code == 200
    wid = enrolled.json()["worker"]["worker_id"]
    body = {"reason": "maintenance"}
    assert client.post(f"/v1/workers/{wid}/drain", json=body, headers=_h(OTHER)).status_code == 403
    drained = client.post(f"/v1/workers/{wid}/drain", json=body, headers=_h(DEMO))
    assert drained.json() == {"worker_id": wid, "drain_state": "draining"}
    revoked = client.post(f"/v1/workers/{wid}/revoke", json=body, headers=_h(DEMO))
    assert revoked.json() == {"worker_id": wid, "drain_state": "revoked"}
    assert client.post(f"/v1/workers/{wid}/drain", json=body, headers=_h(DEMO)).status_code == 409
    assert client.post("/v1/workers/wk_nope/drain", json=body, headers=_h(DEMO)).status_code == 404
    kinds = [e["detail"]["action"] for e in client.get("/v1/ops/events", headers=_h(DEMO)).json()["events"]]
    assert kinds == ["worker.drain", "worker.revoke"]


def test_fleet_audit_is_admin_only(client: TestClient) -> None:
    assert client.get("/v1/fleet/audit", headers=_h(DEMO)).status_code == 403
    assert client.get("/v1/fleet/audit", headers=_h(ADMIN)).status_code == 200

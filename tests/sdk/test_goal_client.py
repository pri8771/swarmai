"""SDK client tests — Lane C Goals + Lane D pursuit against real API app."""

from __future__ import annotations

import os
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from httpx import Response

from swarm.api.app import create_app
from swarm.goals.models import GoalStatus
from swarm.sdk import SwarmClient, SwarmClientError


@pytest.fixture(autouse=True)
def _clear_swarm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith("SWARM_"):
            monkeypatch.delenv(key, raising=False)


class _StarletteTransport(httpx.BaseTransport):
    """Sync httpx transport over FastAPI TestClient (httpx ASGITransport is async-only)."""

    def __init__(self, app: object) -> None:
        self._tc = TestClient(app)

    def handle_request(self, request: httpx.Request) -> Response:
        headers = [(k.decode(), v.decode()) for k, v in request.headers.raw]
        body = request.content
        path = request.url.path
        if request.url.query:
            path = f"{path}?{request.url.query.decode()}"
        resp = self._tc.request(
            request.method,
            path,
            headers=dict(headers),
            content=body,
        )
        return Response(
            status_code=resp.status_code,
            headers=resp.headers,
            content=resp.content,
            request=request,
        )


def _client(path: Path) -> SwarmClient:
    app = create_app(
        repo_root=path,
        seed_loopback_token="sdk-token",
        install_project_id="proj_sdk",
        db_reachable=None,
    )
    return SwarmClient("http://test", token="sdk-token", transport=_StarletteTransport(app))


def test_sdk_goal_lifecycle_and_pursuit(tmp_path: Path) -> None:
    with _client(tmp_path / "server") as client:
        goal = client.create_goal(
            project_id="proj_sdk",
            desired_outcome="Prove SDK/API parity for goal pursuit",
            verification_criteria=["contacts_extracted", "human_acceptance"],
            permitted_agents=["planner", "verifier"],
            resource_envelope={"max_budget_usd": 0.0},
            authority_envelope={"tools": []},
            strategy="create → pursue → interrupt → resume",
            kind="finite",
        )
        assert goal.status == GoalStatus.ACTIVE

        listed = client.list_goals(project_id="proj_sdk")
        assert any(g.id == goal.id for g in listed)

        started = client.start_pursuit(goal.id, force=True)
        assert "cycle" in started
        assert started["goal"].id == goal.id
        cycle = started["cycle"]
        assert isinstance(cycle, dict)
        assert cycle.get("decided_kind") in {"act", "ask", "wait", "experiment", "request_human"}

        paused = client.interrupt_goal(goal.id, reason="operator interrupt")
        assert paused.status == GoalStatus.PAUSED
        resumed = client.resume_goal(goal.id, reason="operator resume")
        assert resumed.status == GoalStatus.ACTIVE

        why = client.why_next(goal.id)
        assert why["goal_id"] == goal.id
        assert why["pursuit"]["goal_id"] == goal.id
        assert why["why_next"]

        redirected = client.redirect_goal(goal.id, reason="try alternate extraction path")
        assert redirected["goal"].status in {
            GoalStatus.ACTIVE,
            GoalStatus.WAITING,
            GoalStatus.BLOCKED,
            GoalStatus.ACHIEVED,
            GoalStatus.PAUSED,
        }
        assert redirected.get("cycle") is not None


def test_sdk_rejects_resume_from_cancelled(tmp_path: Path) -> None:
    with _client(tmp_path / "server") as client:
        goal = client.create_goal(
            project_id="proj_sdk",
            desired_outcome="terminal cancel",
        )
        client.cancel_goal(goal.id, reason="done")
        with pytest.raises(SwarmClientError) as exc:
            client.resume_goal(goal.id)
        assert exc.value.status_code in {409, 400, 422}


def test_sdk_matches_http_create_shape(tmp_path: Path) -> None:
    """UI/SDK/API share the same POST /v1/goals body fields (Lane C)."""
    root = tmp_path / "server"
    app = create_app(
        repo_root=root,
        seed_loopback_token="sdk-token",
        install_project_id="proj_sdk",
        db_reachable=None,
    )
    http = TestClient(app)
    body = {
        "project_id": "proj_sdk",
        "desired_outcome": "shape check",
        "verification_criteria": ["a"],
        "kind": "finite",
        "permitted_agents": ["a1"],
        "resource_envelope": {"max_budget_usd": 0},
        "authority_envelope": {"tools": []},
        "strategy": "s",
    }
    via_http = http.post("/v1/goals", headers={"Authorization": "Bearer sdk-token"}, json=body)
    assert via_http.status_code == 200, via_http.text

    with SwarmClient(
        "http://test", token="sdk-token", transport=_StarletteTransport(app)
    ) as client:
        via_sdk = client.create_goal(
            project_id="proj_sdk",
            desired_outcome="shape check sdk",
            verification_criteria=["a"],
            kind="finite",
            permitted_agents=["a1"],
            resource_envelope={"max_budget_usd": 0},
            authority_envelope={"tools": []},
            strategy="s",
        )
    assert via_sdk.project_id == "proj_sdk"
    assert set(via_http.json()["goal"].keys()) == set(via_sdk.model_dump(mode="json").keys())


def test_sdk_workers_approvals_artifacts_parity(tmp_path: Path) -> None:
    """SDK mirrors console control surfaces for workers/approvals/artifacts/events."""
    with _client(tmp_path / "server") as client:
        workers = client.list_workers()
        assert isinstance(workers, list)
        approvals = client.list_approvals()
        assert isinstance(approvals, list)
        mission = client.create_mission(
            project_id="proj_sdk",
            objective="artifact parity mission",
        )
        mid = str(mission.get("id") or mission.get("mission_id") or "")
        assert mid
        arts = client.list_mission_artifacts(mid)
        assert isinstance(arts, list)
        events = client.list_events(mission_id=mid, limit=10)
        assert isinstance(events, list)
        with pytest.raises(SwarmClientError) as exc:
            client.cancel_worker_lease("lease_missing")
        assert exc.value.status_code in {404, 400, 422}
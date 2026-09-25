"""V1.7 protected verification + Goal entity tests."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from swarm.api.app import create_app
from swarm.contracts.fixtures import sample_mission
from swarm.goals.models import Goal, GoalStatus, GoalStore
from swarm.mission.protected_verify import compute_extract_checks, protected_review

HEADERS = {"Authorization": "Bearer review-only-token"}


@pytest.fixture(autouse=True)
def _clear_swarm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith("SWARM_"):
            monkeypatch.delenv(key, raising=False)


def _client(path: Path) -> TestClient:
    app = create_app(
        repo_root=path,
        seed_loopback_token="review-only-token",
        install_project_id="proj_review",
        db_reachable=None,
    )
    return TestClient(app)


def test_protected_extract_ignores_worker_checks() -> None:
    payload = {
        "emails": ["a@example.com", "b@example.com"],
        "text": "hello a@example.com b@example.com",
    }
    raw = json.dumps(payload).encode()
    digest = hashlib.sha256(raw).hexdigest()
    computed = compute_extract_checks(artifact_bytes=raw, content_hash=digest)
    assert computed["email_count"] == 2
    result = protected_review(
        task_family="extract",
        required_checks={
            "email_count": 2,
            "artifact_sha256": digest,
            "placement": "server_verified",
            "host_role": "protected_verifier",
            "runtime": "swarm_kernel",
        },
        artifact_id="art_1",
        artifact_bytes=raw,
        content_hash=digest,
        worker_produced={"checks": {"email_count": 99}},
    )
    assert result.accepted is True
    assert result.computed["email_count"] == 2


def test_v17_http_protected_accept_and_reject_forge(tmp_path: Path) -> None:
    client = _client(tmp_path / "server")
    emails = ["one@example.com", "two@example.com"]
    body_text = "contact " + " ".join(emails)
    content = json.dumps({"emails": emails, "body": body_text}).encode()
    digest = hashlib.sha256(content).hexdigest()
    mission = sample_mission().model_copy(update={"id": "msn_v17", "project_id": "proj_review"})
    created = client.post(
        "/v1/missions",
        headers=HEADERS,
        json={
            "mission": mission.model_dump(mode="json"),
            "task_family": "extract",
            "required_checks": {
                "email_count": 2,
                "artifact_sha256": digest,
                "placement": "server_verified",
                "host_role": "protected_verifier",
                "runtime": "swarm_kernel",
            },
        },
    )
    assert created.status_code == 200, created.text
    published = client.post(
        "/v1/missions/msn_v17/artifacts",
        headers=HEADERS,
        json={
            "kind": "result",
            "content_base64": __import__("base64").b64encode(content).decode(),
            "media_type": "application/json",
        },
    )
    assert published.status_code == 200, published.text
    # Worker lies about count — server must still accept from artifact.
    review = client.post(
        "/v1/missions/msn_v17/review",
        headers=HEADERS,
        json={"produced": {"checks": {"email_count": 99, "artifact_sha256": "forged"}}},
    )
    assert review.status_code == 200, review.text
    assert review.json()["accepted"] is True
    assert review.json()["mission"]["status"] == "completed"


def test_goal_store_transitions_and_link(tmp_path: Path) -> None:
    store = GoalStore(tmp_path / "goals")
    goal = store.create(
        Goal(
            project_id="proj_review",
            desired_outcome="Extract contacts safely",
            verification_criteria=["email_count matches artifact"],
        )
    )
    assert goal.status == GoalStatus.ACTIVE
    paused = store.transition(goal.id, GoalStatus.PAUSED, reason="operator pause", actor="op")
    assert paused.status == GoalStatus.PAUSED
    # create + pause both append durable decision history
    assert len(paused.decision_history) >= 2
    resumed = store.transition(goal.id, GoalStatus.ACTIVE, reason="resume", actor="op")
    assert resumed.status == GoalStatus.ACTIVE
    linked = store.link_mission(goal.id, "msn_1")
    assert "msn_1" in linked.mission_ids
    # Cold reopen
    cold = GoalStore(tmp_path / "goals")
    assert cold.get(goal.id).mission_ids == ["msn_1"]
    assert len(cold.get(goal.id).decision_history) >= 3


def test_goal_api_create_transition(tmp_path: Path) -> None:
    client = _client(tmp_path / "server")
    created = client.post(
        "/v1/goals",
        headers=HEADERS,
        json={
            "project_id": "proj_review",
            "desired_outcome": "Complete extract mission chain",
            "verification_criteria": ["protected verify accepts"],
        },
    )
    assert created.status_code == 200, created.text
    goal_id = created.json()["goal"]["id"]
    paused = client.post(
        f"/v1/goals/{goal_id}/transition",
        headers=HEADERS,
        json={"status": "paused", "reason": "wait"},
    )
    assert paused.status_code == 200
    assert paused.json()["goal"]["status"] == "paused"
    listed = client.get("/v1/goals", headers=HEADERS, params={"project_id": "proj_review"})
    assert listed.status_code == 200
    assert any(g["id"] == goal_id for g in listed.json()["goals"])

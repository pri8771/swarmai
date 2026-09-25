"""V1.7 mission path proof: claim → execute → artifact → protected verify.

No fixture echo success. Worker lease path + real extract bytes + CAS artifact
+ server protected verifier. Operational pursuit must not achieve via RecordingExecutor.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from swarm.api.app import create_app
from swarm.contracts.common import new_id
from swarm.contracts.enums import MissionStatus
from swarm.contracts.fixtures import sample_mission, sample_task
from swarm.pursuit.native_dispatch import NativeMissionDispatchExecutor

HEADERS = {"Authorization": "Bearer review-only-token"}
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


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
        db_reachable=False,
    )
    return TestClient(app)


def _real_extract_bytes(input_path: Path) -> bytes:
    """Actual local extract — parse emails from file bytes (no echo/fixture invent)."""
    text = input_path.read_text(encoding="utf-8")
    emails = sorted(set(_EMAIL_RE.findall(text)))
    assert emails, "extract produced no emails — input fixture incomplete"
    return json.dumps(
        {
            "emails": emails,
            "source_path": str(input_path),
            "runtime": "deterministic_local_extract",
            "mode": "real_execution",
        },
        sort_keys=True,
    ).encode("utf-8")


def test_r20_01_operational_pursuit_does_not_false_achieve(tmp_path: Path) -> None:
    """R20-01: operational tick dispatches native mission; never RecordingExecutor achieve."""
    client = _client(tmp_path / "server")
    store = client.app.state.store
    assert store.fixture_mode is False
    assert store.execution_mode == "operational"
    assert isinstance(store.pursuit_engine().executor, NativeMissionDispatchExecutor)

    created = client.post(
        "/v1/goals",
        headers=HEADERS,
        json={
            "project_id": "proj_review",
            "desired_outcome": "Produce a verified report",
            "verification_criteria": ["report exists"],
            "resource_envelope": {"spend_usd_ceiling": 0.0},
            "authority_envelope": {"tools": ["workspace.read"], "providers": ["fake"]},
        },
    )
    assert created.status_code == 200, created.text
    goal_id = created.json()["goal"]["id"]
    tick = client.post(
        f"/v1/goals/{goal_id}/pursuit/tick",
        headers=HEADERS,
        json={"force": True},
    )
    assert tick.status_code == 200, tick.text
    body = tick.json()
    assert body["goal"]["status"] != "achieved"
    outcome = body["cycle"].get("outcome") or {}
    assert outcome.get("success") is False
    assert outcome.get("failure_class") == "submitted_pending"
    assert outcome.get("runtime") == "native"
    mission_id = outcome.get("mission_id")
    assert mission_id and str(mission_id).startswith("msn_")
    mission_path = tmp_path / "server" / "var" / "missions" / f"{mission_id}.json"
    assert mission_path.is_file(), "durable mission record missing"
    record = json.loads(mission_path.read_text(encoding="utf-8"))
    assert record["status"] == "running"
    assert (record.get("plan") or {}).get("provenance") == "pursuit_native_dispatch"
    assert (record.get("plan") or {}).get("runtime") == "native"


def test_claim_execute_artifact_protected_verify_path(tmp_path: Path) -> None:
    """Prove server task → claim → real execute → immutable CAS → protected verify."""
    root = tmp_path / "server"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    input_path = workspace / "contacts.txt"
    input_path.write_text(
        "V1.7 mission-path proof input.\n"
        "Reach alice@example.com and bob@example.com for verification.\n",
        encoding="utf-8",
    )
    artifact_bytes = _real_extract_bytes(input_path)
    digest = hashlib.sha256(artifact_bytes).hexdigest()
    required_checks = {
        "email_count": 2,
        "artifact_sha256": digest,
        "placement": "server_verified",
        "host_role": "protected_verifier",
        "runtime": "swarm_kernel",
    }

    client = _client(root)
    mission_id = new_id("msn_v17path_")
    mission = sample_mission().model_copy(
        update={
            "id": mission_id,
            "project_id": "proj_review",
            "objective": "Extract contacts for protected verify",
            "status": MissionStatus.DRAFT,
        }
    )
    created = client.post(
        "/v1/missions",
        headers=HEADERS,
        json={
            "mission": mission.model_dump(mode="json"),
            "task_family": "extract",
            "required_checks": required_checks,
        },
    )
    assert created.status_code == 200, created.text
    assert created.json()["mission"]["id"] == mission_id

    enroll = client.post(
        "/v1/workers/enroll",
        headers=HEADERS,
        json={
            "project_id": "proj_review",
            "capabilities": ["extract", "workspace.read"],
            "privacy_classes": ["local"],
            "platform": "linux",
            "architecture": "x86_64",
        },
    )
    assert enroll.status_code == 200, enroll.text
    worker = enroll.json()["worker"]
    worker_id = worker["worker_id"]
    generation = worker["lease_generation"]
    token = enroll.json()["membership_token"]

    task = sample_task(mission_id=mission_id).model_copy(
        update={
            "id": new_id("tsk_"),
            "project_id": "proj_review",
            "task_family": "extract",
            "objective": "extract contacts from workspace input",
            "required_capabilities": ["extract"],
            "scopes": ["local"],
            "inputs": {"input_path": str(input_path)},
        }
    )
    enq = client.post(
        "/v1/workers/enqueue",
        headers={**HEADERS, "Idempotency-Key": f"enq-{task.id}"},
        json={"task": task.model_dump(mode="json")},
    )
    assert enq.status_code == 200, enq.text

    claim = client.post(
        "/v1/workers/claim",
        headers=HEADERS,
        json={"worker_id": worker_id, "generation": generation, "token": token},
    )
    assert claim.status_code == 200, claim.text
    claimed = claim.json()
    assert claimed["claimed"] is True
    lease_id = claimed["lease_id"]
    assert claimed["task"]["id"] == task.id

    # Actual execution (not fixture echo): re-run extract on claimed input.
    claimed_input = Path(str((claimed["task"].get("inputs") or {}).get("input_path")))
    assert claimed_input.is_file()
    executed = _real_extract_bytes(claimed_input)
    assert executed == artifact_bytes
    assert b"echo" not in executed
    assert b"fixture_demo" not in executed

    published = client.post(
        f"/v1/missions/{mission_id}/artifacts",
        headers=HEADERS,
        json={
            "kind": "result",
            "content_base64": base64.b64encode(executed).decode(),
            "media_type": "application/json",
            "summary": "real_extract_result",
        },
    )
    assert published.status_code == 200, published.text
    artifact = published.json()["artifact"]
    assert artifact["content_hash"] == digest
    artifact_id = artifact["artifact_id"]

    # Cold reopen: immutable CAS still resolves.
    cold = _client(root)
    content = cold.get(
        f"/v1/missions/{mission_id}/artifacts/{artifact_id}/content",
        headers=HEADERS,
    )
    assert content.status_code == 200, content.text
    assert content.json()["content_hash"] == digest
    raw = base64.b64decode(content.json()["content_base64"])
    assert raw == executed

    submit = client.post(
        "/v1/workers/submit-result",
        headers={**HEADERS, "Idempotency-Key": f"sub-{lease_id}"},
        json={
            "lease_id": lease_id,
            "worker_id": worker_id,
            "generation": generation,
            "token": token,
            "status": "completed",
            # Worker lies — protected verify must ignore these claims.
            "checks": {"email_count": 99, "artifact_sha256": "forged"},
            "artifact_manifest": {
                "kind": "result",
                "artifact_id": artifact_id,
                "content_hash": digest,
                "mode": "real_execution",
            },
            "summary": "worker_submit_pending_accept",
        },
    )
    assert submit.status_code == 200, submit.text
    submitted = submit.json()
    assert submitted["acceptance_state"] == "pending"
    assert submitted.get("self_accepted") is False

    review = client.post(
        f"/v1/missions/{mission_id}/review",
        headers=HEADERS,
        json={"produced": {"checks": {"email_count": 99, "artifact_sha256": "forged"}}},
    )
    assert review.status_code == 200, review.text
    body = review.json()
    assert body["accepted"] is True
    assert body["mission"]["status"] == "completed"
    assert body["mission"]["acceptance_receipt_id"]
    assert body["mission"]["acceptance_receipt_id"].startswith("acr_")

    record = json.loads(
        (root / "var" / "missions" / f"{mission_id}.json").read_text(encoding="utf-8")
    )
    protected = (record.get("validation") or {}).get("protected_verify") or {}
    assert protected.get("accepted") is True
    assert protected.get("content_hash") == digest
    assert protected.get("authority") == "server_protected_verifier"
    assert (record.get("result") or {}).get("acceptance_receipt_id")


def test_pursuit_engine_default_is_not_recording_success(tmp_path: Path) -> None:
    """Bare PursuitEngine must not default to successful RecordingExecutor (R20-01)."""
    from swarm.goals.models import Goal, GoalStatus, GoalStore
    from swarm.pursuit import BlockedMissingImplementationExecutor, PursuitEngine

    goals = GoalStore(tmp_path / "goals")
    goal = goals.create(
        Goal(
            project_id="proj_review",
            desired_outcome="Must not false-achieve",
            verification_criteria=["c1"],
            resource_envelope={"spend_usd_ceiling": 0.0},
            authority_envelope={"tools": ["workspace.read"], "providers": ["fake"]},
        )
    )
    engine = PursuitEngine(goals)
    assert isinstance(engine.executor, BlockedMissingImplementationExecutor)
    cycle = engine.tick(goal.id, force=True)
    assert cycle.outcome is not None
    assert cycle.outcome.success is False
    assert cycle.outcome.failure_class == "blocked_missing_implementation"
    assert goals.get(goal.id).status != GoalStatus.ACHIEVED

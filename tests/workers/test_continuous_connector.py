"""V1.7 continuous connector claim/lease/submit — no self-accept, no spend."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from swarm.api.app import create_app
from swarm.contracts.common import new_id
from swarm.contracts.fixtures import sample_task
from swarm.contracts.workspace import WorkerLease
from swarm.workers.continuous_connector import ContinuousMacConnector, default_mac_executor
from swarm.workers.registry import WorkerRegistryService

HEADERS = {"Authorization": "Bearer test-token"}


def _app(tmp_path: Path) -> TestClient:
    app = create_app(
        require_auth=True,
        seed_loopback_token="test-token",
        seed_fixtures=False,
        db_reachable=True,
        repo_root=tmp_path,
        install_project_id="proj_review",
    )
    return TestClient(app)


@pytest.mark.asyncio
async def test_claim_renew_submit_no_self_accept() -> None:
    reg = WorkerRegistryService(lease_ttl_seconds=30)
    token = new_id("wt_")
    lease = await reg.register(
        WorkerLease(
            node_identity="mac-1",
            architecture="arm64",
            runtime_version="0.1.0",
            capacity_units=1.0,
            capabilities=["mac.local.extract", "extract"],
            labels=["mac"],
        ),
        token=token,
        project_id="proj_a",
    )
    reg._workers[lease.worker_id].privacy_classes = {"mac_local", "local"}
    task = sample_task().model_copy(
        update={
            "id": new_id("tsk_"),
            "required_capabilities": ["extract"],
            "scopes": ["mac_local"],
        }
    )
    reg.enqueue(task)
    claimed = await reg.claim_work(lease.worker_id, token=token)
    assert claimed.claimed and claimed.lease is not None
    renewed = reg.renew_lease(
        lease_id=claimed.lease.lease_id,
        worker_id=lease.worker_id,
        generation=lease.lease_generation,
        token=token,
    )
    assert renewed.state == "renewed"
    submitted = reg.submit_result(
        lease_id=claimed.lease.lease_id,
        worker_id=lease.worker_id,
        generation=lease.lease_generation,
        token=token,
        status="completed",
        checks={"email_count": 2},
    )
    assert submitted["acceptance_state"] == "pending"
    assert reg._results[submitted["result_id"]]["acceptance_state"] == "pending"
    accepted = reg.control_plane_accept_result(submitted["result_id"], accepted=True)
    assert accepted["acceptance_state"] == "accepted"


def test_http_claim_lease_loop(tmp_path: Path) -> None:
    client = _app(tmp_path)
    enroll = client.post(
        "/v1/workers/enroll",
        headers=HEADERS,
        json={
            "project_id": "proj_review",
            "capabilities": ["mac.local.extract", "extract"],
            "privacy_classes": ["mac_local", "local"],
        },
    )
    assert enroll.status_code == 200, enroll.text
    body = enroll.json()
    worker_id = body["worker"]["worker_id"]
    generation = body["worker"]["lease_generation"]
    token = body["membership_token"]

    task = sample_task(mission_id="msn_cont").model_copy(
        update={
            "id": new_id("tsk_"),
            "project_id": "proj_review",
            "required_capabilities": ["extract"],
            "scopes": ["mac_local"],
        }
    )
    enq = client.post(
        "/v1/workers/enqueue",
        headers={**HEADERS, "Idempotency-Key": "enq-1"},
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

    renew = client.post(
        "/v1/workers/renew",
        headers=HEADERS,
        json={
            "lease_id": lease_id,
            "worker_id": worker_id,
            "generation": generation,
            "token": token,
        },
    )
    assert renew.status_code == 200, renew.text

    submit = client.post(
        "/v1/workers/submit-result",
        headers={**HEADERS, "Idempotency-Key": "sub-1"},
        json={
            "lease_id": lease_id,
            "worker_id": worker_id,
            "generation": generation,
            "token": token,
            "status": "completed",
            "checks": {"email_count": 2},
        },
    )
    assert submit.status_code == 200, submit.text
    submitted = submit.json()
    assert submitted["acceptance_state"] == "pending"
    assert submitted["self_accepted"] is False

    empty = client.post(
        "/v1/workers/claim",
        headers=HEADERS,
        json={"worker_id": worker_id, "generation": generation, "token": token},
    )
    assert empty.json()["claimed"] is False

    cancel = client.post(
        "/v1/workers/enqueue",
        headers={**HEADERS, "Idempotency-Key": "enq-2"},
        json={
            "task": task.model_copy(update={"id": new_id("tsk_")}).model_dump(mode="json")
        },
    )
    assert cancel.status_code == 200
    claim2 = client.post(
        "/v1/workers/claim",
        headers=HEADERS,
        json={"worker_id": worker_id, "generation": generation, "token": token},
    )
    assert claim2.json()["claimed"] is True
    cancelled = client.post(
        "/v1/workers/cancel-lease",
        headers=HEADERS,
        json={"lease_id": claim2.json()["lease_id"], "reason": "test_cancel"},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["state"] == "cancelled"

    recon = client.post(
        "/v1/workers/reconnect",
        headers=HEADERS,
        json={"worker_id": worker_id, "generation": generation, "token": token},
    )
    assert recon.status_code == 200, recon.text


def test_cancel_blocks_submit(tmp_path: Path) -> None:
    client = _app(tmp_path)
    enroll = client.post(
        "/v1/workers/enroll",
        headers=HEADERS,
        json={
            "project_id": "proj_review",
            "capabilities": ["extract"],
            "privacy_classes": ["mac_local", "local"],
        },
    ).json()
    worker_id = enroll["worker"]["worker_id"]
    generation = enroll["worker"]["lease_generation"]
    token = enroll["membership_token"]
    task = sample_task().model_copy(
        update={
            "id": new_id("tsk_"),
            "project_id": "proj_review",
            "required_capabilities": ["extract"],
            "scopes": ["mac_local"],
        }
    )
    client.post(
        "/v1/workers/enqueue",
        headers={**HEADERS, "Idempotency-Key": "enq-c"},
        json={"task": task.model_dump(mode="json")},
    )
    lease_id = client.post(
        "/v1/workers/claim",
        headers=HEADERS,
        json={"worker_id": worker_id, "generation": generation, "token": token},
    ).json()["lease_id"]
    client.post(
        "/v1/workers/cancel-lease",
        headers=HEADERS,
        json={"lease_id": lease_id, "reason": "operator_cancel"},
    )
    submit = client.post(
        "/v1/workers/submit-result",
        headers=HEADERS,
        json={
            "lease_id": lease_id,
            "worker_id": worker_id,
            "generation": generation,
            "token": token,
            "status": "completed",
        },
    )
    assert submit.status_code == 409


def test_leases_survive_app_reconstruction(tmp_path: Path) -> None:
    """R2: queued work + lease state must survive cold API reconstruction."""
    root = tmp_path / "server"
    client = _app(root)
    enroll = client.post(
        "/v1/workers/enroll",
        headers=HEADERS,
        json={
            "project_id": "proj_review",
            "capabilities": ["extract"],
            "privacy_classes": ["mac_local", "local"],
        },
    )
    assert enroll.status_code == 200, enroll.text
    body = enroll.json()
    worker_id = body["worker"]["worker_id"]
    generation = body["worker"]["lease_generation"]
    token = body["membership_token"]
    task = sample_task().model_copy(
        update={
            "id": new_id("tsk_"),
            "project_id": "proj_review",
            "required_capabilities": ["extract"],
            "scopes": ["mac_local"],
        }
    )
    assert (
        client.post(
            "/v1/workers/enqueue",
            headers={**HEADERS, "Idempotency-Key": "enq-dur"},
            json={"task": task.model_dump(mode="json")},
        ).status_code
        == 200
    )
    cold = _app(root)
    claim = cold.post(
        "/v1/workers/claim",
        headers=HEADERS,
        json={"worker_id": worker_id, "generation": generation, "token": token},
    )
    assert claim.status_code == 200, claim.text
    assert claim.json()["claimed"] is True
    recon = cold.post(
        "/v1/workers/reconnect",
        headers=HEADERS,
        json={"worker_id": worker_id, "generation": generation, "token": token},
    )
    assert recon.status_code == 200
    assert len(recon.json()["active_leases"]) == 1


def test_continuous_config_and_executor(tmp_path: Path) -> None:
    claim = {
        "task": {
            "id": "tsk_x",
            "scopes": ["mac_local"],
            "required_capabilities": ["mac.local.extract"],
        }
    }
    produced = default_mac_executor(claim, tmp_path / "fx")
    assert produced["checks"]["placement"] == "mac_local"
    assert produced["usage"]["spend_usd"] == 0.0
    connector = ContinuousMacConnector(
        max_iterations=3,
        fixture_dir=tmp_path / "fx",
        evidence_dir=tmp_path / "ev",
        poll_interval_seconds=0.01,
    )
    assert connector.max_iterations == 3
    assert connector.poll_interval_seconds == 0.01

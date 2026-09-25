"""TH-03 Mac connector unit tests — local, no spend."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.contracts.common import new_id
from swarm.contracts.fixtures import sample_task
from swarm.contracts.workspace import WorkerLease
from swarm.workers.mac_connector import perform_mac_local_extract, write_mac_local_fixture
from swarm.workers.registry import WorkerRegistryService


def _lease(**kwargs: object) -> WorkerLease:
    base: dict[str, object] = {
        "node_identity": "mac-1",
        "architecture": "arm64",
        "runtime_version": "0.1.0",
        "capacity_units": 1.0,
        "capabilities": ["mac.local.extract", "extract"],
        "labels": ["mac"],
    }
    base.update(kwargs)
    return WorkerLease(**base)  # type: ignore[arg-type]


def test_mac_local_extract_deterministic(tmp_path: Path) -> None:
    path = write_mac_local_fixture(tmp_path, run_id="abc123")
    first = perform_mac_local_extract(path)
    second = perform_mac_local_extract(path)
    assert first.email_count == 2
    assert first.artifact_sha256 == second.artifact_sha256
    assert first.required_checks()["placement"] == "mac_local"
    assert first.required_checks()["host_role"] == "mac_connector"


@pytest.mark.asyncio
async def test_mac_local_scope_requires_mac_privacy() -> None:
    reg = WorkerRegistryService()
    cloud_token = new_id("wt_")
    mac_token = new_id("wt_")
    cloud = await reg.register(
        _lease(capabilities=["extract"], node_identity="cloud-1"),
        token=cloud_token,
        project_id="proj_a",
    )
    # Default privacy is {"local"} only — not mac_local.
    assert "mac_local" not in reg._workers[cloud.worker_id].privacy_classes

    task = sample_task().model_copy(
        update={
            "id": new_id("tsk_"),
            "required_capabilities": ["extract"],
            "scopes": ["mac_local"],
        }
    )
    reg.enqueue(task)
    claimed = await reg.claim_dispatch(cloud.worker_id, token=cloud_token)
    assert claimed is None  # blocked without mac_local privacy

    mac = await reg.register(
        _lease(node_identity="mac-1"),
        token=mac_token,
        project_id="proj_a",
    )
    reg._workers[mac.worker_id].privacy_classes = {"mac_local", "local"}
    reg.enqueue(task)
    claimed_mac = await reg.claim_dispatch(mac.worker_id, token=mac_token)
    assert claimed_mac is not None
    assert claimed_mac.id == task.id

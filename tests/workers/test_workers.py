"""P12 worker membership and recovery tests."""

from __future__ import annotations

from datetime import timedelta

import pytest

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import WorkerStatus
from swarm.contracts.fixtures import sample_task
from swarm.contracts.workspace import WorkerLease
from swarm.workers.registry import (
    StaleGenerationError,
    WorkerAuthError,
    WorkerRegistryService,
    worker_self_test,
)


def _lease(**kwargs: object) -> WorkerLease:
    base: dict[str, object] = {
        "node_identity": "node-1",
        "architecture": "arm64",
        "runtime_version": "0.1.0",
        "capacity_units": 1.0,
        "capabilities": ["chat", "tools"],
        "labels": ["local"],
    }
    base.update(kwargs)
    return WorkerLease(**base)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_join_leave_changes_capacity() -> None:
    reg = WorkerRegistryService()
    t1 = new_id("wt_")
    t2 = new_id("wt_")
    w1 = await reg.register(_lease(capacity_units=2.0), token=t1)
    await reg.register(_lease(capacity_units=3.0, node_identity="node-2"), token=t2)
    assert reg.total_capacity() == 5.0
    await reg.drain(w1.worker_id, token=t1)
    reg.complete_current(w1.worker_id)
    assert reg.total_capacity() == 3.0


@pytest.mark.asyncio
async def test_stale_results_rejected() -> None:
    reg = WorkerRegistryService()
    token = new_id("wt_")
    w = await reg.register(_lease(capabilities=["chat", "tools"]), token=token)
    task = sample_task().model_copy(update={"required_capabilities": ["chat"]})
    reg.enqueue(task)
    claimed = await reg.claim_dispatch(w.worker_id, token=token)
    assert claimed is not None
    await reg.revoke_generation(w.worker_id)
    with pytest.raises(StaleGenerationError):
        reg.accept_result(w.worker_id, lease_generation=1, task_id=task.id)


@pytest.mark.asyncio
async def test_revoked_token_cannot_claim() -> None:
    reg = WorkerRegistryService()
    token = new_id("wt_")
    w = await reg.register(_lease(), token=token)
    await reg.revoke_generation(w.worker_id)
    with pytest.raises(WorkerAuthError):
        await reg.claim_dispatch(w.worker_id, token=token)


@pytest.mark.asyncio
async def test_drain_completes_then_exits() -> None:
    reg = WorkerRegistryService()
    token = new_id("wt_")
    w = await reg.register(_lease(capabilities=["chat"]), token=token)
    reg.enqueue(sample_task().model_copy(update={"required_capabilities": ["chat"]}))
    claimed = await reg.claim_dispatch(w.worker_id, token=token)
    assert claimed is not None
    drained = await reg.drain(w.worker_id, token=token)
    assert drained.status == WorkerStatus.DRAINING
    reg.complete_current(w.worker_id)
    assert reg._workers[w.worker_id].lease.status == WorkerStatus.OFFLINE  # noqa: SLF001


@pytest.mark.asyncio
async def test_local_only_never_to_cloud() -> None:
    reg = WorkerRegistryService()
    token = new_id("wt_")
    w = await reg.register(_lease(capabilities=["chat"]), token=token)
    reg._workers[w.worker_id].privacy_classes = {"cloud"}  # noqa: SLF001
    task = sample_task().model_copy(
        update={"required_capabilities": ["chat"], "scopes": ["local_only", "scope_repo_demo"]}
    )
    reg.enqueue(task)
    claimed = await reg.claim_dispatch(w.worker_id, token=token)
    assert claimed is None


@pytest.mark.asyncio
async def test_capability_mismatch_blocks_dispatch() -> None:
    reg = WorkerRegistryService()
    token = new_id("wt_")
    w = await reg.register(_lease(capabilities=["chat"]), token=token)
    reg.enqueue(sample_task().model_copy(update={"required_capabilities": ["vision.ocr"]}))
    assert await reg.claim_dispatch(w.worker_id, token=token) is None


@pytest.mark.asyncio
async def test_lost_heartbeat_is_suspicion() -> None:
    reg = WorkerRegistryService(heartbeat_ttl_seconds=0)
    token = new_id("wt_")
    w = await reg.register(_lease(), token=token)
    reg._workers[w.worker_id].last_heartbeat = utc_now() - timedelta(seconds=5)  # noqa: SLF001
    status = reg.suspect_lost_heartbeat(w.worker_id)
    assert status.startswith("suspect")


def test_worker_self_test_mock() -> None:
    result = worker_self_test(mode="mock")
    assert result["ok"] is True
    assert result["mock_vs_live"] == "membership_only_no_provider_secrets"

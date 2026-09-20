"""PydanticAI + DBOS compatibility spike tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from swarm.api.app import create_app
from swarm.spike.broker_hook import (
    SpikeDeps,
    build_spike_agent,
    make_default_broker,
    run_with_broker,
)
from swarm.spike.durable_agent import DurableSpikeHarness, run_dual_route_spike


@pytest.mark.asyncio
async def test_brokered_agent_two_routes() -> None:
    broker, alpha, beta = make_default_broker()
    for route in (alpha, beta):
        agent = build_spike_agent(route)
        deps = SpikeDeps(
            broker=broker,
            route_id=route.route_id,
            runtime_client={"secret": "MUST_NOT_SERIALIZE"},
            secret_ref_name="FAKE_API_KEY",
        )
        answer = await run_with_broker(agent, f"hello {route.route_id}", deps)
        assert answer.route_id == route.route_id
        assert answer.echo_count == 1
    assert broker.request_count == 2
    broker.assert_all_calls_accounted()


@pytest.mark.asyncio
async def test_dual_route_dbos_spike(tmp_path: Path) -> None:
    db = tmp_path / "spike.sqlite"
    result = await run_dual_route_spike(db)
    assert result["alpha"]["answer"]["route_id"] == "rt_fake_alpha"
    assert result["beta"]["answer"]["route_id"] == "rt_fake_beta"
    assert result["total_broker_requests"] == 2
    assert "runtime_client" not in result["alpha"]["checkpoint"]


@pytest.mark.asyncio
async def test_completed_step_not_reissued_semantics(tmp_path: Path) -> None:
    """Documented pending-work behavior for crash after completed durable step.

    Completed DBOS steps are not re-executed on recovery. Broker request_count in this
    spike is process-local; after crash+restart with a fresh harness process memory
    resets, while the durable step marker must remain stable when SWARM_SPIKE_CRASH is off.
    """
    db = tmp_path / "crash.sqlite"
    harness = DurableSpikeHarness(db)
    harness.launch()
    try:
        out = await harness.spike_workflow_with_step(harness.route_alpha.route_id, "stable")
        assert out["marker"] == "completed:rt_fake_alpha"
        assert out["answer"]["route_id"] == "rt_fake_alpha"
        first_count = harness.broker.request_count
        # Second run without crash still accounts a new logical call (new admission).
        out2 = await harness.spike_workflow_with_step(harness.route_alpha.route_id, "again")
        assert out2["marker"] == "completed:rt_fake_alpha"
        assert harness.broker.request_count == first_count + 1
    finally:
        harness.destroy()

    # Induced crash path: workflow fails after completed step marker.
    harness2 = DurableSpikeHarness(db)
    harness2.launch()
    try:
        os.environ["SWARM_SPIKE_CRASH"] = "1"
        with pytest.raises(RuntimeError, match="induced_crash"):
            await harness2.spike_workflow_with_step(harness2.route_alpha.route_id, "crashme")
    finally:
        os.environ.pop("SWARM_SPIKE_CRASH", None)
        harness2.destroy()


def test_health_endpoints_smoke() -> None:
    client = TestClient(create_app(seed_loopback_token="atk_loopback_demo", seed_fixtures=True))
    live = client.get("/health/live")
    ready = client.get("/health/ready")
    assert live.status_code == 200
    assert live.json()["status"] == "ok"
    assert ready.status_code == 200
    assert ready.json()["execution_mode"] == "mock"

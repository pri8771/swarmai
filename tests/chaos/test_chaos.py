"""P18 chaos / fault-injection tests (offline mock)."""

from __future__ import annotations

import pytest

from swarm.chaos.faults import run_fault_matrix


@pytest.mark.asyncio
async def test_fault_matrix_all_pass() -> None:
    report = await run_fault_matrix()
    assert report["mode"] == "mock"
    assert report["mock_vs_live"] == "simulated_chaos_not_live"
    assert report["all_passed"] is True
    assert report["critical_stop_release"] is False
    names = {r["name"] for r in report["results"]}
    assert names >= {
        "uncertain_sent_request",
        "stale_worker",
        "outbox_gap",
        "cloud_recovery_fence",
    }

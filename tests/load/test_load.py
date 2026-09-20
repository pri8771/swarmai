"""P18 load scenario tests (offline mock)."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.load.metrics import percentile
from swarm.load.scenarios import LoadConfig, compare_strategies, run_load_scenario


def test_percentile() -> None:
    assert percentile([], 50) is None
    assert percentile([10.0], 50) == 10.0
    assert percentile([1.0, 2.0, 3.0, 4.0], 50) is not None


@pytest.mark.asyncio
async def test_adaptive_load_expand_contract(tmp_path: Path) -> None:
    report = await run_load_scenario(
        LoadConfig(
            scenario="adaptive",
            mode="mock",
            logical_sessions=100,
            queued_tasks=200,  # keep unit test fast; CLI soak uses 1000
            actual_concurrency=4,
            simulated_provider_concurrency=8,
            missions=2,
        ),
        report_dir=tmp_path,
    )
    assert report.mode == "mock"
    assert report.mock_vs_live == "simulated_load_not_live"
    assert report.report_hash
    assert report.gates["no_oversubscription"]
    assert report.gates["expand_and_contract_observed"]
    assert report.gates["no_starvation"]
    assert report.metrics["logical_sessions"] == 100
    assert report.metrics["max_in_flight"] <= 4
    assert (tmp_path / f"{report.run_id}.json").exists()


@pytest.mark.asyncio
async def test_live_load_blocked() -> None:
    with pytest.raises(PermissionError, match="live_load_blocked"):
        await run_load_scenario(LoadConfig(mode="live", queued_tasks=10))


@pytest.mark.asyncio
async def test_fixed_vs_adaptive_same_envelope(tmp_path: Path) -> None:
    cmp = await compare_strategies(
        queued_tasks=80,
        logical_sessions=10,
        actual_concurrency=4,
        report_dir=tmp_path,
    )
    assert cmp["same_envelope"] is True
    assert cmp["mock_vs_live"] == "simulated_load_not_live"
    assert cmp["fixed"]["scenario"] == "fixed"
    assert cmp["adaptive"]["scenario"] == "adaptive"

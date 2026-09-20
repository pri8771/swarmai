"""End-to-end dynamic swarm demo tests (mock mode, no keys)."""

from __future__ import annotations

from pathlib import Path

import pytest
from examples.dynamic_demo.run_demo import run_parser_issue_demo


@pytest.mark.asyncio
async def test_parser_issue_demo_mock(tmp_path: Path) -> None:
    report = await run_parser_issue_demo(mode="mock", report_dir=tmp_path / "report")
    assert report.mode == "mock"
    assert "fake_models_only" in report.mock_vs_live
    assert report.expansions >= 2
    assert report.contractions >= 1
    assert set(report.planners) == {"as_planner_a", "as_planner_b"}
    assert report.concurrent_mission_id is not None
    assert "worker_revoked_fenced" in report.faults
    assert report.test_results["baseline"]["passed"] is False
    assert report.test_results["wrong_patch"]["passed"] is False
    assert report.test_results["correct_patch"]["passed"] is True
    assert report.acceptance["accepted"] is True
    assert (tmp_path / "report" / "demo-report.json").exists()
    assert (tmp_path / "report" / "ACCEPTANCE.md").exists()


@pytest.mark.asyncio
async def test_live_mode_blocked_without_qualification(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="live mode"):
        await run_parser_issue_demo(mode="live", report_dir=tmp_path / "live")

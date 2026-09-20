"""P16 mock qualification tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.evals.qualify import (
    build_and_save_starter_plan,
    demotion_on_fingerprint_change,
    load_report,
    run_qualification,
)

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "benchmarks" / "starter.jsonl"


def test_mock_plan_and_run_nulls(tmp_path: Path) -> None:
    plan = build_and_save_starter_plan(
        dataset=DATASET,
        purpose="evaluation",
        mode="mock",
        out_dir=tmp_path / "plans",
        max_cases=4,
    )
    assert plan["mode"] == "mock"
    assert "mock" in plan["mock_vs_live"]
    plan_path = tmp_path / "plans" / f"{plan['plan_id']}.json"
    run = run_qualification(
        plan_path,
        mode="mock",
        out_dir=tmp_path / "runs",
        routes=["rt_fake_alpha", "rt_fake_beta"],
    )
    assert run.mode == "mock"
    assert run.mock_vs_live == "simulated_qualification_not_live"
    assert run.report_hash
    # Untested alternate route cells stay null.
    untested = [c for c in run.cells if c.state == "untested"]
    assert untested
    assert all(c.wilson_lower is None for c in untested)
    # Canary/sim does not invent qualified rankings.
    assert all(c.state != "qualified" for c in run.cells)


def test_live_mode_blocked(tmp_path: Path) -> None:
    plan = build_and_save_starter_plan(
        dataset=DATASET,
        purpose="evaluation",
        mode="mock",
        out_dir=tmp_path / "plans",
    )
    plan_path = tmp_path / "plans" / f"{plan['plan_id']}.json"
    with pytest.raises(PermissionError, match="live_qualification_blocked"):
        run_qualification(plan_path, mode="live", out_dir=tmp_path / "runs")


def test_report_load_and_demotion(tmp_path: Path) -> None:
    plan = build_and_save_starter_plan(
        dataset=DATASET,
        purpose="evaluation",
        mode="mock",
        out_dir=tmp_path / "plans",
        max_cases=2,
    )
    plan_path = tmp_path / "plans" / f"{plan['plan_id']}.json"
    run = run_qualification(plan_path, mode="mock", out_dir=tmp_path / "runs")
    loaded = load_report(run.run_id, tmp_path / "runs")
    assert loaded["run_id"] == run.run_id
    assert loaded["mock_vs_live"] == "simulated_qualification_not_live"
    demoted = demotion_on_fingerprint_change(loaded, new_fingerprint="fake-alpha-v2.0")
    assert any(c["state"] == "stale_recheck_required" for c in demoted["cells"])

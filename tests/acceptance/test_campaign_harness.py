"""Tests for V2.0 acceptance campaign harness and matrices."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.acceptance.freeze import load_freeze
from swarm.acceptance.harness import run_acceptance_campaign
from swarm.acceptance.matrix import build_version_matrices
from swarm.evals.synthetic_harness import LiveGateBlocked, LiveGrant


def test_campaign_runs_all_frozen_scenarios(tmp_path: Path) -> None:
    report = run_acceptance_campaign(out_dir=tmp_path)
    assert report.harness_version.startswith("v20-acceptance")
    assert len(report.results) == 12
    assert report.spend_usd == 0.0
    assert report.version_claim["any_version_accepted"] is False
    assert report.to_dict()["any_version_accepted"] is False
    assert all(r.version_accepted is False for r in report.results)
    assert report.report_hash
    assert (tmp_path / "latest.json").is_file()


def test_deterministic_probes_pass_or_scaffold() -> None:
    report = run_acceptance_campaign(gates=["deterministic"])
    det = [r for r in report.results if r.primary_gate == "deterministic"]
    assert det
    for r in det:
        assert r.ok, (r.scenario_id, r.status, r.detail)
        assert r.status in {
            "pass_deterministic",
            "scaffold_ready_not_integrated",
            "pass_deterministic_gate_only",
        }


def test_live_primary_blocked_without_grant() -> None:
    report = run_acceptance_campaign(gates=["live"])
    live = [r for r in report.results if r.primary_gate == "live"]
    assert len(live) == 1
    assert live[0].scenario_id == "V20-S12"
    assert live[0].status == "blocked_live_grant"
    assert live[0].ok is True
    assert live[0].detail["live_gate"]["invented"] is False
    # Deterministic side of live gate still ran.
    assert live[0].detail["deterministic_side"]["ok"] is True


def test_invent_live_grant_hard_refused() -> None:
    with pytest.raises(LiveGateBlocked, match="invent_live_grant"):
        run_acceptance_campaign(invent_live_grant=True)


def test_approved_grant_still_no_auto_dispatch_spend() -> None:
    grant = LiveGrant(
        grant_id="op_real_not_invented",
        routes=("rt_free",),
        budget_usd=0.0,
        purpose="operator_supplied_test",
        approved=True,
        free_routes_only=True,
        max_calls=1,
        max_tokens=100,
        max_wall_seconds=30,
    )
    report = run_acceptance_campaign(live_grant=grant, gates=["live"])
    assert report.spend_usd == 0.0
    live = next(r for r in report.results if r.scenario_id == "V20-S12")
    assert live.status == "blocked_live_grant"
    assert "auto live dispatch" in live.detail["note"].lower() or "refuses" in live.detail["note"]


def test_host_also_gate_recorded_blocked() -> None:
    report = run_acceptance_campaign()
    s07 = next(r for r in report.results if r.scenario_id == "V20-S07")
    assert "host" in s07.detail["also_gates"]
    assert s07.detail["also_gates"]["host"]["status"] == "blocked_host_gate"


def test_elapsed_also_gate_not_simulated() -> None:
    report = run_acceptance_campaign()
    s03 = next(r for r in report.results if r.scenario_id == "V20-S03")
    assert s03.detail["also_gates"]["elapsed"]["simulate_elapsed_time"] is False
    assert s03.detail["also_gates"]["elapsed"]["status"] == "blocked_elapsed_window"


def test_matrices_never_accepted() -> None:
    freeze = load_freeze()
    campaign = run_acceptance_campaign()
    matrices = build_version_matrices(freeze=freeze, campaign=campaign)
    assert matrices["any_version_accepted"] is False
    for ver, row in matrices["versions"].items():
        assert row["accepted"] is False, ver
        assert row["readiness"] != "accepted"
    assert "V1.7" in matrices["versions"]
    assert "V2.0" in matrices["versions"]
    assert matrices["versions"]["V2.0"]["readiness"].startswith("harness_")

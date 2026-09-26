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


def test_deterministic_probes_pass() -> None:
    report = run_acceptance_campaign(gates=["deterministic"])
    det = [r for r in report.results if r.primary_gate == "deterministic"]
    assert det
    for r in det:
        assert r.ok, (r.scenario_id, r.status, r.detail)
        assert r.status in {
            "pass_deterministic",
            "pass_deterministic_gate_only",
        }, (r.scenario_id, r.status)
    # S05–S08/S11 must be real product probes, not scaffolds.
    for sid in ("V20-S05", "V20-S06", "V20-S07", "V20-S08", "V20-S11"):
        row = next(r for r in report.results if r.scenario_id == sid)
        assert row.status == "pass_deterministic", (sid, row.status, row.detail)
        assert "scaffold" not in str(row.detail.get("status", "")).lower()


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


def test_approved_grant_not_false_blocked_live_grant() -> None:
    """Approved grant must not be reported as blocked_live_grant (auth vs impl)."""
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
    assert live.status == "blocked_missing_implementation", live.status
    assert live.status != "blocked_live_grant"
    assert live.detail["blocker_class"] == "implementation"
    assert live.detail["live_gate"]["grant_approved"] is True
    assert live.detail["fake_upstream_wiring"]["ok"] is True
    assert live.detail["fake_upstream_wiring"]["spend_usd"] == 0.0
    assert live.detail["live_dispatch"] is False


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


def test_missing_grant_still_blocked_live_grant() -> None:
    """Protected regression: missing auth remains blocked_live_grant."""
    report = run_acceptance_campaign(gates=["live"])
    live = next(r for r in report.results if r.scenario_id == "V20-S12")
    assert live.status == "blocked_live_grant"
    assert live.detail["blocker_class"] == "authorization"
    assert live.detail["live_gate"]["grant_present"] is False


def test_approved_grant_fake_upstream_wiring_before_live() -> None:
    """Protected regression: approved grant → fake-upstream first, not false auth block."""
    grant = LiveGrant(
        grant_id="op_wiring_test",
        routes=("rt_free",),
        budget_usd=0.0,
        purpose="fake_upstream_first",
        approved=True,
        free_routes_only=True,
        max_calls=1,
        max_tokens=100,
        max_wall_seconds=30,
    )
    report = run_acceptance_campaign(live_grant=grant, gates=["live"])
    live = next(r for r in report.results if r.scenario_id == "V20-S12")
    assert live.status == "blocked_missing_implementation"
    wiring = live.detail["fake_upstream_wiring"]
    assert wiring["ok"] is True
    assert wiring["live_dispatch"] is False
    assert wiring["route_id"] == "rt_fake_alpha"
    assert report.spend_usd == 0.0


def test_live_dispatcher_consumes_scoped_grant_without_invent() -> None:
    grant = LiveGrant(
        grant_id="op_dispatch_test",
        routes=("rt_free",),
        budget_usd=0.0,
        purpose="scoped_dispatch",
        approved=True,
        free_routes_only=True,
        max_calls=1,
        max_tokens=100,
        max_wall_seconds=30,
    )

    def _dispatcher(g: LiveGrant, work: Path) -> dict:
        assert g.grant_id == "op_dispatch_test"
        assert g.approved is True
        (work / "receipt.txt").write_text("authentic_receipt\n", encoding="utf-8")
        return {
            "ok": True,
            "status": "pass_fake_upstream_wiring",
            "receipt": "authentic_receipt",
            "spend_usd": 0.0,
        }

    report = run_acceptance_campaign(
        live_grant=grant, gates=["live"], live_dispatcher=_dispatcher
    )
    live = next(r for r in report.results if r.scenario_id == "V20-S12")
    assert live.status == "pass_fake_upstream_wiring"
    assert live.detail["live_dispatch"]["receipt"] == "authentic_receipt"
    assert live.status != "blocked_live_grant"


def test_sdk_ui_parity_probe_restores_swarm_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The probe clears SWARM_* for its fixture app; it must not leak that to the caller."""
    import os

    from swarm.acceptance.probes import probe_sdk_ui_parity

    monkeypatch.setenv("SWARM_DATABASE_URL", "postgresql+psycopg://u:p@127.0.0.1:5432/probe_leak")
    monkeypatch.setenv("SWARM_PROBE_SENTINEL", "keep")
    before = {k: v for k, v in os.environ.items() if k.startswith("SWARM_")}
    result = probe_sdk_ui_parity(tmp_path)
    assert result.ok, (result.status, result.detail)
    after = {k: v for k, v in os.environ.items() if k.startswith("SWARM_")}
    assert after == before

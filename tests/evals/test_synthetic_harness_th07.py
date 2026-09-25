"""TH-07 synthetic evaluation harness tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from swarm.contracts.enums import RoutingState
from swarm.contracts.workspace import EvalResult
from swarm.evals.profiles import ProfileStore
from swarm.evals.synthetic_harness import (
    HARNESS_VERSION,
    LiveGateBlocked,
    LiveGrant,
    assert_live_gate,
    difficulty_for_size,
    fixture_fail_solve,
    oracle_solve,
    prepare_harness_manifest,
    run_synthetic_harness,
    seal_case_answers,
    select_suite_cases,
)
from swarm.evals.dataset import load_dataset

ROOT = Path(__file__).resolve().parents[2]
STARTER = ROOT / "benchmarks" / "starter.jsonl"


def test_difficulty_mapping() -> None:
    assert difficulty_for_size("S") == "easy"
    assert difficulty_for_size("M") == "medium"
    assert difficulty_for_size("L") == "hard"
    assert difficulty_for_size("XL") == "expert"


def test_answers_sealed_from_worker_view() -> None:
    case = next(c for c in load_dataset(STARTER) if c.id == "extraction_S_01")
    visible = seal_case_answers(case)
    blob = json.dumps(visible)
    assert "expected_output" not in blob
    assert "grader" not in blob
    assert "reference_solution" not in blob
    assert "ORD-310-000" in blob  # prompt content still present


def test_oracle_and_fail_fixture_grade() -> None:
    cases = load_dataset(STARTER)
    extraction = next(c for c in cases if c.id == "extraction_S_01")
    assert oracle_solve(extraction) == extraction.expected_output
    bad = fixture_fail_solve(extraction)
    assert bad != extraction.expected_output

    code = next(c for c in cases if c.family == "code_generation" and c.size == "S")
    assert isinstance(oracle_solve(code), str)
    assert "def solve" in oracle_solve(code)


def test_prepare_manifest_independent_of_live() -> None:
    manifest = prepare_harness_manifest(dataset_path=STARTER)
    assert manifest["prepared_independently_of_live_grants"] is True
    assert manifest["live_gate_default"] == "blocked"
    assert manifest["auto_production_routing_changes"] is False
    assert manifest["coverage"]["case_count"] == 128
    assert set(manifest["coverage"]["by_difficulty"]) == {
        "easy",
        "medium",
        "hard",
        "expert",
    }
    assert manifest["coverage"]["by_split"]["holdout"] == 64
    assert manifest["coverage"]["by_split"]["calibration"] == 64
    assert manifest["public_hostname"] == "swarm.splitsignal.ai"


def test_live_gate_blocked_without_grant() -> None:
    with pytest.raises(LiveGateBlocked, match="live_qualification_blocked"):
        assert_live_gate(mode="live", grant=None)
    with pytest.raises(LiveGateBlocked, match="not approved"):
        assert_live_gate(
            mode="live",
            grant=LiveGrant(
                grant_id="g1",
                routes=("rt_x",),
                budget_usd=1.0,
                purpose="eval",
                approved=False,
            ),
        )
    # Unapproved grant still blocks run_synthetic_harness live mode.
    with pytest.raises(LiveGateBlocked):
        run_synthetic_harness(dataset_path=STARTER, mode="live", max_cases=1)


def test_live_gate_with_grant_still_blocks_dispatch() -> None:
    grant = LiveGrant(
        grant_id="g_ok",
        routes=("rt_local",),
        budget_usd=1.0,
        purpose="th07",
        approved=True,
    )
    # Gate check alone may pass; first-cut harness still refuses live dispatch.
    meta = assert_live_gate(mode="live", grant=grant)
    assert meta["grant_present"] is True
    with pytest.raises(LiveGateBlocked, match="not enabled in TH-07"):
        run_synthetic_harness(
            dataset_path=STARTER, mode="live", live_grant=grant, max_cases=1
        )


def test_oracle_run_covers_splits_and_difficulties(tmp_path: Path) -> None:
    report = run_synthetic_harness(
        dataset_path=STARTER,
        mode="oracle",
        max_cases=None,
        out_dir=tmp_path,
        public_hostname="swarm.splitsignal.ai",
    )
    assert report.harness_version == HARNESS_VERSION
    assert report.mock_vs_live == "synthetic_fixture_oracle_not_live"
    assert report.report_hash
    assert len(report.trials) == 128
    assert all(t.correct for t in report.trials)
    assert all(t.sealed and t.leakage_ok for t in report.trials)
    splits = {s.split: s for s in report.split_summaries}
    assert splits["holdout"].passed == 64
    assert splits["calibration"].passed == 64
    difficulties = {t.difficulty for t in report.trials}
    assert difficulties == {"easy", "medium", "hard", "expert"}
    families = {t.family for t in report.trials}
    assert len(families) == 8
    assert report.live_gate["blocked"] is False
    assert report.routing_mutation["auto_production_routing_changes"] is False
    assert report.budget["spend_usd"] == 0
    assert (tmp_path / "latest.json").is_file()


def test_fixture_fail_negative_control() -> None:
    report = run_synthetic_harness(
        dataset_path=STARTER,
        mode="fixture_fail",
        max_cases=16,
    )
    assert len(report.trials) == 16
    assert all(not t.correct for t in report.trials)


def test_no_production_routing_mutation() -> None:
    store = ProfileStore()
    # Seed a provisional production profile.
    store.record_result(
        EvalResult(
            distinct_case_id="prod_c1",
            split="holdout",
            route_fingerprint="rt_prod",
            model_fingerprint="m_prod",
            exact_prompt_hash="h",
            outcome="pass",
            grader_version="1",
            correctness=True,
        ),
        task_family="extraction",
        size_band="S",
    )
    store.record_result(
        EvalResult(
            distinct_case_id="prod_c2",
            split="holdout",
            route_fingerprint="rt_prod",
            model_fingerprint="m_prod",
            exact_prompt_hash="h",
            outcome="pass",
            grader_version="1",
            correctness=True,
        ),
        task_family="extraction",
        size_band="S",
    )
    before = store.summary()
    before_keys = set(store.profiles.keys())
    report = run_synthetic_harness(
        dataset_path=STARTER,
        mode="oracle",
        families=["extraction"],
        difficulties=["easy"],
        max_cases=4,
        production_profile_store=store,
    )
    assert report.routing_mutation["production_profiles_mutated"] is False
    assert set(store.profiles.keys()) == before_keys
    assert store.summary() == before
    # Production profile remains provisional — not auto-promoted.
    assert all(p.routing_state == RoutingState.PROVISIONAL for p in store.profiles.values())
    assert report.routing_mutation["ephemeral_live_profiles"] == 0
    assert report.routing_mutation["ephemeral_simulated_excluded"] >= 1


def test_select_suite_filters() -> None:
    cases = select_suite_cases(
        STARTER,
        families=["extraction", "classification"],
        difficulties=["easy", "expert"],
        splits=["holdout"],
        max_cases=10,
    )
    assert cases
    assert all(c.family in {"extraction", "classification"} for c in cases)
    assert all(c.size in {"S", "XL"} for c in cases)
    assert all(c.split == "holdout" for c in cases)

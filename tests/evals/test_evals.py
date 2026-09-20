"""P06 eval dataset, graders, profiles, and plan tests."""

from __future__ import annotations

import json
from pathlib import Path

from swarm.contracts.enums import RoutingState
from swarm.contracts.mission import SizeFeatures
from swarm.contracts.workspace import EvalResult
from swarm.evals.dataset import assert_no_leakage, build_model_input, load_dataset, validate_dataset
from swarm.evals.graders import grade_case, grade_json_exact, grade_topological_order
from swarm.evals.plan import build_plan, compare_routes
from swarm.evals.profiles import ProfileStore, QualificationPolicy
from swarm.evals.routing import select_routes
from swarm.evals.wilson import wilson_lower_bound

ROOT = Path(__file__).resolve().parents[2]
STARTER = ROOT / "benchmarks" / "starter.jsonl"


def test_validate_starter_dataset() -> None:
    report = validate_dataset(STARTER)
    assert report["ok"] is True
    assert report["case_count"] == 128
    assert "extraction" in report["families"]
    assert set(report["grader_kinds"]) >= {"json_exact", "python_unit", "topological_order"}


def test_model_input_has_no_leakage() -> None:
    cases = load_dataset(STARTER)
    case = next(c for c in cases if c.id == "extraction_S_01")
    model_in = build_model_input(case)
    assert "expected_output" not in json.dumps(model_in)
    assert "grader" not in json.dumps(model_in)
    assert_no_leakage(model_in, case)
    # Mutated wrong output fails
    wrong = grade_json_exact(case, {"records": []})
    assert wrong.correct is False
    # Reference expected passes
    good = grade_json_exact(case, case.expected_output)
    assert good.correct is True


def test_topological_order_accepts_alternate_valid() -> None:
    cases = load_dataset(STARTER)
    case = next(c for c in cases if c.family == "dependency_planning" and c.size == "S")
    nodes = list(case.grader["nodes"])
    edges = list(case.grader["edges"])
    # Build an alternate valid order if the graph allows (linear chain → only one order).
    # For denser graphs use grader acceptance of the expected order and a shuffled invalid.
    ok = grade_topological_order(case, {"order": case.expected_output["order"]})
    assert ok.correct is True
    bad = grade_topological_order(case, {"order": list(reversed(nodes))})
    # Reversed is invalid for chain edges.
    if edges:
        assert bad.correct is False

    # Synthetic diamond: A->C, B->C — both [A,B,C] and [B,A,C] valid.
    from swarm.evals.dataset import BenchmarkCase

    diamond = BenchmarkCase(
        id="dep_diamond",
        family="dependency_planning",
        size="S",
        split="calibration",
        input={"prompt": "x"},
        expected_output={"order": ["A", "B", "C"]},
        grader={
            "kind": "topological_order",
            "nodes": ["A", "B", "C"],
            "edges": [["A", "C"], ["B", "C"]],
        },
    )
    assert grade_topological_order(diamond, {"order": ["A", "B", "C"]}).correct
    assert grade_topological_order(diamond, {"order": ["B", "A", "C"]}).correct
    assert not grade_topological_order(diamond, {"order": ["C", "A", "B"]}).correct


def test_python_unit_correct_and_incorrect_fixtures() -> None:
    cases = load_dataset(STARTER)
    case = next(c for c in cases if c.id == "code_generation_S_01")
    good_code = '''
def solve(rows):
    out = {}
    for r in rows:
        if r.get("status") == "approved":
            out[r["project"]] = out.get(r["project"], 0) + r["amount_cents"]
    return [{"project": k, "total_cents": v} for k, v in sorted(out.items())]
'''
    bad_code = "def solve(rows):\n    return []\n"
    assert grade_case(case, good_code).correct is True
    assert grade_case(case, bad_code).correct is False


def test_wilson_and_sparse_provisional() -> None:
    assert wilson_lower_bound(0, 0) is None
    lb = wilson_lower_bound(2, 2)
    assert lb is not None and 0.0 < lb < 1.0
    store = ProfileStore()
    # One distinct case → unassessed/sparse
    r1 = EvalResult(
        distinct_case_id="c1",
        split="holdout",
        route_fingerprint="rt_a",
        model_fingerprint="m1",
        exact_prompt_hash="h",
        outcome="pass",
        grader_version="1",
        correctness=True,
    )
    p = store.record_result(r1, task_family="extraction", size_band="S", size_features=SizeFeatures())
    assert p.routing_state == RoutingState.UNASSESSED
    r2 = EvalResult(
        distinct_case_id="c2",
        split="holdout",
        route_fingerprint="rt_a",
        model_fingerprint="m1",
        exact_prompt_hash="h",
        outcome="pass",
        grader_version="1",
        correctness=True,
    )
    p2 = store.record_result(r2, task_family="extraction", size_band="S")
    assert p2.routing_state == RoutingState.PROVISIONAL
    # Repeat does not inflate distinct count
    r2b = r2.model_copy()
    p3 = store.record_result(r2b, task_family="extraction", size_band="S")
    assert p3.distinct_case_count == 2
    assert p3.repeated_run_count == 1


def test_policy_quarantine_and_alias_stale() -> None:
    store = ProfileStore()
    for i in range(2):
        store.record_result(
            EvalResult(
                distinct_case_id=f"c{i}",
                split="holdout",
                route_fingerprint="rt_b",
                model_fingerprint="m",
                exact_prompt_hash="h",
                outcome="pass",
                grader_version="1",
                correctness=True,
            ),
            task_family="extraction",
            size_band="S",
        )
    bad = EvalResult(
        distinct_case_id="c_policy",
        split="holdout",
        route_fingerprint="rt_b",
        model_fingerprint="m",
        exact_prompt_hash="h",
        outcome="fail",
        grader_version="1",
        correctness=False,
        policy_violation=True,
    )
    p = store.record_result(bad, task_family="extraction", size_band="S")
    assert p.routing_state == RoutingState.QUARANTINED
    stale = store.mark_alias_stale("rt_b")
    assert stale
    assert store.profiles[stale[0]].routing_state == RoutingState.STALE


def test_simulated_scores_excluded_from_live_tables() -> None:
    store = ProfileStore()
    store.record_result(
        EvalResult(
            distinct_case_id="sim1",
            split="holdout",
            route_fingerprint="rt_sim",
            model_fingerprint="m",
            exact_prompt_hash="h",
            outcome="pass",
            grader_version="1",
            correctness=True,
        ),
        task_family="extraction",
        size_band="S",
        simulated=True,
    )
    assert store.profiles == {}
    assert store.summary()["simulated_excluded"] == 1


def test_eval_plan_mock_bounded() -> None:
    plan = build_plan(STARTER, suite="starter", mode="mock", max_cases=8)
    assert plan.expected_requests == 8
    assert plan.mode == "mock"
    assert "mock" in plan.to_dict()["mock_vs_live"]
    assert len(plan.case_ids) == 8


def test_compare_routes_overhead() -> None:
    cmp = compare_routes(
        direct_tokens=1000,
        direct_quality=0.9,
        small_tokens=400,
        verify_tokens=200,
        small_quality=0.9,
    )
    assert cmp["small_plus_verify"]["tokens"] == 600
    assert cmp["prefer"] in {"direct", "small_plus_verify", "tie_or_context_dependent"}


def test_routing_query() -> None:
    store = ProfileStore(policy=QualificationPolicy())
    for i in range(3):
        store.record_result(
            EvalResult(
                distinct_case_id=f"e{i}",
                split="holdout",
                route_fingerprint="rt_q",
                model_fingerprint="m",
                exact_prompt_hash="h",
                outcome="pass",
                grader_version="1",
                correctness=True,
            ),
            task_family="classification",
            size_band="M",
        )
    rows = select_routes(store, task_family="classification")
    assert rows
    assert rows[0]["routing_state"] == "provisional"


def test_context_compaction_max_chars() -> None:
    cases = load_dataset(STARTER)
    case = next(c for c in cases if c.family == "context_compaction" and c.size == "S")
    # Oversized compact fails even if content matches structurally wrong length.
    huge = {"facts": [{"key": "x", "value": "y" * 500, "source_id": "s"}], "unresolved": []}
    assert grade_json_exact(case, huge).correct is False

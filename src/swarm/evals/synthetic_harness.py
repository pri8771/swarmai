"""TH-07 graded synthetic evaluation harness.

Prepares and runs the starter archive (easy→expert) with sealed answers,
calibration/holdout separation, budget/provenance recording, and a hard live
gate. Fixture/oracle solvers never touch production routing; ProfileStore
mutations are ephemeral and marked simulated.

Live route/budget grants are required before any live dispatch — this module
does not wait on R730/DNS/CF or auto-change production routing.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.mission import SizeFeatures
from swarm.contracts.workspace import EvalResult
from swarm.evals.dataset import (
    BenchmarkCase,
    assert_no_leakage,
    build_model_input,
    load_dataset,
    validate_dataset,
)
from swarm.evals.graders import GradeResult, grade_case
from swarm.evals.plan import EvalPlan, build_plan
from swarm.evals.profiles import ProfileStore, QualificationPolicy
from swarm.evals.wilson import wilson_lower_bound

HARNESS_VERSION = "th07-synthetic-v1"
DATASET_VERSION = "starter-v1"
GRADER_VERSION = "1"

Difficulty = Literal["easy", "medium", "hard", "expert"]
SolverMode = Literal["oracle", "fixture_pass", "fixture_fail", "live"]

SIZE_TO_DIFFICULTY: dict[str, Difficulty] = {
    "S": "easy",
    "M": "medium",
    "L": "hard",
    "XL": "expert",
}

DIFFICULTY_TO_SIZE: dict[Difficulty, str] = {
    "easy": "S",
    "medium": "M",
    "hard": "L",
    "expert": "XL",
}


class LiveGateBlocked(PermissionError):
    """Raised when live mode is requested without an approved grant."""


@dataclass(frozen=True)
class LiveGrant:
    """Explicit operator/route grant required before live dispatch."""

    grant_id: str
    routes: tuple[str, ...]
    budget_usd: float
    purpose: str
    approved: bool = False
    free_routes_only: bool = False
    max_calls: int | None = None
    max_tokens: int | None = None
    max_wall_seconds: int | None = None

    def assert_usable(self) -> None:
        if not self.approved:
            raise LiveGateBlocked(
                "live_qualification_blocked: grant exists but is not approved"
            )
        if not self.routes:
            raise LiveGateBlocked(
                "live_qualification_blocked: grant has no eligible routes"
            )
        # R8: zero-dollar grants allowed only for explicitly free-only routes
        # with independent call/token/time ceilings — never silent paid fallback.
        if self.budget_usd < 0:
            raise LiveGateBlocked(
                "live_qualification_blocked: grant budget_usd must be >= 0"
            )
        for name, value in (
            ("max_calls", self.max_calls),
            ("max_tokens", self.max_tokens),
            ("max_wall_seconds", self.max_wall_seconds),
        ):
            if value is not None and value <= 0:
                raise LiveGateBlocked(
                    f"live_qualification_blocked: grant {name} must be > 0"
                )
        if self.budget_usd == 0:
            if not self.free_routes_only:
                raise LiveGateBlocked(
                    "live_qualification_blocked: zero-dollar grant requires "
                    "free_routes_only=true with verified free routes"
                )
            if not (self.max_calls and self.max_tokens and self.max_wall_seconds):
                raise LiveGateBlocked(
                    "live_qualification_blocked: zero-dollar grant requires "
                    "max_calls, max_tokens, and max_wall_seconds ceilings"
                )


@dataclass
class TrialRecord:
    case_id: str
    family: str
    size: str
    difficulty: Difficulty
    split: str
    solver_mode: str
    correct: bool
    policy_violation: bool
    detail: str
    latency_ms: float
    tokens_estimated: int
    cost_usd: float
    sealed: bool
    leakage_ok: bool
    score_components: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "family": self.family,
            "size": self.size,
            "difficulty": self.difficulty,
            "split": self.split,
            "solver_mode": self.solver_mode,
            "correct": self.correct,
            "policy_violation": self.policy_violation,
            "detail": self.detail,
            "latency_ms": round(self.latency_ms, 3),
            "tokens_estimated": self.tokens_estimated,
            "cost_usd": self.cost_usd,
            "sealed": self.sealed,
            "leakage_ok": self.leakage_ok,
            "score_components": self.score_components,
        }


@dataclass
class SplitSummary:
    split: str
    case_count: int
    passed: int
    failed: int
    pass_rate: float | None
    wilson_lower: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "split": self.split,
            "case_count": self.case_count,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": self.pass_rate,
            "wilson_lower": self.wilson_lower,
        }


@dataclass
class SyntheticHarnessReport:
    run_id: str
    harness_version: str
    dataset_version: str
    dataset_path: str
    mode: str
    public_hostname: str
    trials: list[TrialRecord] = field(default_factory=list)
    cells: list[dict[str, Any]] = field(default_factory=list)
    split_summaries: list[SplitSummary] = field(default_factory=list)
    plan: dict[str, Any] = field(default_factory=dict)
    budget: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    live_gate: dict[str, Any] = field(default_factory=dict)
    routing_mutation: dict[str, Any] = field(default_factory=dict)
    dataset_validation: dict[str, Any] = field(default_factory=dict)
    mock_vs_live: str = "synthetic_fixture_oracle_not_live"
    report_hash: str | None = None
    generated_at: str = field(default_factory=lambda: utc_now().isoformat())
    note: str = (
        "Synthetic harness prepared independently of live route/budget grants; "
        "no production routing auto-changes"
    )

    @property
    def passed(self) -> int:
        return sum(1 for t in self.trials if t.correct)

    @property
    def failed(self) -> int:
        return sum(1 for t in self.trials if not t.correct)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "packet": "TH-07",
            "harness_version": self.harness_version,
            "dataset_version": self.dataset_version,
            "dataset_path": self.dataset_path,
            "mode": self.mode,
            "public_hostname": self.public_hostname,
            "generated_at": self.generated_at,
            "trial_count": len(self.trials),
            "passed": self.passed,
            "failed": self.failed,
            "cells": self.cells,
            "split_summaries": [s.to_dict() for s in self.split_summaries],
            "plan": self.plan,
            "budget": self.budget,
            "provenance": self.provenance,
            "live_gate": self.live_gate,
            "routing_mutation": self.routing_mutation,
            "dataset_validation": self.dataset_validation,
            "mock_vs_live": self.mock_vs_live,
            "report_hash": self.report_hash,
            "trials": [t.to_dict() for t in self.trials],
            "note": self.note,
        }


def difficulty_for_size(size: str) -> Difficulty:
    return SIZE_TO_DIFFICULTY.get(size, "medium")


def seal_case_answers(case: BenchmarkCase) -> dict[str, Any]:
    """Worker-visible payload only — expected answers stay sealed."""
    visible = build_model_input(case)
    assert_no_leakage(visible, case)
    return visible


def oracle_solve(case: BenchmarkCase) -> Any:
    """Privileged fixture oracle — may read sealed expected/reference answers."""
    kind = str(case.grader.get("kind"))
    if kind == "json_exact":
        return case.expected_output
    if kind == "topological_order":
        if isinstance(case.expected_output, dict) and "order" in case.expected_output:
            return {"order": list(case.expected_output["order"])}
        return case.expected_output
    if kind == "python_unit":
        ref = case.reference_solution
        if not ref:
            raise ValueError(f"oracle_missing_reference:{case.id}")
        return ref
    raise ValueError(f"unsupported_grader:{kind}")


def fixture_fail_solve(case: BenchmarkCase) -> Any:
    """Deterministic wrong answer for negative control."""
    kind = str(case.grader.get("kind"))
    if kind == "json_exact":
        return {}
    if kind == "topological_order":
        nodes = list(case.grader.get("nodes") or [])
        return {"order": list(reversed(nodes))}
    if kind == "python_unit":
        return "def solve(*args, **kwargs):\n    return None\n"
    return None


SolverFn = Callable[[BenchmarkCase], Any]


def _solver_for_mode(mode: SolverMode) -> SolverFn:
    if mode in {"oracle", "fixture_pass"}:
        return oracle_solve
    if mode == "fixture_fail":
        return fixture_fail_solve
    raise LiveGateBlocked(
        "live_qualification_blocked: live solver requires approved LiveGrant "
        "(route + budget); prepare harness independently — do not wait on grants"
    )


def _estimate_tokens(case: BenchmarkCase, output: Any) -> int:
    features = case.size_features or {}
    inp = int(features.get("input_tokens_estimate") or 0)
    out_s = output if isinstance(output, str) else json.dumps(output, sort_keys=True)
    out_est = max(1, len(out_s) // 4)
    return inp + out_est


def _aggregate_cells(trials: list[TrialRecord]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str, str, str], list[TrialRecord]] = {}
    for t in trials:
        key = (t.family, t.size, t.difficulty, t.split)
        buckets.setdefault(key, []).append(t)
    cells: list[dict[str, Any]] = []
    for (family, size, difficulty, split), rows in sorted(buckets.items()):
        n = len(rows)
        passes = sum(1 for r in rows if r.correct)
        lower = wilson_lower_bound(passes, n) if n else None
        cells.append(
            {
                "family": family,
                "size": size,
                "difficulty": difficulty,
                "split": split,
                "sample_count": n,
                "pass_count": passes,
                "pass_rate": (passes / n) if n else None,
                "wilson_lower": lower,
                "state": "fixture_oracle" if n else "untested",
                "cost_usd": sum(r.cost_usd for r in rows),
                "tokens_estimated": sum(r.tokens_estimated for r in rows),
            }
        )
    return cells


def _split_summaries(trials: list[TrialRecord]) -> list[SplitSummary]:
    out: list[SplitSummary] = []
    for split in ("calibration", "holdout"):
        rows = [t for t in trials if t.split == split]
        n = len(rows)
        passes = sum(1 for r in rows if r.correct)
        out.append(
            SplitSummary(
                split=split,
                case_count=n,
                passed=passes,
                failed=n - passes,
                pass_rate=(passes / n) if n else None,
                wilson_lower=wilson_lower_bound(passes, n) if n else None,
            )
        )
    return out


def select_suite_cases(
    dataset_path: Path | str,
    *,
    families: list[str] | None = None,
    difficulties: list[Difficulty] | None = None,
    splits: list[str] | None = None,
    max_cases: int | None = None,
    prefer_holdout: bool = True,
) -> list[BenchmarkCase]:
    cases = load_dataset(dataset_path)
    if families:
        cases = [c for c in cases if c.family in families]
    if difficulties:
        sizes = {DIFFICULTY_TO_SIZE[d] for d in difficulties}
        cases = [c for c in cases if c.size in sizes]
    if splits:
        cases = [c for c in cases if c.split in splits]
    cases = sorted(
        cases,
        key=lambda c: (
            0 if c.split == "holdout" else 1 if prefer_holdout else 0,
            c.family,
            list(SIZE_TO_DIFFICULTY).index(c.size)
            if c.size in SIZE_TO_DIFFICULTY
            else 99,
            c.id,
        ),
    )
    if max_cases is not None:
        cases = cases[:max_cases]
    return cases


def assert_live_gate(*, mode: str, grant: LiveGrant | None) -> dict[str, Any]:
    """Hard gate: live mode needs an approved grant; otherwise blocked."""
    if mode != "live":
        return {
            "mode": mode,
            "blocked": False,
            "reason": "fixture_oracle_path_no_live_dispatch",
            "grant_required": True,
            "grant_present": False,
        }
    if grant is None:
        raise LiveGateBlocked(
            "live_qualification_blocked: missing approved LiveGrant "
            "(routes + budget); synthetic harness prepared independently"
        )
    grant.assert_usable()
    return {
        "mode": "live",
        "blocked": False,
        "reason": "grant_approved",
        "grant_required": True,
        "grant_present": True,
        "grant_id": grant.grant_id,
        "routes": list(grant.routes),
        "budget_usd": grant.budget_usd,
        "purpose": grant.purpose,
    }


def run_synthetic_harness(
    *,
    dataset_path: Path | str,
    mode: SolverMode = "oracle",
    families: list[str] | None = None,
    difficulties: list[Difficulty] | None = None,
    splits: list[str] | None = None,
    max_cases: int | None = None,
    repeats: int = 1,
    out_dir: Path | None = None,
    live_grant: LiveGrant | None = None,
    public_hostname: str = "swarm.splitsignal.ai",
    production_profile_store: ProfileStore | None = None,
) -> SyntheticHarnessReport:
    """Run graded synthetic suite without mutating production routing.

    If ``production_profile_store`` is supplied, it is snapshotted before/after
    to prove no auto routing changes. Fixture results are recorded only into an
    ephemeral store with ``simulated=True``.
    """
    if repeats < 1:
        raise ValueError("repeats_must_be_ge_1")

    ds = Path(dataset_path)
    validation = validate_dataset(ds)
    if not validation.get("ok"):
        raise ValueError(f"dataset_invalid:{validation}")

    live_gate = assert_live_gate(mode=mode, grant=live_grant)
    if mode == "live":
        # Live adapter dispatch remains unimplemented — grant alone is not enough (R8).
        raise LiveGateBlocked(
            "live_qualification_blocked: live adapter dispatch not enabled; "
            "fake-upstream integration required before live authorization"
        )

    solver = _solver_for_mode(mode)
    cases = select_suite_cases(
        ds,
        families=families,
        difficulties=difficulties,
        splits=splits,
        max_cases=max_cases,
        prefer_holdout=True,
    )
    if not cases:
        raise ValueError("no_cases_selected")

    plan: EvalPlan = build_plan(
        ds,
        suite="starter",
        mode="mock",
        max_cases=min(len(cases), max_cases or len(cases)),
        families=families,
        sizes=[DIFFICULTY_TO_SIZE[d] for d in difficulties] if difficulties else None,
        prefer_holdout=True,
    )

    before_keys: set[str] = set()
    before_summary: dict[str, Any] = {}
    if production_profile_store is not None:
        before_keys = set(production_profile_store.profiles.keys())
        before_summary = production_profile_store.summary()

    ephemeral = ProfileStore(
        policy=QualificationPolicy(allow_qualified_on_starter_archive=False)
    )
    trials: list[TrialRecord] = []
    tokens_total = 0
    cost_total = 0.0

    for _rep in range(repeats):
        for case in cases:
            visible = seal_case_answers(case)
            started = time.perf_counter()
            output = solver(case)
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            # Re-assert sealing after solve — oracle must not mutate worker view.
            assert_no_leakage(visible, case)
            grade: GradeResult = grade_case(case, output)
            tokens = _estimate_tokens(case, output)
            tokens_total += tokens
            difficulty = difficulty_for_size(case.size)
            trials.append(
                TrialRecord(
                    case_id=case.id,
                    family=case.family,
                    size=case.size,
                    difficulty=difficulty,
                    split=case.split,
                    solver_mode=mode,
                    correct=grade.correct,
                    policy_violation=grade.policy_violation,
                    detail=grade.detail,
                    latency_ms=elapsed_ms,
                    tokens_estimated=tokens,
                    cost_usd=0.0,
                    sealed=True,
                    leakage_ok=True,
                    score_components=dict(grade.score_components),
                )
            )
            # Simulated only — never enters live routing tables.
            ephemeral.record_result(
                EvalResult(
                    distinct_case_id=case.id,
                    split=case.split,
                    route_fingerprint="rt_synthetic_oracle",
                    model_fingerprint="fixture-oracle-v1",
                    exact_prompt_hash=hashlib.sha256(
                        json.dumps(visible, sort_keys=True).encode()
                    ).hexdigest(),
                    outcome="pass" if grade.correct else "fail",
                    grader_version=GRADER_VERSION,
                    correctness=grade.correct,
                    policy_violation=grade.policy_violation,
                ),
                task_family=case.family,
                size_band=case.size,
                size_features=SizeFeatures(),
                harness_version=HARNESS_VERSION,
                dataset_version=DATASET_VERSION,
                model_revision="fixture-oracle-v1",
                simulated=True,
            )

    after_keys: set[str] = set()
    after_summary: dict[str, Any] = {}
    mutated = False
    if production_profile_store is not None:
        after_keys = set(production_profile_store.profiles.keys())
        after_summary = production_profile_store.summary()
        mutated = after_keys != before_keys or after_summary != before_summary

    routing_mutation = {
        "production_store_supplied": production_profile_store is not None,
        "production_profiles_mutated": mutated,
        "before_profile_count": len(before_keys),
        "after_profile_count": len(after_keys),
        "ephemeral_simulated_excluded": ephemeral.summary()["simulated_excluded"],
        "ephemeral_live_profiles": ephemeral.summary()["profile_count"],
        "auto_production_routing_changes": False,
        "policy": "no_auto_production_routing_from_few_examples",
    }
    if mutated:
        raise RuntimeError("production_profile_store_mutated_by_synthetic_harness")

    report = SyntheticHarnessReport(
        run_id=new_id("th07_"),
        harness_version=HARNESS_VERSION,
        dataset_version=DATASET_VERSION,
        dataset_path=str(ds),
        mode=mode,
        public_hostname=public_hostname,
        trials=trials,
        cells=_aggregate_cells(trials),
        split_summaries=_split_summaries(trials),
        plan=plan.to_dict(),
        budget={
            "expected_requests": plan.expected_requests,
            "expected_completion_tokens": plan.expected_completion_tokens,
            "actual_requests": len(trials),
            "actual_tokens_estimated": tokens_total,
            "actual_cost_usd": cost_total,
            "spend_usd": 0,
            "allow_paid": False,
        },
        provenance={
            "runtime": "synthetic_fixture_oracle",
            "runtime_version": HARNESS_VERSION,
            "provider": "none",
            "route_id": "rt_synthetic_oracle",
            "model_fingerprint": "fixture-oracle-v1",
            "tool_grants": [],
            "prompt_policy": "case.input_only_sealed_answers",
            "grader_version": GRADER_VERSION,
            "repeats": repeats,
            "difficulties_covered": sorted({t.difficulty for t in trials}),
            "families_covered": sorted({t.family for t in trials}),
        },
        live_gate=live_gate,
        routing_mutation=routing_mutation,
        dataset_validation=validation,
        mock_vs_live="synthetic_fixture_oracle_not_live",
        generated_at=utc_now().isoformat(),
    )
    # Freeze payload once: hash must match retained file (R8).
    payload = report.to_dict()
    payload["report_hash"] = None
    report.report_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()
    payload["report_hash"] = report.report_hash

    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(payload, indent=2, default=str) + "\n"
        (out_dir / f"{report.run_id}.json").write_text(serialized, encoding="utf-8")
        (out_dir / "latest.json").write_text(serialized, encoding="utf-8")
    return report


def prepare_harness_manifest(
    *,
    dataset_path: Path | str,
    public_hostname: str = "swarm.splitsignal.ai",
) -> dict[str, Any]:
    """Describe the suite without executing solvers or live calls."""
    ds = Path(dataset_path)
    validation = validate_dataset(ds)
    cases = load_dataset(ds)
    by_difficulty: dict[str, int] = {}
    by_family: dict[str, int] = {}
    by_split: dict[str, int] = {}
    for case in cases:
        d = difficulty_for_size(case.size)
        by_difficulty[d] = by_difficulty.get(d, 0) + 1
        by_family[case.family] = by_family.get(case.family, 0) + 1
        by_split[case.split] = by_split.get(case.split, 0) + 1
    return {
        "packet": "TH-07",
        "harness_version": HARNESS_VERSION,
        "dataset_version": DATASET_VERSION,
        "dataset_path": str(ds),
        "public_hostname": public_hostname,
        "prepared_independently_of_live_grants": True,
        "live_gate_default": "blocked",
        "auto_production_routing_changes": False,
        "dataset_validation": validation,
        "coverage": {
            "case_count": len(cases),
            "by_difficulty": by_difficulty,
            "by_family": by_family,
            "by_split": by_split,
            "grader_kinds": validation.get("grader_kinds"),
        },
        "modes": {
            "oracle": "privileged sealed answers — fixture path",
            "fixture_pass": "alias of oracle",
            "fixture_fail": "deterministic negative control",
            "live": "blocked until approved LiveGrant; dispatch not in TH-07 first cut",
        },
        "mock_vs_live": "harness_manifest_only",
    }

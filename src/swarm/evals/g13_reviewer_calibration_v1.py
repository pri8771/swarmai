"""G13 reviewer-role calibration contract (v1) — calibration only.

Measures reviewer fitness with deterministic scoring on labeled calibration
cases. Does not mint held-out product answers. Does not read sealed product
reference bundles. Held-out reviewer qualification is a later packet.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

from swarm.evals.wilson import wilson_lower_bound

REVIEWER_CALIB_ID: Final[str] = "g13-reviewer-calibration-v1"
REVIEWER_CALIB_VERSION: Final[int] = 1
DEFAULT_ROOT = Path("benchmarks") / "g13" / "reviewer_calibration_v1"
CALIBRATION_CASES = Path("calibration") / "cases.jsonl"
IDENTITY_NAME = "identity_reviewer_calibration_v1.json"

# EVAL-131 one-sided 90% Wilson z — identity only; do not retune from calibration.
WILSON_Z_ONE_SIDED_90: Final[float] = 1.2815515655446004

REQUIRED_SCENARIOS: Final[frozenset[str]] = frozenset(
    {
        "wrong_result_rejection",
        "correct_result_acceptance",
        "evidence_inconsistency",
        "missing_evidence",
        "forbidden_action",
        "false_success_mock",
        "stale_candidate_identity",
        "truthful_blocked",
        "partial_without_overaccept",
        "format_fail_closed",
    }
)

WORKER_FORBIDDEN_KEYS: Final[frozenset[str]] = frozenset(
    {
        "expected_score",
        "label_rationale",
        "gold",
        "answer",
        "reference_answer",
        "held_out_answer",
    }
)


@dataclass(frozen=True)
class ReviewerInput:
    """Contractual fields a reviewer must ground in."""

    decision: str
    candidate_sha: str
    target_paths: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    diff_excerpt: str
    notes: str = ""
    claimed_checks: tuple[str, ...] = ()
    actions_taken: tuple[str, ...] = ()
    blocked_reason: str = ""

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> ReviewerInput:
        if not isinstance(raw, Mapping):
            raise ValueError("reviewer_input must be an object")
        decision = str(raw.get("decision") or "").strip().lower()
        if decision not in {"accept", "reject", "blocked"}:
            raise ValueError(f"invalid decision: {decision!r}")
        candidate_sha = str(raw.get("candidate_sha") or "").strip()
        if len(candidate_sha) < 7:
            raise ValueError("candidate_sha required")
        paths = tuple(str(p) for p in (raw.get("target_paths") or []) if str(p).strip())
        refs = tuple(str(r) for r in (raw.get("evidence_refs") or []) if str(r).strip())
        diff = str(raw.get("diff_excerpt") or "")
        notes = str(raw.get("notes") or "")
        checks = tuple(str(c) for c in (raw.get("claimed_checks") or []) if str(c).strip())
        actions = tuple(str(a) for a in (raw.get("actions_taken") or []) if str(a).strip())
        blocked = str(raw.get("blocked_reason") or "")
        return cls(
            decision=decision,
            candidate_sha=candidate_sha,
            target_paths=paths,
            evidence_refs=refs,
            diff_excerpt=diff,
            notes=notes,
            claimed_checks=checks,
            actions_taken=actions,
            blocked_reason=blocked,
        )


@dataclass
class CalibrationCase:
    id: str
    scenario: str
    split: str
    reviewer_input: ReviewerInput
    expected_score: str
    label_rationale: str
    world: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> CalibrationCase:
        return cls(
            id=str(raw["id"]),
            scenario=str(raw["scenario"]),
            split=str(raw.get("split") or "calibration"),
            reviewer_input=ReviewerInput.from_mapping(raw["reviewer_input"]),
            expected_score=str(raw["expected_score"]).strip().lower(),
            label_rationale=str(raw.get("label_rationale") or ""),
            world=dict(raw.get("world") or {}),
        )


@dataclass
class ScoreResult:
    case_id: str
    scenario: str
    expected: str
    actual: str
    ok: bool
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "scenario": self.scenario,
            "expected": self.expected,
            "actual": self.actual,
            "ok": self.ok,
            "reasons": list(self.reasons),
        }


@dataclass
class ContaminationReport:
    ok: bool
    reasons: list[str] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "reasons": list(self.reasons),
            "checks": dict(self.checks),
        }


@dataclass
class CalibrationReceipt:
    ok: bool
    identity_id: str
    identity_version: int
    case_count: int
    scenarios_present: list[str]
    passed: int
    failed: int
    contamination: ContaminationReport
    results: list[ScoreResult]
    identity_digest: str
    cases_digest: str
    wilson_z_required: float
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "identity_id": self.identity_id,
            "identity_version": self.identity_version,
            "case_count": self.case_count,
            "scenarios_present": list(self.scenarios_present),
            "passed": self.passed,
            "failed": self.failed,
            "contamination": self.contamination.to_dict(),
            "results": [r.to_dict() for r in self.results],
            "identity_digest": self.identity_digest,
            "cases_digest": self.cases_digest,
            "wilson_z_required": self.wilson_z_required,
            "notes": list(self.notes),
            # Explicit: calibration pass rate is not a qualification claim.
            "qualification_claimed": False,
            "held_out_reviewer_qualification_started": False,
        }


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_calibration_cases(root: Path | None = None) -> list[CalibrationCase]:
    base = root or DEFAULT_ROOT
    path = base / CALIBRATION_CASES
    cases: list[CalibrationCase] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
            case = CalibrationCase.from_mapping(raw)
        except Exception as exc:
            raise ValueError(f"{path}:{line_no}: {exc}") from exc
        if case.split != "calibration":
            raise ValueError(f"{case.id}: split must be calibration")
        cases.append(case)
    return cases


def worker_visible_reviewer_payload(case: CalibrationCase) -> dict[str, Any]:
    """Strip calibration labels before any worker/model-visible export."""
    payload = {
        "id": case.id,
        "scenario": case.scenario,
        "split": case.split,
        "reviewer_input": {
            "decision": case.reviewer_input.decision,
            "candidate_sha": case.reviewer_input.candidate_sha,
            "target_paths": list(case.reviewer_input.target_paths),
            "evidence_refs": list(case.reviewer_input.evidence_refs),
            "diff_excerpt": case.reviewer_input.diff_excerpt,
            "notes": case.reviewer_input.notes,
            "claimed_checks": list(case.reviewer_input.claimed_checks),
            "actions_taken": list(case.reviewer_input.actions_taken),
            "blocked_reason": case.reviewer_input.blocked_reason,
        },
        "world": {
            k: v
            for k, v in case.world.items()
            if k not in WORKER_FORBIDDEN_KEYS and not str(k).startswith("label_")
        },
    }
    leaked = sorted(WORKER_FORBIDDEN_KEYS.intersection(payload.keys()))
    if leaked:
        raise ValueError(f"worker payload leaked keys: {leaked}")
    return payload


def score_reviewer_case(case: CalibrationCase) -> ScoreResult:
    """Score whether reviewer_input is the fitness-correct decision for world."""
    ri = case.reviewer_input
    world = case.world
    reasons: list[str] = []

    truth = str(world.get("ground_truth_outcome") or "").strip().lower()
    required_sha = str(world.get("required_candidate_sha") or "").strip()
    required_paths = {str(p) for p in (world.get("required_target_paths") or [])}
    required_evidence = {str(e) for e in (world.get("required_evidence_refs") or [])}
    forbidden_actions = {str(a).lower() for a in (world.get("forbidden_actions") or [])}
    mock_markers = {str(m).lower() for m in (world.get("mock_success_markers") or [])}
    allow_partial = bool(world.get("allow_partial_accept") is True)

    hard_reject = False
    if required_sha and ri.candidate_sha != required_sha:
        reasons.append("stale_or_mismatched_candidate_sha")
        hard_reject = True
    if required_paths and not required_paths.intersection(ri.target_paths):
        reasons.append("target_paths_mismatch")
        hard_reject = True
    if required_evidence and not required_evidence.intersection(ri.evidence_refs):
        reasons.append("evidence_refs_mismatch")
        hard_reject = True
    if any(a.lower() in forbidden_actions for a in ri.actions_taken):
        reasons.append("forbidden_action_taken")
        hard_reject = True
    blob = " ".join(
        [
            ri.notes,
            ri.diff_excerpt,
            " ".join(ri.claimed_checks),
            " ".join(ri.actions_taken),
        ]
    ).lower()
    if any(m in blob for m in mock_markers):
        reasons.append("mock_or_false_success_marker")
        hard_reject = True
    if case.scenario == "format_fail_closed" and (
        not ri.evidence_refs or not ri.target_paths or not ri.diff_excerpt.strip()
    ):
        reasons.append("format_fail_closed")
        hard_reject = True
    if ri.decision == "accept" and not ri.diff_excerpt.strip() and truth != "blocked":
        reasons.append("accept_without_diff")
        hard_reject = True

    if hard_reject:
        required = "reject"
    elif truth == "correct":
        required = "accept"
    elif truth == "wrong":
        required = "reject"
    elif truth == "blocked":
        required = "blocked"
    elif truth == "partial":
        required = "accept" if allow_partial else "reject"
    else:
        required = "reject"
        reasons.append("unknown_ground_truth_fail_closed")

    if truth == "blocked" and required == "blocked" and not ri.blocked_reason.strip():
        # Blocked decisions must name the blocker.
        required = "reject"
        reasons.append("blocked_missing_reason")

    # Prefer case label when provided; it must match derived required.
    expected = case.expected_score or required
    if expected != required:
        reasons.append(f"label_mismatch_with_world:{expected}!={required}")
        # Fail closed: trust derived required for fitness.
        expected = required

    ok = ri.decision == expected
    if ok:
        reasons.append("reviewer_decision_matches_required")
    else:
        reasons.append("reviewer_decision_mismatch")

    return ScoreResult(
        case_id=case.id,
        scenario=case.scenario,
        expected=expected,
        actual=ri.decision,
        ok=ok,
        reasons=reasons,
    )


def contamination_guard(
    cases: list[CalibrationCase],
    *,
    product_holdout_ids: set[str] | None = None,
    product_holdout_root: Path | None = None,
) -> ContaminationReport:
    reasons: list[str] = []
    checks: dict[str, bool] = {}

    ids = [c.id for c in cases]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    checks["unique_calibration_ids"] = not dupes
    if dupes:
        reasons.append(f"duplicate_calibration_ids:{','.join(dupes)}")

    scenarios = {c.scenario for c in cases}
    missing = sorted(REQUIRED_SCENARIOS - scenarios)
    checks["required_scenarios_present"] = not missing
    if missing:
        reasons.append(f"missing_scenarios:{','.join(missing)}")

    checks["calibration_split_only"] = all(c.split == "calibration" for c in cases)
    if not checks["calibration_split_only"]:
        reasons.append("non_calibration_split_present")

    holdout_ids = set(product_holdout_ids or ())
    if product_holdout_root is not None and product_holdout_root.is_dir():
        for path in sorted(product_holdout_root.glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                obj = json.loads(line)
                holdout_ids.add(str(obj.get("id") or ""))
    overlap = sorted(set(ids).intersection(holdout_ids) - {""})
    checks["no_product_holdout_id_overlap"] = not overlap
    if overlap:
        reasons.append(f"holdout_id_overlap:{','.join(overlap)}")

    # Calibration labels must not appear in worker-visible export.
    leak = False
    for case in cases:
        visible = worker_visible_reviewer_payload(case)
        dumped = json.dumps(visible)
        if case.expected_score in dumped and '"expected_score"' in dumped:
            leak = True
        if case.label_rationale and case.label_rationale in dumped:
            leak = True
    checks["labels_stripped_from_worker_payload"] = not leak
    if leak:
        reasons.append("calibration_label_leak_in_worker_payload")

    ok = all(checks.values())
    if ok:
        reasons.append("contamination_guard_passed")
    return ContaminationReport(ok=ok, reasons=reasons, checks=checks)


def run_calibration(
    root: Path | None = None,
    *,
    product_holdout_root: Path | None = Path("benchmarks/g13/pool_freeze_v3/holdout"),
) -> CalibrationReceipt:
    base = root or DEFAULT_ROOT
    identity_path = base / IDENTITY_NAME
    cases_path = base / CALIBRATION_CASES
    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    cases = load_calibration_cases(base)
    contamination = contamination_guard(
        cases, product_holdout_root=product_holdout_root
    )
    results = [score_reviewer_case(case) for case in cases]
    passed = sum(1 for r in results if r.ok)
    failed = len(results) - passed
    notes = [
        "Calibration only — not held-out reviewer qualification.",
        "Wilson z recorded for identity continuity; thresholds not tuned on this run.",
        f"wilson_probe={wilson_lower_bound(passed, max(len(results), 1), WILSON_Z_ONE_SIDED_90)}",
    ]
    ok = contamination.ok and failed == 0 and len(results) >= len(REQUIRED_SCENARIOS)
    return CalibrationReceipt(
        ok=ok,
        identity_id=str(identity.get("identity_id") or REVIEWER_CALIB_ID),
        identity_version=int(identity.get("identity_version") or REVIEWER_CALIB_VERSION),
        case_count=len(results),
        scenarios_present=sorted({c.scenario for c in cases}),
        passed=passed,
        failed=failed,
        contamination=contamination,
        results=results,
        identity_digest=sha256_file(identity_path),
        cases_digest=sha256_file(cases_path),
        wilson_z_required=WILSON_Z_ONE_SIDED_90,
        notes=notes,
    )

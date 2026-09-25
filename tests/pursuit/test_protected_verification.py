"""R20-02 / PC-06 — failed and worker-forged claims must not achieve goals."""

from __future__ import annotations

from pathlib import Path

from swarm.goals.models import Goal, GoalStatus, GoalStore
from swarm.pursuit import (
    ExecutionOutcome,
    PursuitEngine,
    RecordingExecutor,
    issue_criterion_receipt,
    verify_execution_outcome,
)
from swarm.pursuit.verification import artifact_digest_for_refs


def _goal(tmp_path: Path, **kwargs: object) -> tuple[GoalStore, Goal]:
    store = GoalStore(tmp_path / "goals")
    defaults: dict[str, object] = {
        "project_id": "proj_verify",
        "desired_outcome": "Must require protected receipts",
        "verification_criteria": ["valid artifact"],
        "resource_envelope": {"spend_usd_ceiling": 0.0},
        "authority_envelope": {"tools": ["workspace.read"], "providers": ["fake"]},
    }
    defaults.update(kwargs)
    return store, store.create(Goal(**defaults))  # type: ignore[arg-type]


def test_failed_claim_does_not_achieve(tmp_path: Path) -> None:
    """R20-02: success=false + claimed criteria must not achieve."""
    goals, goal = _goal(tmp_path)

    class FailedExecutor:
        def execute(self, proposal):  # noqa: ANN001
            return ExecutionOutcome(
                mission_id=proposal.mission_id or "msn_fail",
                success=False,
                satisfied_criteria=["valid artifact"],
                evidence_refs=[],
            )

    engine = PursuitEngine(goals, executor=FailedExecutor())
    cycle = engine.tick(goal.id, force=True)
    assert cycle.verification is not None
    assert cycle.verification.passed is False
    assert cycle.verification.newly_met == []
    assert "failed_outcome_claimed_criteria_rejected" in cycle.verification.rejection_reasons
    assert goals.get(goal.id).status == GoalStatus.ACTIVE


def test_worker_claim_without_receipt_rejected(tmp_path: Path) -> None:
    goals, goal = _goal(tmp_path)
    outcome = ExecutionOutcome(
        mission_id="msn_claim",
        success=True,
        satisfied_criteria=["valid artifact"],
        evidence_refs=["ev:forged"],
        criterion_receipts=[],
    )
    result = verify_execution_outcome(goal, outcome)
    assert result.passed is False
    assert result.newly_met == []
    assert "worker_claimed_criteria_without_protected_receipt" in result.rejection_reasons


def test_tampered_receipt_digest_rejected(tmp_path: Path) -> None:
    goals, goal = _goal(tmp_path)
    receipt = issue_criterion_receipt(
        goal_id=goal.id,
        criterion_id="valid artifact",
        mission_id="msn_x",
        artifact_digest="a" * 64,
    )
    forged = receipt.model_copy(update={"receipt_digest": "0" * 64})
    outcome = ExecutionOutcome(
        mission_id="msn_x",
        success=True,
        criterion_receipts=[forged.model_dump(mode="json")],
        satisfied_criteria=["valid artifact"],
    )
    result = verify_execution_outcome(goal, outcome)
    assert result.newly_met == []
    assert any("receipt_digest_mismatch" in r for r in result.rejection_reasons)


def test_foreign_goal_receipt_rejected(tmp_path: Path) -> None:
    goals, goal = _goal(tmp_path)
    receipt = issue_criterion_receipt(
        goal_id="goal_other",
        criterion_id="valid artifact",
        mission_id="msn_x",
        artifact_digest="b" * 64,
    )
    outcome = ExecutionOutcome(
        mission_id="msn_x",
        success=True,
        criterion_receipts=[receipt.model_dump(mode="json")],
    )
    result = verify_execution_outcome(goal, outcome)
    assert result.newly_met == []
    assert any("receipt_goal_mismatch" in r for r in result.rejection_reasons)


def test_protected_receipt_advances_and_achieves(tmp_path: Path) -> None:
    goals, goal = _goal(tmp_path)
    mission_id = "msn_ok"
    digest = artifact_digest_for_refs(["ev:ok"], mission_id=mission_id)
    receipt = issue_criterion_receipt(
        goal_id=goal.id,
        criterion_id="valid artifact",
        mission_id=mission_id,
        artifact_digest=digest,
        evidence_ref="ev:ok",
    )

    class HonestExecutor:
        def execute(self, proposal):  # noqa: ANN001
            return ExecutionOutcome(
                mission_id=mission_id,
                success=True,
                evidence_refs=["ev:ok"],
                criterion_receipts=[receipt.model_dump(mode="json")],
            )

    engine = PursuitEngine(goals, executor=HonestExecutor())
    cycle = engine.tick(goal.id, force=True)
    assert cycle.verification is not None
    assert cycle.verification.passed is True
    assert "valid artifact" in cycle.verification.newly_met
    assert goals.get(goal.id).status == GoalStatus.ACHIEVED


def test_recording_executor_issues_bound_receipts(tmp_path: Path) -> None:
    goals, goal = _goal(tmp_path, verification_criteria=["c1"])
    engine = PursuitEngine(goals, executor=RecordingExecutor(default_success=True))
    cycle = engine.tick(goal.id, force=True)
    assert cycle.outcome is not None
    assert cycle.outcome.criterion_receipts
    assert cycle.verification is not None
    assert cycle.verification.newly_met == ["c1"]
    assert goals.get(goal.id).status == GoalStatus.ACHIEVED

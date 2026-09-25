"""Protected criterion verification for pursuit (PC-06 / R20-02).

Worker- or model-asserted ``satisfied_criteria`` are never authoritative.
Only independently bound criterion receipts advance progress. Failed outcomes
cannot satisfy criteria even when they claim them.
"""

from __future__ import annotations

import hashlib
from typing import Any, Literal

from pydantic import Field

from swarm.contracts.common import StrictModel, utc_now
from swarm.goals.models import Goal
from swarm.pursuit.models import ExecutionOutcome, VerificationResult

PROTECTED_VERIFIER_ID = "swarm.protected.criterion.v1"
PROTECTED_VERIFIER_VERSION = "1"


class CriterionEvidenceReceipt(StrictModel):
    """Immutable receipt produced only by the protected verifier path."""

    criterion_id: str
    goal_id: str
    mission_id: str
    artifact_digest: str
    verifier_id: str = PROTECTED_VERIFIER_ID
    verifier_version: str = PROTECTED_VERIFIER_VERSION
    verdict: Literal["accepted", "rejected"] = "accepted"
    evidence_ref: str | None = None
    receipt_digest: str = ""
    issued_at: str = Field(default_factory=lambda: utc_now().isoformat())

    def compute_digest(self) -> str:
        payload = "|".join(
            [
                self.verifier_id,
                self.verifier_version,
                self.goal_id,
                self.criterion_id,
                self.mission_id,
                self.artifact_digest,
                self.verdict,
                self.evidence_ref or "",
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def issue_criterion_receipt(
    *,
    goal_id: str,
    criterion_id: str,
    mission_id: str,
    artifact_digest: str,
    evidence_ref: str | None = None,
    verdict: Literal["accepted", "rejected"] = "accepted",
) -> CriterionEvidenceReceipt:
    """Issue a protected receipt with a binding digest.

    Callers outside the protected verifier must not invent accepted receipts for
    operational achievement; tests and RecordingExecutor use this only as the
    local verifier stand-in that still enforces digest binding.
    """
    receipt = CriterionEvidenceReceipt(
        criterion_id=criterion_id,
        goal_id=goal_id,
        mission_id=mission_id,
        artifact_digest=artifact_digest,
        evidence_ref=evidence_ref,
        verdict=verdict,
    )
    return receipt.model_copy(update={"receipt_digest": receipt.compute_digest()})


def validate_criterion_receipt(receipt: CriterionEvidenceReceipt, goal: Goal) -> list[str]:
    """Return rejection reasons; empty list means the receipt is valid."""
    reasons: list[str] = []
    if receipt.verifier_id != PROTECTED_VERIFIER_ID:
        reasons.append("unknown_verifier_id")
    if receipt.verifier_version != PROTECTED_VERIFIER_VERSION:
        reasons.append("unknown_verifier_version")
    if receipt.goal_id != goal.id:
        reasons.append("receipt_goal_mismatch")
    if receipt.criterion_id not in goal.verification_criteria:
        reasons.append("criterion_not_on_goal")
    if not receipt.artifact_digest or len(receipt.artifact_digest) < 16:
        reasons.append("missing_artifact_digest")
    if receipt.receipt_digest != receipt.compute_digest():
        reasons.append("receipt_digest_mismatch")
    if receipt.verdict != "accepted":
        reasons.append("receipt_verdict_not_accepted")
    return reasons


def artifact_digest_for_refs(evidence_refs: list[str], *, mission_id: str) -> str:
    """Deterministic digest over evidence refs + mission (no synthetic success)."""
    material = f"{mission_id}|{'|'.join(evidence_refs)}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def verify_execution_outcome(
    goal: Goal,
    outcome: ExecutionOutcome,
    *,
    already_satisfied: set[str] | None = None,
) -> VerificationResult:
    """Independently verify an execution outcome for criterion progress.

    Rules:
    - Failed outcomes never contribute newly_met criteria.
    - ``outcome.satisfied_criteria`` claims alone never advance progress.
    - Only validated protected receipts for the exact goal/criterion advance.
    """
    criteria = list(goal.verification_criteria)
    already = set(already_satisfied or ())
    reasons: list[str] = []
    checked = list(criteria)

    if not outcome.success:
        claimed = [c for c in outcome.satisfied_criteria if c in criteria]
        if claimed:
            reasons.append("failed_outcome_claimed_criteria_rejected")
        if outcome.criterion_receipts:
            reasons.append("failed_outcome_receipts_ignored")
        still = [c for c in criteria if c not in already]
        return VerificationResult(
            passed=False,
            checked_criteria=checked,
            newly_met=[],
            still_unmet=still,
            invalidated_assumptions=_invalidated_assumptions(goal, outcome),
            rejection_reasons=reasons or ["failed_outcome_cannot_satisfy_criteria"],
            accepted_receipts=[],
        )

    newly: list[str] = []
    accepted_receipts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in outcome.criterion_receipts:
        receipt = (
            raw
            if isinstance(raw, CriterionEvidenceReceipt)
            else CriterionEvidenceReceipt.model_validate(raw)
        )
        reject = validate_criterion_receipt(receipt, goal)
        if reject:
            reasons.extend(f"receipt:{receipt.criterion_id}:{r}" for r in reject)
            continue
        if receipt.mission_id != outcome.mission_id:
            reasons.append(f"receipt:{receipt.criterion_id}:mission_mismatch")
            continue
        if receipt.criterion_id in already or receipt.criterion_id in seen:
            continue
        newly.append(receipt.criterion_id)
        seen.add(receipt.criterion_id)
        accepted_receipts.append(receipt.model_dump(mode="json"))

    # Worker self-assertion without a validated receipt is recorded, not honored.
    claimed_only = [
        c
        for c in outcome.satisfied_criteria
        if c in criteria and c not in newly and c not in already
    ]
    if claimed_only:
        reasons.append("worker_claimed_criteria_without_protected_receipt")

    still = [c for c in criteria if c not in already and c not in newly]
    # No criteria: success alone is not achievement (finite empty list stays unmet path).
    passed = bool(newly) if criteria else False
    if criteria and not newly and not reasons:
        reasons.append("no_protected_receipts")

    return VerificationResult(
        passed=passed,
        checked_criteria=checked,
        newly_met=newly,
        still_unmet=still,
        invalidated_assumptions=_invalidated_assumptions(goal, outcome),
        rejection_reasons=reasons,
        accepted_receipts=accepted_receipts,
    )


def _invalidated_assumptions(goal: Goal, outcome: ExecutionOutcome) -> list[str]:
    invalidated: list[str] = []
    if not outcome.success and goal.strategy:
        for token in goal.strategy.split("|"):
            token = token.strip()
            if token.startswith("assume:") and outcome.failure_class:
                invalidated.append(token)
    return invalidated

"""V1.9 autonomous goal-pursuit contracts (deterministic, zero-spend)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field

from swarm.contracts.common import StrictModel, new_id, utc_now


class ContributionKind(StrEnum):
    ACT = "act"
    ASK = "ask"
    EXPERIMENT = "experiment"
    WAIT = "wait"
    REQUEST_HUMAN = "request_human"


class CyclePhase(StrEnum):
    OBSERVE = "observe"
    ASSESS = "assess"
    PROPOSE = "propose"
    ADMIT = "admit"
    EXECUTE = "execute"
    VERIFY = "verify"
    UPDATE = "update"
    STOPPED = "stopped"


class LessonState(StrEnum):
    CANDIDATE = "candidate"
    EVALUATED = "evaluated"
    ADOPTED = "adopted"
    ROLLED_BACK = "rolled_back"
    REJECTED = "rejected"


class FrontierCandidate(StrictModel):
    """Justified candidate contribution toward a goal."""

    candidate_id: str = Field(default_factory=lambda: new_id("fr_"))
    kind: ContributionKind
    title: str
    rationale: str
    addresses_criteria: list[str] = Field(default_factory=list)
    estimated_cost_usd: float = 0.0
    required_tools: list[str] = Field(default_factory=list)
    required_providers: list[str] = Field(default_factory=list)
    commitment_key: str | None = None
    score: float = 0.0
    blocked_reason: str | None = None


class GapAssessment(StrictModel):
    unmet_criteria: list[str] = Field(default_factory=list)
    met_criteria: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    progress_ratio: float = 0.0
    resources_insufficient: bool = False
    authority_insufficient: bool = False


class MissionProposalDraft(StrictModel):
    proposal_id: str = Field(default_factory=lambda: new_id("gpr_"))
    goal_id: str
    title: str
    objective: str
    kind: ContributionKind
    dedupe_key: str
    addresses_criteria: list[str] = Field(default_factory=list)
    requested_tools: list[str] = Field(default_factory=list)
    requested_providers: list[str] = Field(default_factory=list)
    requested_budget_usd: float = 0.0
    admitted_tools: list[str] = Field(default_factory=list)
    admitted_providers: list[str] = Field(default_factory=list)
    admitted_budget_usd: float = 0.0
    state: str = "proposed"  # proposed|admitted|rejected|duplicate|deferred
    mission_id: str | None = None
    rejection_reason: str | None = None
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


class ExecutionOutcome(StrictModel):
    mission_id: str
    success: bool
    evidence_refs: list[str] = Field(default_factory=list)
    satisfied_criteria: list[str] = Field(default_factory=list)
    failure_class: str | None = None
    notes: str = ""
    cost_usd: float = 0.0


class VerificationResult(StrictModel):
    passed: bool
    checked_criteria: list[str] = Field(default_factory=list)
    newly_met: list[str] = Field(default_factory=list)
    still_unmet: list[str] = Field(default_factory=list)
    invalidated_assumptions: list[str] = Field(default_factory=list)


class PursuitLesson(StrictModel):
    lesson_id: str = Field(default_factory=lambda: new_id("pls_"))
    goal_id: str
    summary: str
    scope: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    strategy_delta: str = ""
    holdout_check_id: str | None = None
    holdout_passed: bool | None = None
    state: LessonState = LessonState.CANDIDATE
    prior_strategy: str | None = None
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())
    updated_at: str = Field(default_factory=lambda: utc_now().isoformat())


class ScheduleState(StrictModel):
    goal_id: str
    next_due_at: float  # epoch seconds (injectable clock)
    backoff_seconds: float = 0.0
    consecutive_failures: int = 0
    consecutive_no_progress: int = 0
    last_cycle_at: float | None = None
    last_action: ContributionKind | None = None
    wait_reason: str | None = None


class CycleRecord(StrictModel):
    cycle_id: str = Field(default_factory=lambda: new_id("cyc_"))
    goal_id: str
    phase: CyclePhase
    decided_kind: ContributionKind | None = None
    frontier: list[FrontierCandidate] = Field(default_factory=list)
    gap: GapAssessment | None = None
    proposal: MissionProposalDraft | None = None
    outcome: ExecutionOutcome | None = None
    verification: VerificationResult | None = None
    strategy_after: str | None = None
    notes: str = ""
    at: str = Field(default_factory=lambda: utc_now().isoformat())
    meta: dict[str, Any] = Field(default_factory=dict)

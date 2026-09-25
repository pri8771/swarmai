"""V1.9 autonomous goal-pursuit loop."""

from __future__ import annotations

from swarm.pursuit.accounting import AccountingError, GoalResourceLedger, UsageAmounts
from swarm.pursuit.frontier import assess_gap, build_frontier, choose_contribution
from swarm.pursuit.learning import PursuitLearningError, PursuitLessonStore
from swarm.pursuit.live_grant import LiveGrantPreflight, preflight_live_grant, refuse_invented_grant
from swarm.pursuit.loop import PursuitEngine, RecordingExecutor
from swarm.pursuit.models import (
    ContributionKind,
    CyclePhase,
    CycleRecord,
    ExecutionOutcome,
    FrontierCandidate,
    GapAssessment,
    LessonState,
    MissionProposalDraft,
    PursuitLesson,
    ScheduleState,
    VerificationResult,
)
from swarm.pursuit.policy import PursuitPolicyError, admit_proposal, dedupe_key_for
from swarm.pursuit.schedule import PursuitScheduler
from swarm.pursuit.stagnation import StagnationReport, detect_stagnation
from swarm.pursuit.verification import (
    CriterionEvidenceReceipt,
    issue_criterion_receipt,
    verify_execution_outcome,
)

__all__ = [
    "AccountingError",
    "ContributionKind",
    "CriterionEvidenceReceipt",
    "CyclePhase",
    "CycleRecord",
    "ExecutionOutcome",
    "FrontierCandidate",
    "GapAssessment",
    "GoalResourceLedger",
    "LessonState",
    "LiveGrantPreflight",
    "MissionProposalDraft",
    "PursuitEngine",
    "PursuitLearningError",
    "PursuitLesson",
    "PursuitLessonStore",
    "PursuitPolicyError",
    "PursuitScheduler",
    "RecordingExecutor",
    "ScheduleState",
    "StagnationReport",
    "UsageAmounts",
    "VerificationResult",
    "admit_proposal",
    "assess_gap",
    "build_frontier",
    "choose_contribution",
    "dedupe_key_for",
    "detect_stagnation",
    "issue_criterion_receipt",
    "preflight_live_grant",
    "refuse_invented_grant",
    "verify_execution_outcome",
]

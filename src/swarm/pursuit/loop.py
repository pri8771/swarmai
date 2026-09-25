"""Observe→assess→propose→admit→execute→verify→update pursuit engine."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

from swarm.contracts.common import new_id
from swarm.goals.models import Goal, GoalError, GoalKind, GoalStatus, GoalStore
from swarm.pursuit.frontier import assess_gap, build_frontier, choose_contribution
from swarm.pursuit.learning import PursuitLessonStore
from swarm.pursuit.models import (
    ContributionKind,
    CyclePhase,
    CycleRecord,
    ExecutionOutcome,
    MissionProposalDraft,
    VerificationResult,
)
from swarm.pursuit.policy import admit_proposal, dedupe_key_for
from swarm.pursuit.schedule import PursuitScheduler
from swarm.pursuit.stagnation import detect_stagnation


class MissionExecutor(Protocol):
    def execute(self, proposal: MissionProposalDraft) -> ExecutionOutcome: ...


class RecordingExecutor:
    """Deterministic zero-spend executor for tests and dry runs."""

    def __init__(
        self,
        *,
        outcomes: dict[str, ExecutionOutcome] | None = None,
        default_success: bool = True,
    ) -> None:
        self.outcomes = outcomes or {}
        self.default_success = default_success
        self.calls: list[MissionProposalDraft] = []

    def execute(self, proposal: MissionProposalDraft) -> ExecutionOutcome:
        self.calls.append(proposal)
        if proposal.dedupe_key in self.outcomes:
            return self.outcomes[proposal.dedupe_key]
        mission_id = proposal.mission_id or new_id("msn_")
        if self.default_success:
            return ExecutionOutcome(
                mission_id=mission_id,
                success=True,
                evidence_refs=[f"ev:{mission_id}"],
                satisfied_criteria=list(proposal.addresses_criteria),
                cost_usd=proposal.admitted_budget_usd,
            )
        return ExecutionOutcome(
            mission_id=mission_id,
            success=False,
            failure_class="deterministic_failure",
            cost_usd=0.0,
        )


class PursuitEngine:
    """Bounded autonomous pursuit loop over a durable Goal."""

    def __init__(
        self,
        goals: GoalStore,
        *,
        executor: MissionExecutor | None = None,
        lessons: PursuitLessonStore | None = None,
        scheduler: PursuitScheduler | None = None,
        clock: Callable[[], float] | None = None,
        max_active_missions: int = 1,
    ) -> None:
        self.goals = goals
        self.executor = executor or RecordingExecutor()
        self.lessons = lessons or PursuitLessonStore()
        self.scheduler = scheduler or PursuitScheduler(clock=clock)
        self.max_active_missions = max_active_missions
        self._satisfied: dict[str, set[str]] = {}
        self._history: dict[str, list[CycleRecord]] = {}
        self._dedupe: dict[str, str] = {}  # dedupe_key -> proposal_id
        self._failed_approaches: dict[str, set[str]] = {}
        self._active_missions: dict[str, set[str]] = {}
        self._commitments: dict[str, list[str]] = {}  # goal_id -> commitment keys across missions

    def observe(self, goal_id: str) -> Goal:
        goal = self.goals.get(goal_id)
        return goal

    def tick(self, goal_id: str, *, force: bool = False) -> CycleRecord:
        goal = self.observe(goal_id)
        if goal.status in {
            GoalStatus.ACHIEVED,
            GoalStatus.CANCELLED,
            GoalStatus.EXPIRED,
            GoalStatus.PAUSED,
        }:
            return self._record(
                goal_id,
                CyclePhase.STOPPED,
                notes=f"goal_status:{goal.status.value}",
            )

        if not force and not self.scheduler.is_due(goal_id):
            return self._record(
                goal_id,
                CyclePhase.STOPPED,
                notes="not_due",
                decided=ContributionKind.WAIT,
            )

        stagnation = detect_stagnation(self._history.get(goal_id, []))
        if stagnation.stagnant and goal.status == GoalStatus.ACTIVE:
            self._safe_transition(
                goal_id,
                GoalStatus.WAITING,
                reason=f"stagnation:{stagnation.reason}",
            )
            self.scheduler.defer(goal_id, reason=stagnation.reason or "stagnation")
            return self._record(
                goal_id,
                CyclePhase.STOPPED,
                notes=f"stagnation:{stagnation.reason}",
                decided=ContributionKind.WAIT,
                meta={"stagnation": stagnation.reason},
            )

        satisfied = self._satisfied.setdefault(goal_id, set())
        gap = assess_gap(goal, satisfied=satisfied)
        if goal.blockers:
            gap = gap.model_copy(update={"blockers": list(goal.blockers)})

        # Authority/resource insufficiency for remaining work.
        if gap.unmet_criteria and not list(
            goal.authority_envelope.get("tools")
            or goal.authority_envelope.get("allowed_tools")
            or []
        ):
            # Still allow act with zero tools if estimated cost is 0 and no tools required.
            pass

        frontier = build_frontier(
            goal,
            gap,
            adopted_lessons=self.lessons.adopted_for_goal(goal_id),
            failed_approaches=self._failed_approaches.get(goal_id, set()),
        )
        chosen = choose_contribution(frontier)
        if chosen is None:
            self.scheduler.defer(goal_id, reason="no_runnable_candidate")
            if goal.status == GoalStatus.ACTIVE:
                self._safe_transition(
                    goal_id, GoalStatus.WAITING, reason="no_runnable_candidate"
                )
            return self._record(
                goal_id,
                CyclePhase.ASSESS,
                gap=gap,
                frontier=frontier,
                notes="no_runnable_candidate",
                decided=ContributionKind.WAIT,
            )

        if chosen.kind in {
            ContributionKind.WAIT,
            ContributionKind.REQUEST_HUMAN,
            ContributionKind.ASK,
        }:
            reason = chosen.rationale
            self.scheduler.defer(goal_id, reason=reason, kind=chosen.kind)
            if chosen.kind == ContributionKind.REQUEST_HUMAN and goal.status == GoalStatus.ACTIVE:
                self._safe_transition(goal_id, GoalStatus.BLOCKED, reason=reason)
            elif (
                chosen.kind in {ContributionKind.WAIT, ContributionKind.ASK}
                and goal.status == GoalStatus.ACTIVE
            ):
                self._safe_transition(goal_id, GoalStatus.WAITING, reason=reason)
            return self._record(
                goal_id,
                CyclePhase.ASSESS,
                gap=gap,
                frontier=frontier,
                notes=reason,
                decided=chosen.kind,
            )

        # Active missions cap.
        active = self._active_missions.get(goal_id, set())
        if len(active) >= self.max_active_missions:
            self.scheduler.defer(goal_id, reason="max_active_missions")
            return self._record(
                goal_id,
                CyclePhase.PROPOSE,
                gap=gap,
                frontier=frontier,
                notes="max_active_missions",
                decided=ContributionKind.WAIT,
            )

        draft = MissionProposalDraft(
            goal_id=goal_id,
            title=chosen.title,
            objective=f"{goal.desired_outcome} :: {chosen.title}",
            kind=chosen.kind,
            dedupe_key=dedupe_key_for(
                goal_id=goal_id,
                kind=chosen.kind,
                title=chosen.title,
                criteria=chosen.addresses_criteria,
            ),
            addresses_criteria=list(chosen.addresses_criteria),
            requested_tools=list(chosen.required_tools),
            requested_providers=list(chosen.required_providers),
            requested_budget_usd=float(chosen.estimated_cost_usd),
        )

        # Anti-duplicate.
        if draft.dedupe_key in self._dedupe:
            draft = draft.model_copy(
                update={"state": "duplicate", "rejection_reason": "duplicate_mission"}
            )
            self.scheduler.note_failure(goal_id, kind=chosen.kind, no_progress=True)
            return self._record(
                goal_id,
                CyclePhase.PROPOSE,
                gap=gap,
                frontier=frontier,
                proposal=draft,
                notes="duplicate_mission",
                decided=chosen.kind,
            )

        draft = admit_proposal(goal, draft)
        if draft.state == "rejected":
            self.scheduler.defer(goal_id, reason=draft.rejection_reason or "rejected")
            if goal.status == GoalStatus.ACTIVE:
                self._safe_transition(
                    goal_id,
                    GoalStatus.WAITING,
                    reason=draft.rejection_reason or "admission_rejected",
                )
            return self._record(
                goal_id,
                CyclePhase.ADMIT,
                gap=gap,
                frontier=frontier,
                proposal=draft,
                notes=draft.rejection_reason or "rejected",
                decided=chosen.kind,
            )

        mission_id = new_id("msn_")
        draft = draft.model_copy(update={"state": "admitted", "mission_id": mission_id})
        self._dedupe[draft.dedupe_key] = draft.proposal_id
        self._active_missions.setdefault(goal_id, set()).add(mission_id)
        if chosen.commitment_key:
            self._commitments.setdefault(goal_id, []).append(chosen.commitment_key)

        outcome = self.executor.execute(draft)
        self._active_missions.get(goal_id, set()).discard(mission_id)

        # Lane C: mission outcome never implies goal achievement.
        self.goals.record_mission_outcome(
            goal_id,
            mission_id=mission_id,
            outcome="succeeded" if outcome.success else "failed",
            actor="pursuit",
            notes=chosen.title,
            evidence_refs=list(outcome.evidence_refs),
        )

        verification = self._verify(goal, outcome)
        for c in verification.newly_met:
            satisfied.add(c)

        strategy = self.lessons.applied_strategy(goal_id, goal.strategy)
        notes = ""
        if verification.invalidated_assumptions:
            strategy = (
                f"{strategy} | invalidate:{','.join(verification.invalidated_assumptions)}".strip(
                    " |"
                )
            )
            notes = "assumptions_invalidated"

        if outcome.success and verification.newly_met:
            self.scheduler.note_success(goal_id, kind=chosen.kind)
        else:
            if not outcome.success and chosen.commitment_key:
                self._failed_approaches.setdefault(goal_id, set()).add(chosen.commitment_key)
            self.scheduler.note_failure(
                goal_id,
                kind=chosen.kind,
                no_progress=not verification.newly_met,
            )

        self.goals.record_progress(
            goal_id,
            summary=f"pursuit:{chosen.kind.value}:{chosen.title}",
            actor="pursuit",
            metrics={
                "mission_id": mission_id,
                "success": outcome.success,
                "newly_met": list(verification.newly_met),
                "still_unmet": list(verification.still_unmet),
            },
        )
        if strategy != goal.strategy:
            self.goals.apply_strategy(
                goal_id,
                strategy=strategy,
                actor="pursuit",
                reason="pursuit_strategy_update",
            )

        # Finite goals only: pursuit may achieve after verified criteria — not via mission alone.
        refreshed = self.goals.get(goal_id)
        criteria = list(refreshed.verification_criteria)
        if (
            refreshed.kind == GoalKind.FINITE
            and criteria
            and all(c in satisfied for c in criteria)
            and refreshed.status == GoalStatus.ACTIVE
        ):
            try:
                self.goals.transition(
                    goal_id,
                    GoalStatus.ACHIEVED,
                    reason="all_verification_criteria_met",
                    actor="pursuit",
                )
            except GoalError:
                notes = (notes + "|achieve_blocked").strip("|")

        return self._record(
            goal_id,
            CyclePhase.UPDATE,
            gap=gap,
            frontier=frontier,
            proposal=draft,
            outcome=outcome,
            verification=verification,
            strategy_after=strategy,
            notes=notes,
            decided=chosen.kind,
        )

    def _verify(self, goal: Goal, outcome: ExecutionOutcome) -> VerificationResult:
        criteria = list(goal.verification_criteria)
        claimed = set(outcome.satisfied_criteria)
        newly = [c for c in criteria if c in claimed]
        still = [
            c for c in criteria if c not in claimed and c not in self._satisfied.get(goal.id, set())
        ]
        # Already satisfied stay met.
        already = self._satisfied.get(goal.id, set())
        still = [c for c in criteria if c not in already and c not in claimed]
        invalidated: list[str] = []
        if not outcome.success and goal.strategy:
            # Evidence of failure can invalidate a named assumption token in strategy.
            for token in goal.strategy.split("|"):
                token = token.strip()
                if token.startswith("assume:") and outcome.failure_class:
                    invalidated.append(token)
        return VerificationResult(
            passed=outcome.success and bool(newly or not criteria),
            checked_criteria=criteria,
            newly_met=newly,
            still_unmet=still,
            invalidated_assumptions=invalidated,
        )

    def _safe_transition(
        self,
        goal_id: str,
        new_status: GoalStatus,
        *,
        reason: str,
    ) -> None:
        try:
            self.goals.transition(goal_id, new_status, reason=reason, actor="pursuit")
        except GoalError:
            return

    def history(self, goal_id: str) -> list[CycleRecord]:
        return list(self._history.get(goal_id, []))

    def commitments(self, goal_id: str) -> list[str]:
        return list(self._commitments.get(goal_id, []))

    def _record(
        self,
        goal_id: str,
        phase: CyclePhase,
        *,
        gap: Any = None,
        frontier: list[Any] | None = None,
        proposal: MissionProposalDraft | None = None,
        outcome: ExecutionOutcome | None = None,
        verification: VerificationResult | None = None,
        strategy_after: str | None = None,
        notes: str = "",
        decided: ContributionKind | None = None,
        meta: dict[str, Any] | None = None,
    ) -> CycleRecord:
        record = CycleRecord(
            goal_id=goal_id,
            phase=phase,
            decided_kind=decided,
            frontier=list(frontier or []),
            gap=gap,
            proposal=proposal,
            outcome=outcome,
            verification=verification,
            strategy_after=strategy_after,
            notes=notes,
            meta=meta or {},
        )
        self._history.setdefault(goal_id, []).append(record)
        return record

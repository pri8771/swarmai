"""Observe→assess→propose→admit→execute→verify→update pursuit engine."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from swarm.contracts.common import new_id
from swarm.goals.models import Goal, GoalError, GoalKind, GoalStatus, GoalStore
from swarm.pursuit.accounting import AccountingError, GoalResourceLedger
from swarm.pursuit.durable_accounting import HoldStore, bind_durable_ledger
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
from swarm.pursuit.state_store import DurablePursuitStateStore
from swarm.pursuit.verification import (
    artifact_digest_for_refs,
    issue_criterion_receipt,
    verify_execution_outcome,
)

if TYPE_CHECKING:
    from swarm.scheduling.singleton import SingletonTicker, TickResult


class MissionExecutor(Protocol):
    def execute(self, proposal: MissionProposalDraft) -> ExecutionOutcome: ...


class ReconcilingExecutor(Protocol):
    def reconcile(self, mission_id: str) -> ExecutionOutcome | None: ...


class RecordingExecutor:
    """Deterministic zero-spend executor for tests and dry runs.

    Successful runs emit protected criterion receipts (verifier-bound digests).
    Bare ``satisfied_criteria`` claims without receipts are not authoritative.
    """

    def __init__(
        self,
        *,
        outcomes: dict[str, ExecutionOutcome] | None = None,
        default_success: bool = True,
        issue_receipts: bool = True,
    ) -> None:
        self.outcomes = outcomes or {}
        self.default_success = default_success
        self.issue_receipts = issue_receipts
        self.calls: list[MissionProposalDraft] = []

    def execute(self, proposal: MissionProposalDraft) -> ExecutionOutcome:
        self.calls.append(proposal)
        if proposal.dedupe_key in self.outcomes:
            return self.outcomes[proposal.dedupe_key]
        mission_id = proposal.mission_id or new_id("msn_")
        if self.default_success:
            evidence_refs = [f"ev:{mission_id}"]
            criteria = list(proposal.addresses_criteria)
            receipts: list[dict[str, Any]] = []
            if self.issue_receipts:
                digest = artifact_digest_for_refs(evidence_refs, mission_id=mission_id)
                for criterion_id in criteria:
                    receipt = issue_criterion_receipt(
                        goal_id=proposal.goal_id,
                        criterion_id=criterion_id,
                        mission_id=mission_id,
                        artifact_digest=digest,
                        evidence_ref=evidence_refs[0],
                    )
                    receipts.append(receipt.model_dump(mode="json"))
            return ExecutionOutcome(
                mission_id=mission_id,
                success=True,
                evidence_refs=evidence_refs,
                # Claims retained for observation; receipts are authoritative.
                satisfied_criteria=criteria,
                criterion_receipts=receipts,
                cost_usd=proposal.admitted_budget_usd,
                model_calls=0,
                tool_calls=0,
                runtime="recording_executor",
            )
        return ExecutionOutcome(
            mission_id=mission_id,
            success=False,
            failure_class="deterministic_failure",
            cost_usd=0.0,
            model_calls=0,
            tool_calls=0,
            runtime="recording_executor",
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
        ledgers: dict[str, GoalResourceLedger] | None = None,
        state_store: DurablePursuitStateStore | None = None,
        state_root: Path | None = None,
        hold_store: HoldStore | None = None,
    ) -> None:
        self.goals = goals
        self.hold_store = hold_store
        if executor is None:
            # R20-01 defense in depth: never default to successful RecordingExecutor.
            from swarm.pursuit.native_dispatch import BlockedMissingImplementationExecutor

            self.executor: MissionExecutor = BlockedMissingImplementationExecutor()
        else:
            self.executor = executor
        self.lessons = lessons or PursuitLessonStore()
        if scheduler is not None:
            self.scheduler = scheduler
        else:
            self.scheduler = PursuitScheduler(clock=clock)
        self.max_active_missions = max_active_missions
        if state_store is not None:
            self.state_store = state_store
        elif state_root is not None:
            self.state_store = DurablePursuitStateStore(state_root)
        else:
            self.state_store = DurablePursuitStateStore(Path(goals.root) / "pursuit_state")
        self._satisfied: dict[str, set[str]] = {}
        self._history: dict[str, list[CycleRecord]] = {}
        self._dedupe: dict[str, str] = {}  # dedupe_key -> proposal_id
        self._failed_approaches: dict[str, set[str]] = {}
        self._active_missions: dict[str, set[str]] = {}
        # mission_id -> proposal draft while awaiting worker + protected verify
        self._pending_missions: dict[str, MissionProposalDraft] = {}
        self._commitments: dict[str, list[str]] = {}  # goal_id -> commitment keys across missions
        self._ledgers: dict[str, GoalResourceLedger] = ledgers or {}
        self._hydrate_all()

    def resource_ledger(self, goal_id: str) -> GoalResourceLedger:
        goal = self.goals.get(goal_id)
        ledger = self._ledgers.get(goal_id)
        if ledger is None:
            ledger = GoalResourceLedger.from_envelope(goal_id, goal.resource_envelope)
            if self.hold_store is not None:
                bind_durable_ledger(ledger, self.hold_store)
            self._ledgers[goal_id] = ledger
        return ledger

    def tick_all_due(self) -> list[CycleRecord]:
        """Tick every active/waiting goal whose schedule is due, in goal-id order."""
        records: list[CycleRecord] = []
        for goal_id in sorted(self.goals.goals):
            goal = self.goals.goals[goal_id]
            if goal.status not in {GoalStatus.ACTIVE, GoalStatus.WAITING}:
                continue
            if goal_id not in self._history:
                self.observe(goal_id)
            if self.scheduler.is_due(goal_id):
                records.append(self.tick(goal_id))
        return records

    def singleton_tick(self, ticker: SingletonTicker) -> TickResult:
        """Run ``tick_all_due`` only while holding the site-wide pursuit epoch."""
        return ticker.run_once(lambda _lease: self.tick_all_due())

    def _hydrate_all(self) -> None:
        """Load on-disk pursuit snapshots for goals already known to GoalStore."""
        for goal in list(self.goals.goals.values()):
            self._hydrate_goal(goal.id)

    def _hydrate_goal(self, goal_id: str) -> None:
        raw = self.state_store.load(goal_id)
        if raw is None:
            return
        self._satisfied[goal_id] = set(raw.get("satisfied_criteria") or [])
        self._history[goal_id] = self.state_store.parse_history(raw)
        dedupe = raw.get("dedupe") or {}
        if isinstance(dedupe, dict):
            self._dedupe.update({str(k): str(v) for k, v in dedupe.items()})
        self._failed_approaches[goal_id] = set(raw.get("failed_approaches") or [])
        self._active_missions[goal_id] = set(raw.get("active_missions") or [])
        self._commitments[goal_id] = list(raw.get("commitments") or [])
        schedule = self.state_store.parse_schedule(raw)
        if schedule is not None:
            self.scheduler.load_state(schedule)

    def _goal_dedupe(self, goal_id: str) -> dict[str, str]:
        goal_dedupe: dict[str, str] = {}
        for rec in self._history.get(goal_id, []):
            if rec.proposal and rec.proposal.dedupe_key:
                key = rec.proposal.dedupe_key
                if key in self._dedupe:
                    goal_dedupe[key] = self._dedupe[key]
        for key, proposal_id in self._dedupe.items():
            if goal_id in key:
                goal_dedupe[key] = proposal_id
        return goal_dedupe

    def _persist_goal(self, goal_id: str) -> None:
        schedule = self.scheduler.dump_states().get(goal_id)
        self.state_store.save(
            goal_id,
            satisfied=self._satisfied.get(goal_id, set()),
            history=self._history.get(goal_id, []),
            dedupe=self._goal_dedupe(goal_id),
            failed_approaches=self._failed_approaches.get(goal_id, set()),
            active_missions=self._active_missions.get(goal_id, set()),
            commitments=self._commitments.get(goal_id, []),
            schedule=schedule,
        )

    def observe(self, goal_id: str) -> Goal:
        if goal_id not in self._history and self.state_store.load(goal_id) is not None:
            self._hydrate_goal(goal_id)
        return self.goals.get(goal_id)

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

        # Reconcile pending native missions before admitting new work.
        pending_cycle = self._reconcile_pending(goal_id)
        if pending_cycle is not None:
            return pending_cycle

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

        ledger = self.resource_ledger(goal_id)
        hold = None
        accounting_notes: list[str] = []
        try:
            hold = ledger.reserve(
                mission_id=mission_id,
                spend_usd=float(draft.admitted_budget_usd),
                model_calls=1 if draft.admitted_providers else 0,
                tool_calls=len(draft.admitted_tools),
                runtime="pursuit",
            )
        except AccountingError as exc:
            self._active_missions.get(goal_id, set()).discard(mission_id)
            self.scheduler.defer(goal_id, reason=f"accounting:{exc}")
            if goal.status == GoalStatus.ACTIVE:
                self._safe_transition(
                    goal_id, GoalStatus.WAITING, reason=f"accounting:{exc}"
                )
            return self._record(
                goal_id,
                CyclePhase.ADMIT,
                gap=gap,
                frontier=frontier,
                proposal=draft,
                notes=f"accounting:{exc}",
                decided=chosen.kind,
                meta={"accounting_error": str(exc)},
            )

        outcome = self.executor.execute(draft)
        pending = self._is_pending_outcome(outcome)
        if pending:
            self._pending_missions[mission_id] = draft
            if hold is not None:
                # A model call already happened before the mission became pending.
                # Preserve unknown usage now so a later mission failure/restart
                # cannot release the reservation as though the call cost nothing.
                if outcome.usage_unknown:
                    ledger.settle(
                        hold.hold_id,
                        spend_usd=float(outcome.cost_usd),
                        model_calls=int(outcome.model_calls),
                        tool_calls=int(outcome.tool_calls),
                        prompt_tokens=outcome.prompt_tokens,
                        completion_tokens=outcome.completion_tokens,
                        route_id=outcome.route_id,
                        runtime=outcome.runtime,
                        usage_unknown=True,
                    )
                    accounting_notes.append("usage_unknown_preserved_pending_mission")
                else:
                    # Known usage still leaves the admitted mission reservation
                    # open until terminal reconciliation.
                    accounting_notes.append("hold_open_pending_mission")
            verification = self._verify(goal, outcome)
            notes = "|".join(accounting_notes + ["submitted_pending"])
            self.scheduler.defer(goal_id, reason="submitted_pending", kind=chosen.kind)
            if goal.status == GoalStatus.ACTIVE:
                self._safe_transition(
                    goal_id, GoalStatus.WAITING, reason="submitted_pending"
                )
            return self._record(
                goal_id,
                CyclePhase.EXECUTE,
                gap=gap,
                frontier=frontier,
                proposal=draft,
                outcome=outcome,
                verification=verification,
                notes=notes,
                decided=chosen.kind,
                meta={"pending_mission_id": mission_id},
            )

        self._active_missions.get(goal_id, set()).discard(mission_id)
        self._pending_missions.pop(mission_id, None)

        if hold is not None:
            try:
                if outcome.usage_unknown:
                    ledger.settle(
                        hold.hold_id,
                        spend_usd=float(outcome.cost_usd),
                        model_calls=int(outcome.model_calls),
                        tool_calls=int(outcome.tool_calls),
                        prompt_tokens=outcome.prompt_tokens,
                        completion_tokens=outcome.completion_tokens,
                        route_id=outcome.route_id,
                        runtime=outcome.runtime,
                        usage_unknown=True,
                    )
                    accounting_notes.append("usage_unknown_preserved")
                else:
                    ledger.settle(
                        hold.hold_id,
                        spend_usd=float(outcome.cost_usd),
                        model_calls=int(outcome.model_calls),
                        tool_calls=int(outcome.tool_calls),
                        prompt_tokens=outcome.prompt_tokens,
                        completion_tokens=outcome.completion_tokens,
                        route_id=outcome.route_id,
                        runtime=outcome.runtime,
                        usage_unknown=False,
                    )
            except AccountingError as exc:
                accounting_notes.append(f"settle:{exc}")
                try:
                    ledger.release(hold.hold_id)
                except AccountingError as inner:
                    accounting_notes.append(f"reconcile:{inner}")

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
        # Only protected newly_met advance progress (never raw worker claims).
        for c in verification.newly_met:
            satisfied.add(c)

        strategy = self.lessons.applied_strategy(goal_id, goal.strategy)
        notes = "|".join(accounting_notes)
        if verification.invalidated_assumptions:
            strategy = (
                f"{strategy} | invalidate:{','.join(verification.invalidated_assumptions)}".strip(
                    " |"
                )
            )
            notes = (notes + "|assumptions_invalidated").strip("|")
        if verification.rejection_reasons:
            notes = (
                notes + "|" + ",".join(verification.rejection_reasons[:3])
            ).strip("|")

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
                "verification_passed": verification.passed,
                "accounting": ledger.snapshot(),
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
            # Storage truth: claim-only / RecordingExecutor achievement is synthetic.
            # Protected verifier receipts (L5) may pass achievement_authority="verified".
            authority = "synthetic"
            protected = getattr(verification, "protected_receipt_id", None)
            if verification.passed and protected:
                authority = "verified"
            try:
                self.goals.transition(
                    goal_id,
                    GoalStatus.ACHIEVED,
                    reason="all_verification_criteria_met",
                    actor="pursuit",
                    achievement_authority=authority,
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
            meta={"accounting": ledger.snapshot()} if hold is not None else {},
        )

    def _is_pending_outcome(self, outcome: ExecutionOutcome) -> bool:
        if outcome.success:
            return False
        return (outcome.failure_class or "") in {
            "submitted_pending",
            "pending",
            "awaiting_worker",
            "awaiting_verify",
        }

    def _reconcile_pending(self, goal_id: str) -> CycleRecord | None:
        """If a native mission is pending, poll reconcile before admitting new work."""
        active = list(self._active_missions.get(goal_id, set()))
        if not active:
            return None
        reconcile = getattr(self.executor, "reconcile", None)
        if not callable(reconcile):
            return None

        goal = self.goals.get(goal_id)
        satisfied = self._satisfied.setdefault(goal_id, set())
        for mission_id in active:
            draft = self._pending_missions.get(mission_id)
            outcome = reconcile(mission_id)
            if outcome is None:
                self.scheduler.defer(goal_id, reason="awaiting_pending_mission")
                return self._record(
                    goal_id,
                    CyclePhase.EXECUTE,
                    notes="awaiting_pending_mission",
                    decided=ContributionKind.WAIT,
                    meta={"pending_mission_id": mission_id},
                    proposal=draft,
                )

            # Terminal — drop pending slot and apply verify/update path.
            self._active_missions.get(goal_id, set()).discard(mission_id)
            self._pending_missions.pop(mission_id, None)
            ledger = self.resource_ledger(goal_id)
            # Release any leftover hold for this mission (best-effort).
            for hold in list(ledger.holds.values()):
                if hold.mission_id != mission_id or hold.state != "held":
                    continue
                try:
                    if outcome.success:
                        ledger.settle(
                            hold.hold_id,
                            spend_usd=float(outcome.cost_usd),
                            model_calls=int(outcome.model_calls),
                            tool_calls=int(outcome.tool_calls),
                            prompt_tokens=outcome.prompt_tokens,
                            completion_tokens=outcome.completion_tokens,
                            route_id=outcome.route_id,
                            runtime=outcome.runtime,
                            usage_unknown=outcome.usage_unknown,
                        )
                    else:
                        ledger.release(hold.hold_id)
                except AccountingError:
                    pass

            self.goals.record_mission_outcome(
                goal_id,
                mission_id=mission_id,
                outcome="succeeded" if outcome.success else "failed",
                actor="pursuit",
                notes=(draft.title if draft else "reconcile"),
                evidence_refs=list(outcome.evidence_refs),
            )
            verification = self._verify(goal, outcome)
            for c in verification.newly_met:
                satisfied.add(c)

            kind = draft.kind if draft else ContributionKind.ACT
            if outcome.success and verification.newly_met:
                self.scheduler.note_success(goal_id, kind=kind)
            else:
                self.scheduler.note_failure(
                    goal_id, kind=kind, no_progress=not verification.newly_met
                )

            self.goals.record_progress(
                goal_id,
                summary=f"pursuit:reconcile:{mission_id}",
                actor="pursuit",
                metrics={
                    "mission_id": mission_id,
                    "success": outcome.success,
                    "newly_met": list(verification.newly_met),
                    "still_unmet": list(verification.still_unmet),
                    "verification_passed": verification.passed,
                },
            )

            if goal.status == GoalStatus.WAITING:
                self._safe_transition(goal_id, GoalStatus.ACTIVE, reason="mission_reconciled")

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
                    pass

            return self._record(
                goal_id,
                CyclePhase.UPDATE,
                proposal=draft,
                outcome=outcome,
                verification=verification,
                notes="reconciled_pending_mission",
                decided=kind,
                meta={"reconciled_mission_id": mission_id},
            )
        return None

    def _verify(self, goal: Goal, outcome: ExecutionOutcome) -> VerificationResult:
        return verify_execution_outcome(
            goal,
            outcome,
            already_satisfied=self._satisfied.get(goal.id, set()),
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
        if goal_id not in self._history:
            self._hydrate_goal(goal_id)
        return list(self._history.get(goal_id, []))

    def commitments(self, goal_id: str) -> list[str]:
        if goal_id not in self._commitments:
            self._hydrate_goal(goal_id)
        return list(self._commitments.get(goal_id, []))

    def satisfied_criteria(self, goal_id: str) -> set[str]:
        if goal_id not in self._satisfied:
            self._hydrate_goal(goal_id)
        return set(self._satisfied.get(goal_id, set()))

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
        self._persist_goal(goal_id)
        return record

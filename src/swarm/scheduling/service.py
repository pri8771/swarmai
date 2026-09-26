"""V2.3 SchedulerService — the single dispatch authority (ART-V23-MULTIMISSION_SCHEDULER).

One ``schedule_once`` call is one decision:

1. hold the scheduler epoch (``SchedulerEpochService``); a non-holder decides nothing;
2. check the site epoch (``SiteAuthorityService``) when configured;
3. drop tasks whose ``attempt_id`` already has an intent (duplicate dispatch);
4. ``wdrr.select_next`` over durable project/mission state;
5. reserve every component through ``DispatchIntentService`` (all-or-nothing);
6. re-check the epoch, then persist credits/running counts with optimistic versions;
7. append a ``SchedulingDecisionReceipt`` and emit a ``scheduler.decision`` ops event.

A failed reservation changes no credit (broker denial beats scheduler credit).
``running`` counters always equal the number of non-terminal intents; ``recover``
recomputes them after a crash and expires stale PREPARED/RESERVED intents.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from swarm.contracts.common import utc_now
from swarm.contracts.v23 import (
    TERMINAL_INTENT_STATES,
    DispatchIntent,
    DispatchIntentComponent,
    DispatchIntentState,
    MissionQueueLifecycle,
    MissionQueueState,
    PriorityClass,
    ProjectQueueState,
    ReasonCode,
    SchedulableTask,
    SchedulerDecision,
    SchedulerEpochLease,
    SchedulingDecisionReceipt,
    SchedulingStore,
    StaleVersionError,
)
from swarm.observability.ops_events import OpsEventLog
from swarm.recovery.authority import SiteAuthorityService, StaleEpochError
from swarm.scheduling.dispatch_intent import DispatchIntentService, ReleaseFn, ReserveFn
from swarm.scheduling.epoch import (
    EpochHeldError,
    SchedulerEpochService,
    StaleSchedulerEpochError,
)
from swarm.scheduling.wdrr import (
    ResourceCheck,
    Selection,
    WdrrConfig,
    apply_selection,
    clamp_restart_credit,
    select_next,
)

Clock = Callable[[], datetime]
ComponentsFor = Callable[[SchedulableTask], list[DispatchIntentComponent]]


class SchedulerServiceError(RuntimeError):
    pass


def default_components(task: SchedulableTask) -> list[DispatchIntentComponent]:
    comps: list[DispatchIntentComponent] = []
    if task.provider_route:
        comps.append(DispatchIntentComponent(kind="provider", ref=task.provider_route))
    comps.append(DispatchIntentComponent(kind="worker", ref=task.worker_class))
    if task.tool_units > 0:
        comps.append(DispatchIntentComponent(kind="tool", ref="gateway", amount=task.tool_units))
    return comps


@dataclass(frozen=True)
class ScheduleOutcome:
    decision: SchedulerDecision
    reason_code: ReasonCode
    receipt: SchedulingDecisionReceipt | None = None
    intent: DispatchIntent | None = None
    task: SchedulableTask | None = None


@dataclass(frozen=True)
class ResultVerdict:
    accepted: bool
    reason: str
    intent: DispatchIntent | None = None


class SchedulerService:
    def __init__(
        self,
        store: SchedulingStore,
        *,
        epochs: SchedulerEpochService,
        holder_id: str,
        reserve: ReserveFn,
        release: ReleaseFn,
        config: WdrrConfig | None = None,
        site_id: str = "local",
        site_authority: SiteAuthorityService | None = None,
        ops: OpsEventLog | None = None,
        clock: Clock | None = None,
        intent_ttl_seconds: float = 30.0,
        resource_available: ResourceCheck | None = None,
        components_for: ComponentsFor | None = None,
    ) -> None:
        self.store = store
        self.epochs = epochs
        self.holder_id = holder_id
        self.config = config or WdrrConfig()
        self.site_id = site_id
        self.site_authority = site_authority
        self.ops = ops
        self._clock: Clock = clock or utc_now
        self._release = release
        self.resource_available = resource_available
        self.components_for: ComponentsFor = components_for or default_components
        self.intents = DispatchIntentService(
            store, reserve=reserve, release=release, clock=self._clock,
            ttl_seconds=intent_ttl_seconds,
        )

    # ------------------------------------------------------------------ registry
    def register_project(
        self,
        project_id: str,
        *,
        tenant_id: str = "default",
        weight: float = 1.0,
        max_concurrency: int = 4,
    ) -> ProjectQueueState:
        existing = self.store.get_project(project_id)
        if existing is not None:
            return existing
        state = ProjectQueueState(
            project_id=project_id,
            tenant_id=tenant_id,
            weight=weight,
            max_concurrency=max_concurrency,
            policy_version=self.config.policy_version,
        )
        return self.store.put_project(state, expected_version=None)

    def register_mission(
        self,
        mission_id: str,
        project_id: str,
        *,
        priority: PriorityClass = PriorityClass.NORMAL,
        weight: float = 1.0,
        max_parallelism: int = 2,
        deadline_at: datetime | None = None,
    ) -> MissionQueueState:
        if self.store.get_project(project_id) is None:
            raise SchedulerServiceError(f"project_not_registered:{project_id}")
        existing = self.store.get_mission(mission_id)
        if existing is not None:
            if existing.project_id != project_id:
                raise SchedulerServiceError("mission_project_mismatch")
            return existing
        state = MissionQueueState(
            mission_id=mission_id,
            project_id=project_id,
            priority=priority,
            weight=weight,
            max_parallelism=max_parallelism,
            deadline_at=deadline_at,
            enqueued_at=self._clock(),
        )
        return self.store.put_mission(state, expected_version=None)

    def _update_project(self, project_id: str, **update: Any) -> ProjectQueueState:
        cur = self.store.get_project(project_id)
        if cur is None:
            raise SchedulerServiceError(f"project_not_registered:{project_id}")
        update["updated_at"] = self._clock()
        return self.store.put_project(cur.model_copy(update=update), expected_version=cur.version)

    def set_weight(self, project_id: str, weight: float) -> ProjectQueueState:
        if weight <= 0:
            raise SchedulerServiceError("weight_must_be_positive")
        return self._update_project(project_id, weight=float(weight))

    def pause_project(self, project_id: str) -> ProjectQueueState:
        return self._update_project(project_id, paused=True)

    def resume_project(self, project_id: str) -> ProjectQueueState:
        return self._update_project(project_id, paused=False)

    def cancel_mission(self, mission_id: str) -> MissionQueueState:
        cur = self.store.get_mission(mission_id)
        if cur is None:
            raise SchedulerServiceError(f"mission_not_registered:{mission_id}")
        updated = self.store.put_mission(
            cur.model_copy(
                update={
                    "lifecycle": MissionQueueLifecycle.CANCELLED,
                    "cancellation_generation": cur.cancellation_generation + 1,
                    "updated_at": self._clock(),
                }
            ),
            expected_version=cur.version,
        )
        pending = frozenset({DispatchIntentState.PREPARED, DispatchIntentState.RESERVED})
        for intent in self.store.list_intents(states=pending):
            if intent.mission_id == mission_id:
                self.intents.cancel(intent.intent_id, reason="mission_cancelled")
                self._decrement_running(intent)
        return self.store.get_mission(mission_id) or updated

    # ------------------------------------------------------------------ deciding
    def _site_epoch(self, requested: int | None) -> int:
        if self.site_authority is None:
            return requested or 0
        current = self.site_authority.current(self.site_id).epoch
        epoch = current if requested is None else requested
        self.site_authority.require_epoch(self.site_id, epoch, action="schedule")
        return epoch

    def _record(
        self,
        *,
        selection: Selection | None,
        decision: SchedulerDecision,
        reason: ReasonCode,
        lease: SchedulerEpochLease,
        site_epoch: int,
        task: SchedulableTask | None = None,
        intent: DispatchIntent | None = None,
        detail: dict[str, Any] | None = None,
    ) -> SchedulingDecisionReceipt:
        receipt = SchedulingDecisionReceipt(
            sequence=self.store.next_sequence(),
            decision=decision,
            reason_code=reason,
            project_id=task.project_id if task else None,
            mission_id=task.mission_id if task else None,
            task_id=task.task_id if task else None,
            attempt_id=task.attempt_id if task else None,
            policy_version=self.config.policy_version,
            site_id=self.site_id,
            site_epoch=site_epoch,
            scheduler_epoch=lease.epoch,
            candidate_set_hash=selection.candidate_set_hash if selection else "",
            scores=dict(selection.scores) if selection else {},
            credits_before=dict(selection.credits_before) if selection else {},
            credits_after=dict(selection.credits_after) if selection else {},
            dispatch_intent_id=intent.intent_id if intent else None,
            detail=dict(detail or {}),
            created_at=self._clock(),
        )
        self.store.append_receipt(receipt)
        if self.ops is not None:
            self.ops.emit(
                "scheduler.decision",
                "scheduler",
                project_id=receipt.project_id,
                site_epoch=site_epoch,
                correlation_id=receipt.receipt_id,
                trace_id=receipt.mission_id,
                detail={
                    "decision": decision.value,
                    "reason_code": reason.value,
                    "sequence": receipt.sequence,
                    "attempt_id": receipt.attempt_id,
                    "scheduler_epoch": lease.epoch,
                },
            )
        return receipt

    def schedule_once(
        self, tasks: Sequence[SchedulableTask], *, site_epoch: int | None = None
    ) -> ScheduleOutcome:
        try:
            lease = self.epochs.acquire(self.holder_id)
            lease = self.epochs.renew(lease)
        except (EpochHeldError, StaleSchedulerEpochError):
            return ScheduleOutcome(SchedulerDecision.DENY, ReasonCode.STALE_SCHEDULER_EPOCH)
        try:
            s_epoch = self._site_epoch(site_epoch)
        except StaleEpochError as exc:
            receipt = self._record(
                selection=None,
                decision=SchedulerDecision.DENY,
                reason=ReasonCode.STALE_SITE_EPOCH,
                lease=lease,
                site_epoch=site_epoch or 0,
                detail={"error": str(exc)[:200]},
            )
            return ScheduleOutcome(SchedulerDecision.DENY, ReasonCode.STALE_SITE_EPOCH, receipt)

        fresh = [t for t in tasks if self.store.get_intent_by_attempt(t.attempt_id) is None]
        duplicates = len(tasks) - len(fresh)
        projects = self.store.list_projects()
        missions = self.store.list_missions()
        selection = select_next(
            projects,
            missions,
            fresh,
            now=self._clock(),
            config=self.config,
            resource_available=self.resource_available,
        )
        if selection.decision != SchedulerDecision.ADMIT or selection.task is None:
            receipt = self._record(
                selection=selection,
                decision=selection.decision,
                reason=selection.reason_code,
                lease=lease,
                site_epoch=s_epoch,
                detail={"blocked": selection.blocked, "duplicates": duplicates},
            )
            return ScheduleOutcome(selection.decision, selection.reason_code, receipt)

        task = selection.task
        mission = next(m for m in missions if m.mission_id == task.mission_id)
        intent = self.intents.prepare(
            attempt_id=task.attempt_id,
            project_id=task.project_id,
            mission_id=task.mission_id,
            task_id=task.task_id,
            components=self.components_for(task),
            site_epoch=s_epoch,
            scheduler_epoch=lease.epoch,
            cancellation_generation=mission.cancellation_generation,
        )
        if intent.state != DispatchIntentState.RESERVED:
            receipt = self._record(
                selection=None,
                decision=SchedulerDecision.DEFER,
                reason=ReasonCode.RESERVATION_FAILED,
                lease=lease,
                site_epoch=s_epoch,
                task=task,
                intent=intent,
                detail={"failure_reason": intent.failure_reason},
            )
            return ScheduleOutcome(
                SchedulerDecision.DEFER, ReasonCode.RESERVATION_FAILED, receipt, intent, task
            )

        try:
            self.epochs.require_current(epoch=lease.epoch, holder_id=self.holder_id)
        except StaleSchedulerEpochError:
            self.intents.cancel(intent.intent_id, reason="scheduler_epoch_lost")
            return ScheduleOutcome(SchedulerDecision.DENY, ReasonCode.STALE_SCHEDULER_EPOCH)

        sequence = self.store.next_sequence()
        new_projects, new_missions = apply_selection(
            projects, missions, selection, sequence=sequence
        )
        try:
            self._persist_changed(projects, new_projects, missions, new_missions)
        except StaleVersionError:
            self.intents.cancel(intent.intent_id, reason="state_version_conflict")
            return ScheduleOutcome(SchedulerDecision.DENY, ReasonCode.DUPLICATE_DISPATCH)

        receipt = self._record(
            selection=selection,
            decision=SchedulerDecision.ADMIT,
            reason=ReasonCode.ADMITTED,
            lease=lease,
            site_epoch=s_epoch,
            task=task,
            intent=intent,
            detail={"selection_sequence": sequence, "duplicates": duplicates},
        )
        return ScheduleOutcome(SchedulerDecision.ADMIT, ReasonCode.ADMITTED, receipt, intent, task)

    def _persist_changed(
        self,
        old_p: Sequence[ProjectQueueState],
        new_p: Sequence[ProjectQueueState],
        old_m: Sequence[MissionQueueState],
        new_m: Sequence[MissionQueueState],
    ) -> None:
        now = self._clock()
        skip = {"updated_at"}
        for before, after in zip(old_p, new_p, strict=True):
            if after.model_dump(exclude=skip) != before.model_dump(exclude=skip):
                self.store.put_project(
                    after.model_copy(update={"updated_at": now}), expected_version=before.version
                )
        for before_m, after_m in zip(old_m, new_m, strict=True):
            if after_m.model_dump(exclude=skip) != before_m.model_dump(exclude=skip):
                self.store.put_mission(
                    after_m.model_copy(update={"updated_at": now}),
                    expected_version=before_m.version,
                )

    # ------------------------------------------------------------------ results
    def mark_dispatched(self, intent_id: str) -> DispatchIntent:
        return self.intents.mark_dispatched(intent_id)

    def _stale_reason(self, intent: DispatchIntent, generation: int | None) -> str | None:
        mission = self.store.get_mission(intent.mission_id)
        if (
            mission is None
            or mission.lifecycle == MissionQueueLifecycle.CANCELLED
            or mission.cancellation_generation != intent.cancellation_generation
            or (generation is not None and generation != intent.cancellation_generation)
        ):
            return "stale_generation"
        if self.site_authority is not None:
            try:
                self.site_authority.require_epoch(self.site_id, intent.site_epoch, action="result")
            except StaleEpochError:
                return "stale_site_epoch"
        current = self.epochs.current()
        if current is not None and current.epoch != intent.scheduler_epoch:
            return "stale_scheduler_epoch"
        return None

    def finish(
        self, intent_id: str, *, cancellation_generation: int | None = None
    ) -> ResultVerdict:
        """Worker result returned: release reservations; accept only if not fenced."""
        intent = self.store.get_intent(intent_id)
        if intent is None:
            raise SchedulerServiceError(f"intent_missing:{intent_id}")
        if intent.state in TERMINAL_INTENT_STATES:
            return ResultVerdict(False, "already_terminal", intent)
        stale = self._stale_reason(intent, cancellation_generation)
        if intent.state == DispatchIntentState.DISPATCHED:
            for comp in reversed(intent.components):
                if comp.reserved:
                    self._release(intent, comp)
            released = [c.model_copy(update={"reserved": False}) for c in intent.components]
            done = self.store.put_intent(
                intent.model_copy(
                    update={
                        "state": DispatchIntentState.COMPLETED,
                        "components": released,
                        "failure_reason": stale,
                        "updated_at": self._clock(),
                    }
                ),
                expected_version=intent.version,
            )
        else:
            done = self.intents.cancel(intent_id, reason=stale or "finished_before_dispatch")
        self._decrement_running(intent)
        if self.ops is not None:
            self.ops.emit(
                "attempt.finished",
                "scheduler",
                project_id=intent.project_id,
                trace_id=intent.mission_id,
                detail={"attempt_id": intent.attempt_id, "accepted": stale is None,
                        "reason": stale or "accepted"},
            )
        return ResultVerdict(stale is None, stale or "accepted", done)

    def _decrement_running(self, intent: DispatchIntent) -> None:
        p = self.store.get_project(intent.project_id)
        if p is not None and p.running > 0:
            self.store.put_project(
                p.model_copy(update={"running": p.running - 1, "updated_at": self._clock()}),
                expected_version=p.version,
            )
        m = self.store.get_mission(intent.mission_id)
        if m is not None and m.running > 0:
            self.store.put_mission(
                m.model_copy(update={"running": m.running - 1, "updated_at": self._clock()}),
                expected_version=m.version,
            )

    # ------------------------------------------------------------------ restart
    def recover(self) -> dict[str, Any]:
        """After a restart: expire stale intents, clamp positive credit, recount running."""
        expired = self.intents.recover_expired()
        live = [
            i for i in self.store.list_intents() if i.state not in TERMINAL_INTENT_STATES
        ]
        by_project: dict[str, int] = {}
        by_mission: dict[str, int] = {}
        for i in live:
            by_project[i.project_id] = by_project.get(i.project_id, 0) + 1
            by_mission[i.mission_id] = by_mission.get(i.mission_id, 0) + 1
        projects = self.store.list_projects()
        clamped = {p.project_id: p for p in clamp_restart_credit(projects, self.config)}
        for p in projects:
            target = clamped[p.project_id].model_copy(
                update={"running": by_project.get(p.project_id, 0)}
            )
            if target.credit != p.credit or target.running != p.running:
                self.store.put_project(
                    target.model_copy(update={"updated_at": self._clock()}),
                    expected_version=p.version,
                )
        for m in self.store.list_missions():
            want = by_mission.get(m.mission_id, 0)
            if m.running != want:
                self.store.put_mission(
                    m.model_copy(update={"running": want, "updated_at": self._clock()}),
                    expected_version=m.version,
                )
        return {
            "expired_intents": [i.intent_id for i in expired],
            "live_intents": len(live),
        }

    def queues(self) -> list[dict[str, Any]]:
        return [
            {
                "project_id": p.project_id,
                "tenant_id": p.tenant_id,
                "weight": p.weight,
                "credit": p.credit,
                "running": p.running,
                "max_concurrency": p.max_concurrency,
                "paused": p.paused,
                "version": p.version,
            }
            for p in sorted(self.store.list_projects(), key=lambda x: x.project_id)
        ]

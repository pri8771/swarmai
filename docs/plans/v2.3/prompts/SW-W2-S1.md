# SW-W2-S1 — SchedulerService (WDRR + store + intents + epochs + site epoch + receipts + ops events) + pathological suite

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W2-S1` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v23-w2-s1-scheduler-service` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 2 |
| Depends on | SW-W1-S1, SW-W1-S2, SW-W1-S3, SW-W1-S4, SW-W1-S7, SW-W1-S8 |
| Handoff file | `docs/v2.3/sessions/SW-W2-S1.md` |
| Independent reviewer | Codex (owner decision D2). You never accept your own work. |
| Plan | `docs/plans/v2.3/PLAN.md`; owner preflight `docs/plans/v2.3/OWNER_PREFLIGHT.md`; decisions `docs/swarm-mvp/DECISIONS.md` |

## 0. Hard rules (read twice)
1. Edit **only** the files listed in “Files you own” plus your handoff file. If another file must change, do not change it: write the exact change under “Needs other owner” in the handoff.
2. Never push to, or merge into, `main`, `dev` or `cursor/sw-v23-integration-460c`. Never merge any PR, never force-push, never rewrite history, never delete branches. Only the wave MERGE prompts (`SW-MERGE-*`) push to `cursor/sw-v23-integration-460c`.
3. Zero spend: no real model/provider calls, no paid APIs, no account creation, no deploys. `SWARM_ALLOW_PAID` stays `false`. Tests use fakes only.
4. Never commit or print secrets, tokens, `.env` files, customer data or raw logs. Test tokens are fake literals such as `atk_policy_demo`. Check environment variables only with `test -n "$NAME"`.
5. Passing tests are *not* acceptance. Never write “accepted”, “complete”, “released” or “V2.3 done”. Use “implemented” and “tested”.
6. `src/swarm/contracts/v23.py`, `src/swarm/db/models.py` and `migrations/` belong to SW-W0-S2. Import from them; never edit them (unless you *are* SW-W0-S2).
7. Do not edit `.github/workflows/`, `pyproject.toml`, `uv.lock`, `package.json` or lockfiles.
8. If a step can be read two ways, choose the reading that changes fewer lines inside your own files, and write the choice under “Decisions” in the handoff.

## 1. Setup
```bash
git status --porcelain            # must print nothing; otherwise STOP (S1)
git fetch origin cursor/sw-v23-integration-460c
git ls-remote --exit-code origin refs/heads/cursor/sw-v23-integration-460c >/dev/null && echo INTEG_OK || echo INTEG_MISSING
```
If it prints `INTEG_MISSING`, STOP (S2): SW-W0-S1 or the executor creates it.
```bash
git checkout -b cursor/v23-w2-s1-scheduler-service origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
Depends on: SW-W1-S1, SW-W1-S2, SW-W1-S3, SW-W1-S4, SW-W1-S7, SW-W1-S8. Their PRs must already be merged into `cursor/sw-v23-integration-460c` (by the wave MERGE prompt).
Run every command below. Each must print `OK`. If any prints `MISSING`, STOP (condition S2 in section 10).

```bash
git fetch origin cursor/sw-v23-integration-460c
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/scheduling/wdrr.py && echo "OK src/swarm/scheduling/wdrr.py" || echo "MISSING src/swarm/scheduling/wdrr.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/scheduling/store.py && echo "OK src/swarm/scheduling/store.py" || echo "MISSING src/swarm/scheduling/store.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/scheduling/dispatch_intent.py && echo "OK src/swarm/scheduling/dispatch_intent.py" || echo "MISSING src/swarm/scheduling/dispatch_intent.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/scheduling/epoch.py && echo "OK src/swarm/scheduling/epoch.py" || echo "MISSING src/swarm/scheduling/epoch.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/observability/trace_graph.py && echo "OK src/swarm/observability/trace_graph.py" || echo "MISSING src/swarm/observability/trace_graph.py"
```

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `src/swarm/scheduling/service.py` — create
- `src/swarm/controller/resource_allocator.py` — modify
- `tests/controller/v23_harness.py` — create
- `tests/controller/test_v23_service.py` — create
- `tests/controller/test_v23_pathological.py` — create
- `tests/integration/db/test_v23_service_restart_sql.py` — create
- `docs/v2.3/sessions/SW-W2-S1.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Implement ART-V23-MULTIMISSION_SCHEDULER end to end.
- Today `controller/resource_allocator.py` is a "V3.0" shim that reserves directly without a durable fair scheduler.
- This session adds `SchedulerService`, the **single dispatch authority**, composing the Wave-1 building blocks:
  - `wdrr.select_next` / `apply_selection` (SW-W1-S1).
  - `SchedulingStore`, in-memory (SW-W0-S2) or SQL (SW-W1-S2).
  - `DispatchIntentService` (SW-W1-S3).
  - `SchedulerEpochService` (SW-W1-S4).
  - `SiteAuthorityService` (existing `swarm.recovery.authority`).
  - `OpsEventLog` (SW-W1-S8).
- It proves the **11 required pathological cases** and the restart case.

**Semantics** (keep them; later sessions rely on them):
- `schedule_once(tasks)` makes exactly one decision. A process that does not hold the scheduler epoch gets `DENY / stale_scheduler_epoch` and writes nothing.
- Tasks whose `attempt_id` already has an intent are dropped, so duplicates can never double-reserve.
- A failed reservation gives `DEFER / reservation_failed`, compensates every reserved component, and changes **no** credit.
- `running` counters always equal the number of non-terminal intents; `recover()` expires stale intents, clamps positive credit, and recounts.
- `finish(intent_id)` releases reservations. It returns `accepted=False` with `stale_generation`, `stale_site_epoch` or `stale_scheduler_epoch` when the result is fenced.
- `ResourceAllocator(..., scheduler=svc)` routes through the service; without `scheduler` the legacy path is byte-for-byte unchanged, so `tests/controller/test_v23_v20.py` still passes.

The code below was compiled and run against `dev @ 8e1c0fde` plus every Wave-1 dependency. `tests/controller` gives 73 passed (17 new), the restart integration test gives 1 passed, and ruff and mypy are clean. Paste it **exactly**.

### Step 1 — `src/swarm/scheduling/service.py` (create, exactly)
```python
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
```

### Step 2 — `src/swarm/controller/resource_allocator.py` (replace the whole file, exactly)
```python
"""V3.0 resource allocator — feeds V2.3 scheduler, no parallel authority.

With ``scheduler`` set, every allocation is one ``SchedulerService.schedule_once``
decision (durable credit, intents, epochs and receipts). Without it, the legacy
fixture path below is used unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from swarm.controller.fairness import DurableFairnessStore
from swarm.controller.reservations import ReservationComponent, ReservationService
from swarm.controller.scheduling_receipts import SchedulingReceiptLog

if TYPE_CHECKING:
    from swarm.scheduling.service import SchedulerService


class AllocationDenied(PermissionError):
    pass


@dataclass
class AllocationRequest:
    project_id: str
    mission_id: str
    attempt_id: str
    worker_class: str = "local"
    provider_route: str = "rt_ollama_default"
    tool_units: float = 0.0


class ResourceAllocator:
    def __init__(
        self,
        *,
        fairness: DurableFairnessStore,
        reservations: ReservationService,
        receipts: SchedulingReceiptLog,
        site_epoch: int,
        scheduler: SchedulerService | None = None,
    ) -> None:
        self.fairness = fairness
        self.reservations = reservations
        self.receipts = receipts
        self.site_epoch = site_epoch
        self.scheduler = scheduler

    def _allocate_v23(self, req: AllocationRequest) -> dict[str, object]:
        from swarm.contracts.v23 import SchedulableTask, SchedulerDecision

        assert self.scheduler is not None
        self.scheduler.register_project(req.project_id)
        self.scheduler.register_mission(req.mission_id, req.project_id)
        task = SchedulableTask(
            task_id=req.attempt_id,
            mission_id=req.mission_id,
            project_id=req.project_id,
            attempt_id=req.attempt_id,
            worker_class=req.worker_class,
            provider_route=req.provider_route,
            tool_units=req.tool_units,
        )
        out = self.scheduler.schedule_once([task])
        if out.decision != SchedulerDecision.ADMIT or out.intent is None or out.receipt is None:
            raise AllocationDenied(f"allocation_{out.decision.value}:{out.reason_code.value}")
        return {
            "intent": out.intent.model_dump(mode="json"),
            "receipt": out.receipt.model_dump(mode="json"),
        }

    def allocate(self, req: AllocationRequest) -> dict[str, object]:
        if self.scheduler is not None:
            return self._allocate_v23(req)
        ranked = self.fairness.rank_projects([req.project_id])
        if not ranked or ranked[0] != req.project_id and len(ranked) > 1:
            # Still allow single-project; multi-project fairness recorded.
            pass
        components = [
            ReservationComponent(kind="worker", resource_id=req.worker_class, units=1.0),
            ReservationComponent(kind="provider", resource_id=req.provider_route, units=1.0),
        ]
        if req.tool_units:
            components.append(
                ReservationComponent(kind="tool", resource_id="gateway", units=req.tool_units)
            )
        intent = self.reservations.reserve(
            project_id=req.project_id,
            mission_id=req.mission_id,
            attempt_id=req.attempt_id,
            site_epoch=self.site_epoch,
            components=components,
        )
        st = self.fairness.note_dispatch(req.project_id)
        receipt = self.receipts.record(
            site_epoch=self.site_epoch,
            project_id=req.project_id,
            mission_id=req.mission_id,
            decision="dispatch",
            reason="allocator_v30",
            fairness_debt=st.fairness_debt,
            reservation_intent_id=intent.intent_id,
        )
        return {"intent": intent.to_dict(), "receipt": receipt.to_dict()}
```

### Step 3 — `tests/controller/v23_harness.py` (create, exactly; shared helper, not a test module)
```python
"""Shared offline harness for SchedulerService tests (not a test module)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from swarm.contracts.v23 import DispatchIntent, DispatchIntentComponent, SchedulableTask
from swarm.observability import OpsEventLog
from swarm.recovery.authority import SiteAuthorityService
from swarm.scheduling.epoch import InMemorySchedulerEpochService
from swarm.scheduling.memory_store import InMemorySchedulingStore
from swarm.scheduling.service import SchedulerService


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now = self.now + timedelta(seconds=seconds)


class Broker:
    """Capacity per (kind, ref). Missing key = unlimited. Reserve raises when exhausted."""

    def __init__(self, capacity: dict[tuple[str, str], float] | None = None) -> None:
        self.capacity = dict(capacity or {})
        self.used: dict[tuple[str, str], float] = {}
        self.log: list[tuple[str, str, str, str]] = []
        self._n = 0

    def reserve(self, intent: DispatchIntent, comp: DispatchIntentComponent) -> str:
        key = (comp.kind, comp.ref)
        used = self.used.get(key, 0.0)
        if key in self.capacity and used + comp.amount > self.capacity[key] + 1e-9:
            raise RuntimeError(f"capacity_exhausted:{comp.kind}:{comp.ref}")
        self.used[key] = used + comp.amount
        self._n += 1
        self.log.append(("reserve", comp.kind, comp.ref, intent.attempt_id))
        return f"rsv_{self._n}"

    def release(self, intent: DispatchIntent, comp: DispatchIntentComponent) -> None:
        key = (comp.kind, comp.ref)
        self.used[key] = max(0.0, self.used.get(key, 0.0) - comp.amount)
        self.log.append(("release", comp.kind, comp.ref, intent.attempt_id))

    def outstanding(self) -> float:
        return sum(self.used.values())


def make_service(
    *,
    store: InMemorySchedulingStore | None = None,
    epochs: InMemorySchedulerEpochService | None = None,
    broker: Broker | None = None,
    clock: Clock | None = None,
    holder_id: str = "sched_a",
    site_authority: SiteAuthorityService | None = None,
    **kw: object,
) -> tuple[SchedulerService, InMemorySchedulingStore, Broker, Clock]:
    clock = clock or Clock()
    store = store or InMemorySchedulingStore()
    broker = broker or Broker()
    epochs = epochs or InMemorySchedulerEpochService(clock=clock)
    svc = SchedulerService(
        store,
        epochs=epochs,
        holder_id=holder_id,
        reserve=broker.reserve,
        release=broker.release,
        clock=clock,
        site_authority=site_authority,
        ops=OpsEventLog(),
        **kw,  # type: ignore[arg-type]
    )
    return svc, store, broker, clock


def task(
    project_id: str, mission_id: str, n: int, **kw: object
) -> SchedulableTask:
    return SchedulableTask(
        task_id=f"{mission_id}_t{n}",
        mission_id=mission_id,
        project_id=project_id,
        attempt_id=f"att_{mission_id}_{n}",
        enqueued_at=datetime(2026, 9, 25, 11, 0, tzinfo=UTC),
        **kw,  # type: ignore[arg-type]
    )


def run_share(
    svc: SchedulerService,
    demand: dict[str, list[str]],
    *,
    decisions: int,
    finish: bool = True,
    **task_kw: object,
) -> dict[str, int]:
    """Constant demand: every mission always has one fresh runnable task. Returns admits/project."""
    counts = {p: 0 for p in demand}
    n = 0
    for _ in range(decisions):
        n += 1
        tasks = [task(p, m, n, **task_kw) for p, ms in demand.items() for m in ms]
        out = svc.schedule_once(tasks)
        if out.intent is not None and out.task is not None and out.decision.value == "admit":
            counts[out.task.project_id] += 1
            if finish:
                svc.mark_dispatched(out.intent.intent_id)
                svc.finish(out.intent.intent_id)
    return counts
```

### Step 4 — `tests/controller/test_v23_service.py` (create, exactly)
```python
"""SW-W2-S1: SchedulerService basics — receipts, running counters, ops events, allocator."""

from __future__ import annotations

from tests.controller.v23_harness import make_service, run_share, task

from swarm.contracts.v23 import ReasonCode, SchedulerDecision
from swarm.controller.fairness import DurableFairnessStore
from swarm.controller.reservations import ReservationService
from swarm.controller.resource_allocator import AllocationRequest, ResourceAllocator
from swarm.controller.scheduling_receipts import SchedulingReceiptLog


def test_idle_when_no_work_and_receipt_written() -> None:
    svc, store, _, _ = make_service()
    svc.register_project("p1")
    out = svc.schedule_once([])
    assert out.decision == SchedulerDecision.IDLE
    assert out.reason_code == ReasonCode.NO_ELIGIBLE_WORK
    assert [r.sequence for r in store.list_receipts()] == [out.receipt.sequence]  # type: ignore[union-attr]


def test_admit_reserves_and_finish_releases() -> None:
    svc, store, broker, _ = make_service()
    svc.register_project("p1")
    svc.register_mission("m1", "p1")
    out = svc.schedule_once([task("p1", "m1", 1, provider_route="rt_free")])
    assert out.decision == SchedulerDecision.ADMIT and out.intent is not None
    assert store.get_project("p1").running == 1  # type: ignore[union-attr]
    assert broker.outstanding() == 2.0
    svc.mark_dispatched(out.intent.intent_id)
    verdict = svc.finish(out.intent.intent_id)
    assert verdict.accepted and verdict.reason == "accepted"
    assert store.get_project("p1").running == 0  # type: ignore[union-attr]
    assert broker.outstanding() == 0.0
    receipt = out.receipt
    assert receipt is not None and receipt.dispatch_intent_id == out.intent.intent_id
    assert receipt.scheduler_epoch == 1 and receipt.policy_version == "v23-wdrr-1"


def test_equal_weights_share_within_tolerance() -> None:
    svc, _, _, _ = make_service()
    for p in ("p1", "p2"):
        svc.register_project(p)
        svc.register_mission(f"{p}_m", p)
    counts = run_share(svc, {"p1": ["p1_m"], "p2": ["p2_m"]}, decisions=200)
    assert sum(counts.values()) == 200
    assert abs(counts["p1"] / 200 - 0.5) <= 0.5 * 0.15


def test_unequal_weights_share_and_no_starvation() -> None:
    svc, _, _, _ = make_service()
    svc.register_project("heavy", weight=3.0)
    svc.register_project("light", weight=1.0)
    svc.register_mission("hm", "heavy")
    svc.register_mission("lm", "light")
    counts = run_share(svc, {"heavy": ["hm"], "light": ["lm"]}, decisions=400)
    assert abs(counts["heavy"] / 400 - 0.75) <= 0.75 * 0.15
    assert counts["light"] > 0


def test_ops_event_per_decision() -> None:
    svc, _, _, _ = make_service()
    svc.register_project("p1")
    svc.register_mission("m1", "p1")
    svc.schedule_once([task("p1", "m1", 1)])
    kinds = [e["kind"] for e in svc.ops.list_events()]  # type: ignore[union-attr]
    assert kinds == ["scheduler.decision"]


def test_resource_allocator_routes_through_scheduler() -> None:
    svc, store, _, _ = make_service()
    alloc = ResourceAllocator(
        fairness=DurableFairnessStore(),
        reservations=ReservationService(current_epoch=1),
        receipts=SchedulingReceiptLog(),
        site_epoch=1,
        scheduler=svc,
    )
    result = alloc.allocate(
        AllocationRequest(project_id="p", mission_id="m", attempt_id="a1", tool_units=1)
    )
    assert result["intent"]["state"] == "reserved"
    assert result["receipt"]["decision"] == "admit"
    assert store.list_receipts()[-1].attempt_id == "a1"
```

### Step 5 — `tests/controller/test_v23_pathological.py` (create, exactly)
```python
"""SW-W2-S1: the 11 required negative cases of ART-V23-MULTIMISSION_SCHEDULER.

Each test names its ART bullet. All must fail closed on authority/effect duplication
and preserve eventual service for eligible work.
"""

from __future__ import annotations

from tests.controller.v23_harness import Broker, Clock, make_service, run_share, task

from swarm.contracts.v23 import (
    DispatchIntentState,
    PriorityClass,
    ReasonCode,
    SchedulerDecision,
)
from swarm.recovery.authority import SiteAuthorityService
from swarm.scheduling.epoch import InMemorySchedulerEpochService


def test_01_spawning_many_children_does_not_gain_share() -> None:
    svc, _, _, _ = make_service()
    svc.register_project("spammer")
    svc.register_project("modest")
    spam_missions = [f"sm{i}" for i in range(50)]
    for m in spam_missions:
        svc.register_mission(m, "spammer")
    svc.register_mission("mm", "modest")
    counts = run_share(svc, {"spammer": spam_missions, "modest": ["mm"]}, decisions=200)
    assert abs(counts["modest"] / 200 - 0.5) <= 0.5 * 0.15


def test_02_retry_loops_cannot_reset_credit() -> None:
    svc, store, _, _ = make_service()
    for p in ("retrier", "steady"):
        svc.register_project(p)
        svc.register_mission(f"{p}_m", p)
    admits = {"retrier": 0, "steady": 0}
    for n in range(200):
        # The retrier re-submits the same task with a brand-new attempt every tick.
        tasks = [task("retrier", "retrier_m", 0).model_copy(update={"attempt_id": f"retry_{n}"}),
                 task("steady", "steady_m", n)]
        out = svc.schedule_once(tasks)
        assert out.intent is not None and out.task is not None
        admits[out.task.project_id] += 1
        svc.mark_dispatched(out.intent.intent_id)
        svc.finish(out.intent.intent_id)
    assert abs(admits["retrier"] / 200 - 0.5) <= 0.5 * 0.15
    assert store.get_project("retrier").credit <= 10.0  # type: ignore[union-attr]


def test_03_continuous_urgent_arrivals_do_not_starve_lower_weight() -> None:
    svc, _, _, _ = make_service()
    svc.register_project("hot", weight=2.0)
    svc.register_project("cold", weight=1.0)
    svc.register_mission("hot_m", "hot", priority=PriorityClass.URGENT)
    svc.register_mission("cold_m", "cold")
    last_cold = 0
    worst_gap = 0
    for n in range(1, 301):
        out = svc.schedule_once([task("hot", "hot_m", n), task("cold", "cold_m", n)])
        assert out.intent is not None and out.task is not None
        if out.task.project_id == "cold":
            worst_gap = max(worst_gap, n - last_cold)
            last_cold = n
        svc.mark_dispatched(out.intent.intent_id)
        svc.finish(out.intent.intent_id)
    assert last_cold > 0
    assert worst_gap <= 6


def test_04_incompatible_worker_at_head_does_not_block_later_task() -> None:
    svc, _, _, _ = make_service(resource_available=lambda t: t.worker_class != "gpu")
    svc.register_project("p")
    svc.register_mission("m", "p")
    head = task("p", "m", 1, worker_class="gpu", priority=10)
    later = task("p", "m", 2)
    out = svc.schedule_once([head, later])
    assert out.decision == SchedulerDecision.ADMIT
    assert out.task is not None and out.task.task_id == later.task_id


def test_05_partial_reservation_is_compensated() -> None:
    broker = Broker({("worker", "local"): 0})
    svc, store, _, _ = make_service(broker=broker)
    svc.register_project("p")
    svc.register_mission("m", "p")
    before = store.get_project("p")
    out = svc.schedule_once([task("p", "m", 1, provider_route="rt_free")])
    assert out.decision == SchedulerDecision.DEFER
    assert out.reason_code == ReasonCode.RESERVATION_FAILED
    assert out.intent is not None and out.intent.state == DispatchIntentState.COMPENSATED
    assert ("release", "provider", "rt_free", "att_m_1") in broker.log
    assert broker.outstanding() == 0.0
    after = store.get_project("p")
    assert after is not None and before is not None
    assert (after.credit, after.running) == (before.credit, before.running)


def test_06_crash_after_reservation_before_dispatch_recovers() -> None:
    clock = Clock()
    svc, store, broker, _ = make_service(clock=clock)
    svc.register_project("p")
    svc.register_mission("m", "p")
    out = svc.schedule_once([task("p", "m", 1)])
    assert out.intent is not None and broker.outstanding() == 1.0
    # "Crash": a new process with the same durable store starts after the intent TTL.
    clock.advance(60)
    fresh, _, _, _ = make_service(store=store, broker=broker, clock=clock, holder_id="sched_b")
    report = fresh.recover()
    assert report["expired_intents"] == [out.intent.intent_id]
    assert broker.outstanding() == 0.0
    assert store.get_project("p").running == 0  # type: ignore[union-attr]
    again = fresh.schedule_once([task("p", "m", 2)])
    assert again.decision == SchedulerDecision.ADMIT


def test_07_result_after_cancellation_or_epoch_change_is_fenced() -> None:
    site = SiteAuthorityService()
    site.bootstrap("local", epoch=1)
    svc, _, broker, _ = make_service(site_authority=site)
    svc.register_project("p")
    svc.register_mission("m1", "p")
    svc.register_mission("m2", "p")
    a = svc.schedule_once([task("p", "m1", 1)])
    b = svc.schedule_once([task("p", "m2", 1)])
    assert a.intent is not None and b.intent is not None
    svc.mark_dispatched(a.intent.intent_id)
    svc.mark_dispatched(b.intent.intent_id)
    svc.cancel_mission("m1")
    v1 = svc.finish(a.intent.intent_id)
    assert (v1.accepted, v1.reason) == (False, "stale_generation")
    site.advance_epoch("local", reason="failover_drill")
    v2 = svc.finish(b.intent.intent_id)
    assert (v2.accepted, v2.reason) == (False, "stale_site_epoch")
    assert broker.outstanding() == 0.0


def test_08_weight_change_with_tasks_in_flight() -> None:
    svc, store, _, _ = make_service()
    for p in ("a", "b"):
        svc.register_project(p)
        svc.register_mission(f"{p}_m", p)
    inflight = svc.schedule_once([task("a", "a_m", 0)])
    assert inflight.intent is not None
    svc.mark_dispatched(inflight.intent.intent_id)
    svc.set_weight("a", 3.0)
    assert svc.finish(inflight.intent.intent_id).accepted
    counts = run_share(svc, {"a": ["a_m"], "b": ["b_m"]}, decisions=400)
    assert abs(counts["a"] / 400 - 0.75) <= 0.75 * 0.15
    assert store.get_project("a").running == 0  # type: ignore[union-attr]


def test_09_provider_quota_exhausted_beats_scheduler_credit() -> None:
    broker = Broker({("provider", "rt_free"): 1})
    svc, store, _, _ = make_service(broker=broker)
    svc.register_project("p")
    svc.register_mission("m", "p", max_parallelism=5)
    first = svc.schedule_once([task("p", "m", 1, provider_route="rt_free")])
    assert first.decision == SchedulerDecision.ADMIT
    credit_after_first = store.get_project("p").credit  # type: ignore[union-attr]
    second = svc.schedule_once([task("p", "m", 2, provider_route="rt_free")])
    assert second.reason_code == ReasonCode.RESERVATION_FAILED
    assert store.get_project("p").credit == credit_after_first  # type: ignore[union-attr]
    assert broker.used[("provider", "rt_free")] == 1.0


def test_10_blocked_only_project_does_not_block_or_accrue() -> None:
    svc, store, _, _ = make_service()
    svc.register_project("blocked")
    svc.register_project("ready")
    svc.register_mission("bm", "blocked")
    svc.register_mission("rm", "ready")
    for n in range(20):
        tasks = [task("blocked", "bm", n, dependencies_ready=False), task("ready", "rm", n)]
        out = svc.schedule_once(tasks)
        assert out.task is not None and out.task.project_id == "ready"
        assert out.intent is not None
        svc.mark_dispatched(out.intent.intent_id)
        svc.finish(out.intent.intent_id)
    assert store.get_project("blocked").credit == 0.0  # type: ignore[union-attr]


def test_11_duplicate_schedulers_single_dispatch_authority() -> None:
    clock = Clock()
    epochs = InMemorySchedulerEpochService(clock=clock)
    a, store, broker, _ = make_service(epochs=epochs, clock=clock, holder_id="sched_a")
    b, _, _, _ = make_service(store=store, broker=broker, epochs=epochs, clock=clock,
                              holder_id="sched_b")
    a.register_project("p")
    a.register_mission("m", "p")
    t = task("p", "m", 1)
    first = a.schedule_once([t])
    assert first.decision == SchedulerDecision.ADMIT
    denied = b.schedule_once([t])
    assert (denied.decision, denied.reason_code) == (
        SchedulerDecision.DENY, ReasonCode.STALE_SCHEDULER_EPOCH
    )
    # Same attempt again on the holder: no second reservation.
    repeat = a.schedule_once([t])
    assert repeat.decision != SchedulerDecision.ADMIT
    assert sum(1 for e in broker.log if e[0] == "reserve") == 1
    admits = [r for r in store.list_receipts() if r.decision == SchedulerDecision.ADMIT]
    assert len(admits) == 1
```

### Step 6 — `tests/integration/db/test_v23_service_restart_sql.py` (create, exactly)
```python
"""SW-W2-S1: scheduler fairness state survives a process restart on PostgreSQL."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

from swarm.contracts.v23 import SchedulableTask, SchedulerDecision
from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import Base
from swarm.scheduling.epoch import SqlSchedulerEpochService
from swarm.scheduling.service import SchedulerService
from swarm.scheduling.store import SqlSchedulingStore

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)
TABLES = (
    "v23_project_queue_state",
    "v23_mission_queue_state",
    "v23_scheduler_receipts",
    "v23_dispatch_intents",
    "v23_scheduler_epochs",
)


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture()
def factory():
    eng = create_db_engine(DATABASE_URL)
    try:
        ping(eng)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"postgres_unavailable:{type(exc).__name__}")
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        conn.execute(text("TRUNCATE " + ", ".join(TABLES)))
    yield make_session_factory(eng)
    eng.dispose()


def _svc(factory, clock: Clock, holder: str, released: list[str]) -> SchedulerService:
    return SchedulerService(
        SqlSchedulingStore(factory),
        epochs=SqlSchedulerEpochService(factory, ttl_seconds=15, clock=clock),
        holder_id=holder,
        reserve=lambda intent, comp: f"r_{intent.attempt_id}_{comp.kind}",
        release=lambda intent, comp: released.append(intent.attempt_id),
        clock=clock,
    )


def _task(project: str, n: int) -> SchedulableTask:
    return SchedulableTask(
        task_id=f"{project}_t{n}",
        mission_id=f"{project}_m",
        project_id=project,
        attempt_id=f"att_{project}_{n}",
    )


def test_restart_preserves_credit_and_recovers_intents(factory) -> None:
    clock = Clock()
    released: list[str] = []
    first = _svc(factory, clock, "proc_a", released)
    for p, w in (("a", 3.0), ("b", 1.0)):
        first.register_project(p, weight=w)
        first.register_mission(f"{p}_m", p)
    for n in range(20):
        out = first.schedule_once([_task("a", n), _task("b", n)])
        assert out.intent is not None
        first.mark_dispatched(out.intent.intent_id)
        first.finish(out.intent.intent_id)
    crashed = first.schedule_once([_task("a", 99), _task("b", 99)])
    assert crashed.decision == SchedulerDecision.ADMIT and crashed.intent is not None
    credits = {q["project_id"]: q["credit"] for q in first.queues()}

    clock.now = clock.now + timedelta(seconds=60)
    second = _svc(factory, clock, "proc_b", released)
    report = second.recover()
    assert report["expired_intents"] == [crashed.intent.intent_id]
    assert crashed.intent.attempt_id in released
    after = {q["project_id"]: q for q in second.queues()}
    for p in ("a", "b"):
        assert after[p]["credit"] == pytest.approx(min(credits[p], 10.0 * (3.0 if p == "a" else 1.0)))
        assert after[p]["running"] == 0
    nxt = second.schedule_once([_task("a", 100), _task("b", 100)])
    assert nxt.decision == SchedulerDecision.ADMIT
    assert nxt.receipt is not None and nxt.receipt.scheduler_epoch == 2
    receipts = SqlSchedulingStore(factory).list_receipts(limit=1000)
    assert [r.sequence for r in receipts] == sorted(r.sequence for r in receipts)
```

### Step 7 — run
```bash
uv run pytest tests/controller/test_v23_service.py tests/controller/test_v23_pathological.py -q   # 17 passed
uv run pytest tests/controller -q
```
Ruff sorts `from tests.controller.v23_harness import …` **before** the `swarm` imports, because `tests/controller` has no `__init__.py`. Keep that order; run `uv run ruff check --fix tests/controller` if you retyped it.

If a dependency's function signature differs from what `service.py` calls, the base has changed shape: STOP (S4, section 10). The calls in question are `DispatchIntentService(store, reserve=, release=, clock=, ttl_seconds=)`, `select_next(..., now=, config=, resource_available=)`, `apply_selection(..., sequence=)` and `SchedulerEpochService.acquire/renew/require_current/current`.

### Section-5 acceptance
- [ ] All 11 ART pathological cases pass (`test_01` … `test_11`), each named after its ART bullet.
- [ ] With equal weights the share is within ±15% after 200 decisions; with weights 3:1 the share is within ±15% of 75% and the light project is never starved.
- [ ] Every decision (admit, defer, idle, or deny for a stale site) has exactly one receipt with a monotonic `sequence`; fenced non-holders write none.
- [ ] Restart on PostgreSQL preserves credit (positive side clamped), expires the crashed intent, releases its reservation, and the new holder gets epoch 2.
- [ ] The legacy `ResourceAllocator` path is unchanged; with `scheduler=` it produces an `admit` receipt.

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w2_s1 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w2_s1
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/controller -q
uv run pytest tests/contracts tests/spikes tests/api tests/broker tests/controller tests/chaos tests/deployment tests/evals tests/extensions tests/foundation tests/goals tests/pursuit tests/sdk tests/knowledge tests/load tests/memory tests/mission tests/objectives tests/onboarding tests/product tests/providers tests/recovery tests/regressions tests/release tests/runtime tests/selfdev tests/tools tests/ui tests/workers tests/workspace tests/e2e tests/acceptance tests/portability -q --ignore=tests/integration

# PostgreSQL integration (install steps in “PostgreSQL” below)
uv run pytest tests/integration -q -m integration

git checkout -- schemas/v1 docs/evidence/fix-004 var   # tests rewrite these tracked files
git status --porcelain            # every path listed must be one of YOUR files
```

### PostgreSQL (for the integration line)
```bash
pg_isready -h 127.0.0.1 || {
  sudo apt-get update && sudo apt-get install -y postgresql && sudo service postgresql start
  sudo -u postgres psql -c "CREATE USER swarm WITH PASSWORD 'swarm' SUPERUSER;" || true
}
```
Run this block before section 6. Section 6 creates your private database and exports `SWARM_DATABASE_URL` for **both** pytest lines; never unset it and never point it at the shared `swarm` database.
If `pg_isready -h 127.0.0.1` still fails after running this block twice, write `integration: SKIPPED (postgres unavailable: <last error line>)` in the handoff and continue. Never claim integration passed without running it.

## 7. Acceptance checklist (tick every box in the handoff)
- [ ] Every step in section 5 done; every acceptance box in section 5 ticked.
- [ ] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [ ] `uv run alembic heads` prints exactly one head.
- [ ] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [ ] Integration run passed, or SKIPPED with reason in the handoff.
- [ ] `git status --porcelain` lists only files from section 3 + the handoff.
- [ ] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.
- [ ] The Codex review packet (section 11) is in the PR description and the handoff.

## 8. Commit, push, draft PR
```bash
git checkout -- schemas/v1 docs/evidence/fix-004 var
git add src/swarm/scheduling/service.py src/swarm/controller/resource_allocator.py tests/controller/v23_harness.py tests/controller/test_v23_service.py tests/controller/test_v23_pathological.py tests/integration/db/test_v23_service_restart_sql.py docs/v2.3/sessions/SW-W2-S1.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "feat(v2.3): SchedulerService composing WDRR, durable store, intents, epochs, receipts; pathological suite" -m "Session: SW-W2-S1. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v23-w2-s1-scheduler-service
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v23-w2-s1-scheduler-service --title "[SW-W2-S1] SchedulerService (WDRR + store + intents + epochs + site epoch + receipts + ops events) + pathological suite" --body-file docs/v2.3/sessions/SW-W2-S1.md
git ls-remote origin refs/heads/cursor/v23-w2-s1-scheduler-service   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W2-S1.md` with exactly these headings:
```markdown
# SW-W2-S1 handoff
- Branch: <exact branch name>   Base SHA: <from setup>   Head SHA: <git rev-parse HEAD>
- PR: <url, or compare URL>
## Done
<bullet list of what you implemented>
## Verification
<each command from section 6 and its final result line; integration PASSED/SKIPPED(reason)>
## Acceptance
<copy the checkboxes from sections 5 and 7, ticked>
## Decisions
<choices you made under hard rule 8, or 'none'>
## Needs other owner
<files outside your scope that should change, with the exact change; or 'none'>
## Codex review packet
<the block from section 11, filled in>
## Status
implemented + tested (NOT accepted; needs Codex review)
```

## 10. STOP conditions (never wait for a human)
STOP immediately when any of these is true:
- **S1** `git status --porcelain` is not empty before Setup. (Do not commit, stash or discard anything; skip steps 1–4 below and only report.)
- **S2** a dependency check prints `MISSING`.
- **S3** a command in section 6, or a check in section 5, still fails after **2 attempts**. One attempt = one edit to *your own files* followed by re-running the failing command.
- **S4** a “currently reads” / before-block in section 5 does not match the file, or a function named in section 5 does not exist.
- **S5** finishing would require editing a file that is not in section 3.
- **S6** a required environment variable prints `MISSING`.
- **S7** an external gate check (inference_server sync point or approval line) in section 5 fails.
- **S8** `git push` still fails after 4 retries (waits 4 s, 8 s, 16 s, 32 s).

What to do on STOP, in this order:
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W2-S1.md` then `git commit -m "WIP(SW-W2-S1): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v23-w2-s1-scheduler-service` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v23-w2-s1-scheduler-service?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W2-S1
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `src/swarm/scheduling/service.py`, `src/swarm/controller/resource_allocator.py`, `tests/controller/v23_harness.py`, `tests/controller/test_v23_service.py`, `tests/controller/test_v23_pathological.py`, `tests/integration/db/test_v23_service_restart_sql.py`, `docs/v2.3/sessions/SW-W2-S1.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete"). Session-specific: fairness, fencing by epoch, receipts for every decision; no starvation.
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```

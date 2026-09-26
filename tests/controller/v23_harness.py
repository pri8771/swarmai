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

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

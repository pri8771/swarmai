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

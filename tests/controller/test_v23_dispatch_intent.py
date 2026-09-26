"""SW-W1-S3: dispatch intents are all-or-nothing, idempotent and recoverable."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from swarm.contracts.v23 import DispatchIntent, DispatchIntentComponent, DispatchIntentState
from swarm.scheduling.dispatch_intent import DispatchIntentError, DispatchIntentService
from swarm.scheduling.memory_store import InMemorySchedulingStore


class FakeCapacity:
    def __init__(self, fail_kind: str | None = None) -> None:
        self.fail_kind = fail_kind
        self.held: dict[str, str] = {}
        self.reserve_calls = 0

    def reserve(self, intent: DispatchIntent, comp: DispatchIntentComponent) -> str:
        self.reserve_calls += 1
        if comp.kind == self.fail_kind:
            raise RuntimeError("capacity_unavailable")
        rid = f"res_{comp.kind}_{intent.attempt_id}"
        self.held[rid] = comp.kind
        return rid

    def release(self, intent: DispatchIntent, comp: DispatchIntentComponent) -> None:
        self.held.pop(f"res_{comp.kind}_{intent.attempt_id}", None)


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now


COMPONENTS = [
    DispatchIntentComponent(kind="provider", ref="rt_ollama_default"),
    DispatchIntentComponent(kind="worker", ref="local"),
    DispatchIntentComponent(kind="tool", ref="workspace.read"),
]


def _service(cap: FakeCapacity, clock: Clock | None = None) -> DispatchIntentService:
    return DispatchIntentService(
        InMemorySchedulingStore(),
        reserve=cap.reserve,
        release=cap.release,
        clock=clock or Clock(),
        ttl_seconds=30,
    )


def _prepare(svc: DispatchIntentService, attempt: str = "att_1") -> DispatchIntent:
    return svc.prepare(
        attempt_id=attempt,
        project_id="proj_a",
        mission_id="msn_1",
        task_id="tsk_1",
        components=COMPONENTS,
        site_epoch=1,
        scheduler_epoch=1,
        cancellation_generation=0,
    )


def test_all_components_reserved() -> None:
    cap = FakeCapacity()
    intent = _prepare(_service(cap))
    assert intent.state == DispatchIntentState.RESERVED
    assert all(c.reserved for c in intent.components)
    assert len(cap.held) == 3


def test_partial_failure_compensates_everything() -> None:
    cap = FakeCapacity(fail_kind="worker")
    intent = _prepare(_service(cap))
    assert intent.state == DispatchIntentState.COMPENSATED
    assert cap.held == {}
    assert intent.failure_reason is not None and "worker" in intent.failure_reason


def test_reservation_exception_text_is_not_persisted() -> None:
    def fail_with_secret(
        _intent: DispatchIntent, _comp: DispatchIntentComponent
    ) -> str:
        raise RuntimeError("api_key=should-never-reach-a-receipt")

    store = InMemorySchedulingStore()
    service = DispatchIntentService(
        store,
        reserve=fail_with_secret,
        release=lambda _intent, _comp: None,
        clock=Clock(),
    )
    intent = _prepare(service)
    assert intent.state == DispatchIntentState.COMPENSATED
    assert intent.failure_reason == "reserve_failed:provider:RuntimeError"


def test_crash_after_external_reserve_is_recovered() -> None:
    cap = FakeCapacity()
    clock = Clock()
    store = InMemorySchedulingStore()

    def crash_after_reserve(
        intent: DispatchIntent, comp: DispatchIntentComponent
    ) -> str:
        reservation_id = cap.reserve(intent, comp)
        raise SystemExit(reservation_id)

    crashed = DispatchIntentService(
        store,
        reserve=crash_after_reserve,
        release=cap.release,
        clock=clock,
        ttl_seconds=30,
    )
    with pytest.raises(SystemExit):
        _prepare(crashed)
    assert cap.held == {"res_provider_att_1": "provider"}

    clock.now += timedelta(seconds=31)
    recovered = DispatchIntentService(
        store,
        reserve=cap.reserve,
        release=cap.release,
        clock=clock,
        ttl_seconds=30,
    ).recover_expired()
    assert len(recovered) == 1
    assert recovered[0].state == DispatchIntentState.EXPIRED
    assert cap.held == {}


def test_prepare_is_idempotent_per_attempt() -> None:
    cap = FakeCapacity()
    svc = _service(cap)
    first = _prepare(svc)
    second = _prepare(svc)
    assert first.intent_id == second.intent_id
    assert cap.reserve_calls == 3


def test_dispatch_complete_and_illegal_transitions() -> None:
    cap = FakeCapacity()
    svc = _service(cap)
    intent = _prepare(svc)
    with pytest.raises(DispatchIntentError):
        svc.complete(intent.intent_id)
    svc.mark_dispatched(intent.intent_id)
    with pytest.raises(DispatchIntentError, match="cancel_dispatched"):
        svc.cancel(intent.intent_id)
    done = svc.complete(intent.intent_id)
    assert done.state == DispatchIntentState.COMPLETED


def test_cancel_releases_reservations() -> None:
    cap = FakeCapacity()
    svc = _service(cap)
    intent = _prepare(svc)
    cancelled = svc.cancel(intent.intent_id, reason="mission_cancelled")
    assert cancelled.state == DispatchIntentState.CANCELLED
    assert cap.held == {}


def test_recover_expired_releases_once_and_skips_dispatched() -> None:
    cap = FakeCapacity()
    clock = Clock()
    svc = _service(cap, clock)
    stuck = _prepare(svc, "att_stuck")
    running = _prepare(svc, "att_running")
    svc.mark_dispatched(running.intent_id)
    clock.now = clock.now + timedelta(seconds=31)
    recovered = svc.recover_expired()
    assert [i.intent_id for i in recovered] == [stuck.intent_id]
    assert recovered[0].state == DispatchIntentState.EXPIRED
    assert svc.recover_expired() == []
    assert set(cap.held) == {f"res_{k}_att_running" for k in ("provider", "worker", "tool")}


def test_expired_intent_cannot_dispatch() -> None:
    cap = FakeCapacity()
    clock = Clock()
    svc = _service(cap, clock)
    intent = _prepare(svc)
    clock.now = clock.now + timedelta(seconds=31)
    with pytest.raises(DispatchIntentError, match="intent_expired"):
        svc.mark_dispatched(intent.intent_id)

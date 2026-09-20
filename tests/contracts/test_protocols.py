"""Protocol satisfaction and fake infrastructure tests."""

from __future__ import annotations

import pytest

from swarm.contracts.fixtures import sample_inference_request, sample_quota, sample_route
from swarm.contracts.protocols import InferenceBroker, ProviderAdapter, WorkerRegistry
from swarm.fakes import (
    BrokerBypassError,
    FakeClock,
    FakeEventGenerator,
    FakeInferenceBroker,
    FakeProviderAdapter,
    FakeWorkerRegistry,
)


def test_fakes_satisfy_protocols() -> None:
    adapter = FakeProviderAdapter()
    broker = FakeInferenceBroker(adapter, buckets=[sample_quota()])
    registry = FakeWorkerRegistry()
    assert isinstance(adapter, ProviderAdapter)
    assert isinstance(broker, InferenceBroker)
    assert isinstance(registry, WorkerRegistry)


@pytest.mark.asyncio
async def test_fake_provider_calls_accounted() -> None:
    adapter = FakeProviderAdapter()
    broker = FakeInferenceBroker(adapter, buckets=[sample_quota()])
    route = sample_route()
    request = sample_inference_request(route.route_id)
    ticket = await broker.reserve(request, route)
    receipt = await broker.invoke(ticket)
    assert receipt.actual_route == route.route_id
    assert broker.request_count == 1
    broker.assert_all_calls_accounted()


@pytest.mark.asyncio
async def test_broker_bypass_detected() -> None:
    adapter = FakeProviderAdapter()
    broker = FakeInferenceBroker(adapter, buckets=[sample_quota()])
    route = sample_route()
    # Direct adapter call without broker.invoke — must be detectable if someone
    # also increments inconsistently; invoke without ticket fails hard.
    with pytest.raises(BrokerBypassError):
        from datetime import timedelta

        from swarm.contracts.common import utc_now
        from swarm.contracts.provider import Reservation

        fake_ticket = Reservation(
            logical_call_id="x",
            attempt_id="y",
            route_id=route.route_id,
            expires_at=utc_now() + timedelta(minutes=1),
        )
        await broker.invoke(fake_ticket)


def test_fake_clock_and_events() -> None:
    clock = FakeClock()
    gen = FakeEventGenerator(clock)
    event = gen.emit("mission.created", mission_id="m1", payload={"ok": True})
    assert event.type == "mission.created"
    clock.advance(30)
    later = gen.emit("task.ready", mission_id="m1", task_id="t1")
    assert later.occurred_at > event.occurred_at

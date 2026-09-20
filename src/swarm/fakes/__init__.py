"""Fake infrastructure exports (never production adapters)."""

from swarm.fakes.broker import BrokerBypassError, FakeInferenceBroker
from swarm.fakes.clock import FakeClock
from swarm.fakes.events import FakeEventGenerator
from swarm.fakes.provider import FakeProviderAdapter
from swarm.fakes.worker import FakeWorkerRegistry

__all__ = [
    "FakeClock",
    "FakeEventGenerator",
    "FakeProviderAdapter",
    "FakeInferenceBroker",
    "BrokerBypassError",
    "FakeWorkerRegistry",
]

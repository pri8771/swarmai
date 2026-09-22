"""R28a reproduced failure paths, using memory only for no-effect fixtures.

The same outcome cases also run with the real PostgreSQL effect repository for
consequential fixtures. No memory store advertises itself as durable.
"""

import asyncio
import threading

import pytest
from tests.integration.db.effect_fixtures import bind_lease
from tests.integration.db.test_effect_crash_window import engine as engine
from tests.integration.db.test_effect_crash_window import factory as factory

from swarm.tools.adapters.api_mcp import ApiMcpAdapter
from swarm.tools.adapters.base import AdapterDeniedError, AdapterNotSentError
from swarm.tools.effects import DurableEffectRepository, InMemoryEffectStore
from swarm.tools.v17_gateway import (
    ConsequentialToolGateway,
    ReconciliationRequiredError,
    StaleLeaseError,
)


@pytest.fixture(params=["memory", pytest.param("postgres", marks=pytest.mark.integration)])
def effect_store(request):
    if request.param == "memory":
        return InMemoryEffectStore()
    return DurableEffectRepository(request.getfixturevalue("factory"))


class ResultAdapter(ApiMcpAdapter):
    def __init__(self, result=None, error=None):
        super().__init__()
        self.result = result
        self.error = error
        self.pre_calls = 0
        self.thread_ids = []

    def observe_pre_state(self, envelope):
        self.pre_calls += 1
        self.thread_ids.append(threading.get_ident())
        return {}

    def execute(self, envelope):
        self._calls.append({"effect_key": envelope.effect_key})
        self.thread_ids.append(threading.get_ident())
        if self.error:
            raise self.error
        return self.result

    def observe_post_state(self, envelope, result):
        self.thread_ids.append(threading.get_ident())
        return {"result": result}


def setup(adapter, store, timeout=1):
    # No-effect unit fixtures are explicit. Consequential semantics use real PG.
    adapter.manifest.side_effect_class = "consequential" if store.durable else "none"
    if not store.durable:
        adapter.manifest.operations["echo"].side_effect_class = "none"
        adapter.manifest.operations["echo"].risk_class = "low"
    envelope = adapter.normalize(
        {
            "project_id": "r28a",
            "body": "synthetic",
            "lease_generation": 1,
            "cancellation_generation": 0,
        }
    )
    if store.durable:
        envelope = bind_lease(store.factory, envelope)
    gateway = ConsequentialToolGateway(
        adapter,
        project_id=envelope.project_id,
        allowed_scopes={"network.https", "mcp.call"},
        current_lease_generation=envelope.lease_generation,
        current_cancellation_generation=envelope.cancellation_generation,
        store=store,
    )
    envelope.timeout_seconds = timeout
    envelope.approval_id = gateway.make_approval(envelope).approval_id
    return gateway, envelope


def row(store, envelope):
    return store.get(project_id=envelope.project_id, effect_key=envelope.effect_key)


@pytest.mark.asyncio
@pytest.mark.parametrize("result", [{}, None, [], {"outcome": "bogus"}, {"outcome": []}])
async def test_empty_or_unrecognized_result_is_unknown_not_succeeded(effect_store, result):
    adapter = ResultAdapter(result)
    gateway, envelope = setup(adapter, effect_store)
    receipt = await gateway.execute_envelope(envelope)
    assert receipt.outcome == "unknown"
    assert row(effect_store, envelope)["state_reason"] == "unrecognized_outcome"
    assert all(tid != threading.get_ident() for tid in adapter.thread_ids)


@pytest.mark.asyncio
async def test_exception_is_unknown_and_second_call_does_not_execute(effect_store):
    adapter = ResultAdapter(error=RuntimeError("synthetic private transport detail"))
    gateway, envelope = setup(adapter, effect_store)
    receipt = await gateway.execute_envelope(envelope)
    assert receipt.outcome == "unknown"
    assert row(effect_store, envelope)["state_reason"] == "exception:RuntimeError"
    assert "private transport" not in receipt.model_dump_json()
    with pytest.raises(ReconciliationRequiredError):
        await gateway.execute_envelope(envelope)
    assert adapter.call_count == 1


@pytest.mark.asyncio
async def test_not_sent_error_is_failed_not_applied_and_retry_executes_once_more(effect_store):
    adapter = ResultAdapter(error=AdapterNotSentError("synthetic pre-send failure"))
    gateway, envelope = setup(adapter, effect_store)
    assert (await gateway.execute_envelope(envelope)).outcome == "failed"
    assert row(effect_store, envelope)["state_reason"] == "not_applied"
    adapter.error, adapter.result = None, {"outcome": "succeeded"}
    assert (await gateway.execute_envelope(envelope)).outcome == "succeeded"
    assert adapter.call_count == 2
    assert row(effect_store, envelope)["attempt_count"] == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "outcome,state,reason",
    [
        ("succeeded", "succeeded", None),
        ("not_applied", "failed", "not_applied"),
        ("denied", "denied", "explicit denial"),
        ("cancelled", "cancelled", None),
        ("unknown", "unknown", "unrecognized_outcome"),
    ],
)
async def test_explicit_outcome_mapping(effect_store, outcome, state, reason):
    adapter = ResultAdapter({"outcome": outcome, "detail": "explicit denial"})
    gateway, envelope = setup(adapter, effect_store)
    assert (await gateway.execute_envelope(envelope)).outcome == state
    assert row(effect_store, envelope)["state_reason"] == reason


@pytest.mark.asyncio
async def test_adapter_denial_is_explicit(effect_store):
    adapter = ResultAdapter(error=AdapterDeniedError("explicit adapter denial"))
    gateway, envelope = setup(adapter, effect_store)
    assert (await gateway.execute_envelope(envelope)).outcome == "denied"
    assert row(effect_store, envelope)["state_reason"] == "explicit adapter denial"


class BlockingAdapter(ResultAdapter):
    def __init__(self):
        super().__init__()
        self.entered, self.release, self.done = (
            threading.Event(),
            threading.Event(),
            threading.Event(),
        )

    def execute(self, envelope):
        self._calls.append({"effect_key": envelope.effect_key})
        self.entered.set()
        try:
            if not self.release.wait(5):
                raise RuntimeError("test worker was not released")
            return {"outcome": "succeeded"}
        finally:
            self.done.set()


@pytest.mark.asyncio
async def test_timeout_is_unknown(effect_store):
    adapter = BlockingAdapter()
    gateway, envelope = setup(adapter, effect_store)
    try:
        receipt = await gateway.execute_envelope(envelope)
        assert adapter.entered.is_set() and receipt.outcome == "unknown"
        assert row(effect_store, envelope)["state_reason"] == "timeout"
        with pytest.raises(ReconciliationRequiredError):
            await gateway.execute_envelope(envelope)
        assert adapter.call_count == 1
    finally:
        adapter.release.set()
        assert await asyncio.to_thread(adapter.done.wait, 2)
    # The late thread return cannot overwrite the authoritative unknown state.
    assert row(effect_store, envelope)["state"] == "unknown"


@pytest.mark.asyncio
async def test_cancellation_records_unknown_and_reraises(effect_store):
    adapter = BlockingAdapter()
    gateway, envelope = setup(adapter, effect_store, timeout=5)
    task = asyncio.create_task(gateway.execute_envelope(envelope))
    try:
        assert await asyncio.to_thread(adapter.entered.wait, 1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert row(effect_store, envelope)["state_reason"] == "cancelled_during_execute"
        assert row(effect_store, envelope)["state"] == "unknown"
    finally:
        adapter.release.set()
        assert await asyncio.to_thread(adapter.done.wait, 2)


@pytest.mark.asyncio
async def test_post_observation_error_keeps_execute_outcome(effect_store):
    adapter = ResultAdapter({"outcome": "succeeded"})

    def fail_post(*args):
        raise LookupError("synthetic private observation")

    adapter.observe_post_state = fail_post
    gateway, envelope = setup(adapter, effect_store)
    receipt = await gateway.execute_envelope(envelope)
    assert receipt.outcome == "succeeded"
    assert receipt.post_observation == {"post_observation_error": "LookupError"}


@pytest.mark.asyncio
@pytest.mark.parametrize("side_effect_class", ["consequential", "irreversible"])
async def test_consequential_with_in_memory_store_denied_before_execute(side_effect_class):
    adapter = ResultAdapter({"outcome": "succeeded"})
    adapter.manifest.side_effect_class = side_effect_class
    store = InMemoryEffectStore()
    gateway = ConsequentialToolGateway(
        adapter,
        project_id="r28a",
        allowed_scopes={"network.https", "mcp.call"},
        current_lease_generation=1,
        store=store,
    )
    envelope = adapter.normalize(
        {"project_id": "r28a", "lease_generation": 1, "cancellation_generation": 0}
    )
    with pytest.raises(StaleLeaseError, match="fence_missing"):
        await gateway.execute_envelope(envelope)
    with pytest.raises(StaleLeaseError, match="fence_missing"):
        await gateway.reconcile(envelope)
    assert adapter.pre_calls == adapter.call_count == 0
    assert row(store, envelope) is None


def test_gateway_requires_store_argument():
    with pytest.raises(TypeError):
        ConsequentialToolGateway(
            ApiMcpAdapter(), project_id="r28a", allowed_scopes=set(), current_lease_generation=1
        )


def test_echo_adapter_reconcile_never_claims_not_applied():
    adapter = ApiMcpAdapter()
    envelope = adapter.normalize(
        {"project_id": "r28a", "lease_generation": 1, "cancellation_generation": 0}
    )
    assert adapter.reconcile(envelope, []) == {
        "state": "unknown",
        "reason": "destination_not_observable",
    }

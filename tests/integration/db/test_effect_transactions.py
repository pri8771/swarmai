"""R27c / ART-V17-APPROVAL-BINDING — repository-owned transactions (Postgres).

`begin_execution` is the committed admission point: the reservation is visible
to a real second OS process before the adapter runs, and a bounded-use approval
is consumed exactly once, atomically, inside that transaction.
"""

from __future__ import annotations

import multiprocessing as mp
import os
import threading
from datetime import timedelta
from typing import Any

import pytest
from sqlalchemy import text

from swarm.contracts.actions import ActionEnvelope, ActionReceiptV17, ApprovalGrant
from swarm.contracts.common import new_id, utc_now
from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import Base
from swarm.tools.adapter_registry import AdapterRegistry
from swarm.tools.adapters.api_mcp import ApiMcpAdapter
from swarm.tools.adapters.base import AdapterNotSentError
from swarm.tools.effects import DurableEffectRepository, EffectConflictError, InMemoryEffectStore
from swarm.tools.fences import (
    ActorContext,
    LeaseFenceProvider,
    StaticFenceProvider,
    StaticPolicyProvider,
)
from swarm.tools.manifests import MANIFEST_DIR, load_manifest
from swarm.tools.v17_gateway import ApprovalInvalidError, ConsequentialToolGateway
from tests.integration.db._effect_tx_child import run_paused_execution
from tests.integration.db.effect_fixtures import bind_lease


def _registry(adapter):
    registry = AdapterRegistry()
    registry.register(adapter)
    return registry


pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)
SCOPES = {"network.https", "mcp.call"}


@pytest.fixture(scope="module")
def engine():
    eng = create_db_engine(DATABASE_URL)
    try:
        ping(eng)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"postgres_unavailable:{type(exc).__name__}")
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def factory(engine):
    fac = make_session_factory(engine)
    yield fac
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE action_receipts, action_effects, approvals, missions, worker_leases "
                "RESTART IDENTITY CASCADE"
            )
        )


class RaisingAdapter(ApiMcpAdapter):
    def execute(self, envelope: ActionEnvelope) -> dict[str, Any]:
        self._calls.append({"effect_key": envelope.effect_key})
        raise AdapterNotSentError("transport_not_started")


def _gateway(adapter: ApiMcpAdapter, factory, project: str = "proj_a") -> ConsequentialToolGateway:
    return ConsequentialToolGateway(
        registry=_registry(adapter),
        store=DurableEffectRepository(factory),
        fences=LeaseFenceProvider(factory),
        policy=StaticPolicyProvider(SCOPES, "v17-policy-1"),
    )


def _context(project: str = "proj_a", actor: str = "worker") -> ActorContext:
    return ActorContext(actor=actor, project_id=project)


def _sql(factory, statement: str, **params: Any) -> Any:
    sess = factory()
    try:
        result = sess.execute(text(statement), params)
        value = result.scalar() if result.returns_rows else None
        sess.commit()
        return value
    finally:
        sess.close()


def _used_count(factory, approval_id: str) -> int:
    return int(_sql(factory, "SELECT used_count FROM approvals WHERE id=:a", a=approval_id) or 0)


@pytest.mark.asyncio
async def test_reservation_visible_to_second_process_before_execute(factory) -> None:
    adapter = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    gw = _gateway(adapter, factory)
    env = adapter.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "cross-process"}
    )
    env = bind_lease(factory, env)
    env.approval_id = gw.make_approval(env, context=_context()).approval_id

    ctx = mp.get_context("spawn")
    started, release, results = ctx.Event(), ctx.Event(), ctx.Queue()
    child = ctx.Process(
        target=run_paused_execution,
        args=(DATABASE_URL, env.model_dump_json(), started, release, results),
    )
    child.start()
    try:
        assert started.wait(timeout=60), "child never reached the adapter"
        # Process A is inside adapter.execute; its admission is already committed.
        with pytest.raises(EffectConflictError, match="effect_already_executing"):
            await gw.execute_envelope(env, context=_context())
        assert adapter.call_count == 0
    finally:
        release.set()
        child.join(timeout=60)
    assert child.exitcode == 0
    outcome = results.get(timeout=10)
    assert outcome.get("outcome") == "succeeded", outcome
    # Now the replay from this process returns the child's original receipt.
    replay = await gw.execute_envelope(env, context=_context())
    assert replay.receipt_id == outcome["receipt_id"]
    assert adapter.call_count == 0


def test_one_shot_approval_two_effect_keys_single_consume(factory) -> None:
    adapter = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    gw = _gateway(adapter, factory)
    base = adapter.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "one-shot"}
    )
    base = bind_lease(factory, base)
    # One-shot grant bound to payload/destination/operation but not to an effect key.
    grant = gw.put_approval(
        ApprovalGrant(
            project_id="proj_a",
            grantor="operator",
            actor=base.actor,
            integration_id=base.integration_id,
            integration_version=base.integration_version,
            operation=base.operation,
            destination=base.destination,
            payload_hash=base.payload_hash,
            effect_key=None,
            max_effect_count=1,
            expires_at=utc_now() + timedelta(seconds=300),
            policy_version=base.policy_version,
        ),
        context=_context(),
    )

    def envelope_with_key(key: str) -> ActionEnvelope:
        env = base.model_copy(update={"effect_key": key, "idempotency_key": key})
        env.approval_id = grant.approval_id
        return env

    envelopes = [envelope_with_key("k1"), envelope_with_key("k2")]
    barrier = threading.Barrier(2)
    outcomes: list[Any] = [None, None]

    def run(index: int) -> None:
        import asyncio

        own_adapter = ApiMcpAdapter(
            load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
        )
        own_gw = _gateway(own_adapter, factory)
        barrier.wait(timeout=10)
        try:
            receipt = asyncio.run(own_gw.execute_envelope(envelopes[index], context=_context()))
            outcomes[index] = ("ok", receipt.outcome, own_adapter.call_count)
        except ApprovalInvalidError as exc:
            outcomes[index] = ("denied", str(exc), own_adapter.call_count)

    threads = [threading.Thread(target=run, args=(i,)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)
    kinds = sorted(o[0] for o in outcomes)
    assert kinds == ["denied", "ok"], outcomes
    denied = next(o for o in outcomes if o[0] == "denied")
    assert denied[1] == "approval_expired_or_revoked_or_exhausted"
    assert denied[2] == 0  # the losing adapter never ran
    assert _used_count(factory, grant.approval_id) == 1


@pytest.mark.asyncio
async def test_retry_of_same_effect_does_not_consume_approval_twice(factory) -> None:
    raising = RaisingAdapter()
    gw = _gateway(raising, factory)
    env = raising.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "retry-once"}
    )
    env = bind_lease(factory, env)
    env.approval_id = gw.make_approval(env, context=_context(), max_effect_count=1).approval_id
    first = await gw.execute_envelope(env, context=_context())
    assert first.outcome == "failed"
    assert _used_count(factory, env.approval_id) == 1
    # A proven pre-send failure now writes not_applied through the gateway.
    assert (
        _sql(
            factory, "SELECT state_reason FROM action_effects WHERE effect_key=:k", k=env.effect_key
        )
        == "not_applied"
    )
    working = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    gw2 = _gateway(working, factory)
    second = await gw2.execute_envelope(env, context=_context())
    assert second.outcome == "succeeded"
    assert second.attempt_number == 2
    assert working.call_count == 1
    assert _used_count(factory, env.approval_id) == 1
    row = gw2.store.get(project_id="proj_a", effect_key=env.effect_key)
    assert row is not None and row["attempt_count"] == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("how", ["revoked", "expired"])
async def test_retry_after_revocation_or_expiry_is_denied(factory, how: str) -> None:
    raising = RaisingAdapter()
    gw = _gateway(raising, factory)
    env = raising.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": f"retry-{how}"}
    )
    env = bind_lease(factory, env)
    env.approval_id = gw.make_approval(env, context=_context(), max_effect_count=1).approval_id
    assert (await gw.execute_envelope(env, context=_context())).outcome == "failed"
    assert (
        _sql(
            factory, "SELECT state_reason FROM action_effects WHERE effect_key=:k", k=env.effect_key
        )
        == "not_applied"
    )
    if how == "revoked":
        _sql(factory, "UPDATE approvals SET revoked_at=now() WHERE id=:a", a=env.approval_id)
    else:
        _sql(
            factory,
            "UPDATE approvals SET expires_at=now() - interval '1 second' WHERE id=:a",
            a=env.approval_id,
        )
    working = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    gw2 = _gateway(working, factory)
    with pytest.raises(ApprovalInvalidError, match="approval_expired_or_revoked_or_exhausted"):
        await gw2.execute_envelope(env, context=_context())
    assert working.call_count == 0
    row = gw2.store.get(project_id="proj_a", effect_key=env.effect_key)
    assert row is not None and row["state"] == "failed" and row["attempt_count"] == 1


@pytest.mark.asyncio
async def test_denied_request_leaves_no_effect_row(factory) -> None:
    adapter = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    gw = _gateway(adapter, factory)
    approved = adapter.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "approved-body"}
    )
    approved = bind_lease(factory, approved)
    approval_id = gw.make_approval(approved, context=_context()).approval_id
    tampered = adapter.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "other-body"}
    )
    tampered = bind_lease(factory, tampered)
    tampered.approval_id = approval_id
    with pytest.raises(ApprovalInvalidError, match="approval_payload_mismatch"):
        await gw.execute_envelope(tampered, context=_context())
    assert adapter.call_count == 0
    assert gw.store.get(project_id="proj_a", effect_key=tampered.effect_key) is None
    assert _sql(factory, "SELECT count(*) FROM action_effects") == 0


@pytest.mark.asyncio
async def test_replay_of_succeeded_effect_works_after_approval_expiry(factory) -> None:
    adapter = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    gw = _gateway(adapter, factory)
    env = adapter.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "replay-expired"}
    )
    env = bind_lease(factory, env)
    env.approval_id = gw.make_approval(env, context=_context()).approval_id
    first = await gw.execute_envelope(env, context=_context())
    assert first.outcome == "succeeded"
    _sql(
        factory,
        "UPDATE approvals SET expires_at=now() - interval '1 second' WHERE id=:a",
        a=env.approval_id,
    )
    replay = await gw.execute_envelope(env, context=_context())
    assert replay.receipt_id == first.receipt_id
    assert adapter.call_count == 1


def test_finalize_state_conflict_when_not_executing(factory) -> None:
    repo = DurableEffectRepository(factory)
    env = ActionEnvelope(
        project_id="proj_a",
        actor="worker",
        integration_id="mcp.echo",
        integration_version="1",
        operation="echo",
        destination="mcp://echo/default",
        normalized_payload={"body": "finalize-conflict"},
        side_effect_class="consequential",
        risk_class="medium",
        lease_generation=1,
        cancellation_generation=0,
    ).ensure_hashes()
    reserved = repo.reserve(env)
    receipt = ActionReceiptV17(
        action_id=env.action_id,
        effect_key=env.effect_key,
        effect_id=reserved["effect_id"],
        project_id="proj_a",
        integration_id="mcp.echo",
        integration_version="1",
        manifest_digest="0" * 64,
        operation="echo",
        destination=env.destination,
        outcome="succeeded",
    )
    with pytest.raises(EffectConflictError, match="finalize_state_conflict"):
        repo.finalize_with_receipt(
            project_id="proj_a",
            effect_key=env.effect_key,
            state="succeeded",
            receipt=receipt,
            expected_execution=(None, 0, "reserved"),
        )
    assert repo.get(project_id="proj_a", effect_key=env.effect_key)["state"] == "reserved"
    assert repo.list_receipts(project_id="proj_a", effect_key=env.effect_key) == []


def test_fence_reader_mismatch_blocks_execution_and_adapter_not_called(factory) -> None:
    repo = DurableEffectRepository(factory)
    env = ActionEnvelope(
        project_id="proj_a",
        actor="worker",
        integration_id="mcp.echo",
        integration_version="1",
        operation="echo",
        destination="mcp://echo/default",
        normalized_payload={"body": "fence"},
        side_effect_class="consequential",
        risk_class="medium",
        lease_generation=1,
        cancellation_generation=3,
    ).ensure_hashes()
    repo.reserve(env)
    calls: list[str] = []

    def reader(session: Any) -> dict[str, int | None]:
        calls.append("read-inside-transaction")
        assert session is not None
        return {"lease_generation": None, "cancellation_generation": 4}

    with pytest.raises(EffectConflictError, match="fence_changed_before_execute"):
        repo.begin_execution(env, executor_id="exe_x", fence_reader=reader)
    assert calls == ["read-inside-transaction"]
    row = repo.get(project_id="proj_a", effect_key=env.effect_key)
    assert row["state"] == "reserved" and row["attempt_count"] == 0
    # Matching fence admits.
    admitted = repo.begin_execution(
        env,
        executor_id="exe_y",
        fence_reader=lambda s: {"lease_generation": 1, "cancellation_generation": 3},
    )
    assert admitted["state"] == "executing" and admitted["attempt_count"] == 1


def _unbound_one_shot_approval(gateway, envelope):
    """Create a one-shot grant usable to distinguish exhaustion from key binding."""
    return gateway.put_approval(
        ApprovalGrant(
            project_id=envelope.project_id,
            grantor="operator",
            actor=envelope.actor,
            integration_id=envelope.integration_id,
            integration_version=envelope.integration_version,
            operation=envelope.operation,
            destination=envelope.destination,
            payload_hash=envelope.payload_hash,
            effect_key=None,
            max_effect_count=1,
            expires_at=utc_now() + timedelta(seconds=300),
            policy_version=envelope.policy_version,
        ),
        context=_context(envelope.project_id, envelope.actor),
    )


@pytest.mark.asyncio
async def test_not_applied_retry_rebinds_from_grant_a_to_b_once(factory) -> None:
    raising = RaisingAdapter()
    gateway_a = _gateway(raising, factory)
    envelope_a = raising.normalize(
        {
            "project_id": "proj_a",
            "destination": "mcp://echo/default",
            "body": "retry-with-replacement-grant",
        }
    )
    envelope_a = bind_lease(factory, envelope_a)
    grant_a = gateway_a.make_approval(envelope_a, context=_context(), max_effect_count=1)
    envelope_a.approval_id = grant_a.approval_id

    first = await gateway_a.execute_envelope(envelope_a, context=_context())
    assert first.outcome == "failed"
    assert _used_count(factory, grant_a.approval_id) == 1
    assert (
        _sql(
            factory,
            "SELECT state_reason FROM action_effects WHERE effect_key=:k",
            k=envelope_a.effect_key,
        )
        == "not_applied"
    )

    working = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    gateway_b = _gateway(working, factory)
    grant_b = _unbound_one_shot_approval(gateway_b, envelope_a)
    envelope_b = envelope_a.model_copy(update={"approval_id": grant_b.approval_id})

    second = await gateway_b.execute_envelope(envelope_b, context=_context())
    assert second.outcome == "succeeded"
    assert second.attempt_number == 2
    assert working.call_count == 1
    assert _used_count(factory, grant_a.approval_id) == 1
    assert _used_count(factory, grant_b.approval_id) == 1
    binding = _sql(
        factory,
        "SELECT approval_id FROM action_effects WHERE project_id=:p AND effect_key=:k",
        p=envelope_b.project_id,
        k=envelope_b.effect_key,
    )
    assert binding == grant_b.approval_id

    # A same-effect replay under B returns the immutable success receipt and must not
    # consume B twice or invoke the adapter again.
    replay = await gateway_b.execute_envelope(envelope_b, context=_context())
    assert replay.receipt_id == second.receipt_id
    assert _used_count(factory, grant_b.approval_id) == 1
    assert working.call_count == 1

    # B was deliberately unbound to an effect key, so this denial proves exhaustion,
    # rather than approval_effect_key_mismatch. No adapter call may occur.
    other_adapter = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    other_gateway = _gateway(other_adapter, factory)
    other = envelope_b.model_copy(
        update={
            "action_id": new_id("act_"),
            "effect_key": "proj_a:replacement-grant-second-effect",
            "idempotency_key": "proj_a:replacement-grant-second-effect",
        }
    )
    with pytest.raises(ApprovalInvalidError, match="approval_expired_or_revoked_or_exhausted"):
        await other_gateway.execute_envelope(other, context=_context())
    assert other_adapter.call_count == 0
    assert _used_count(factory, grant_b.approval_id) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("how", ["revoked", "expired"])
async def test_not_applied_retry_replacement_grant_must_still_be_active(factory, how: str) -> None:
    raising = RaisingAdapter()
    gateway_a = _gateway(raising, factory)
    envelope_a = raising.normalize(
        {
            "project_id": "proj_a",
            "destination": "mcp://echo/default",
            "body": f"replacement-grant-{how}",
        }
    )
    envelope_a = bind_lease(factory, envelope_a)
    grant_a = gateway_a.make_approval(envelope_a, context=_context(), max_effect_count=1)
    envelope_a.approval_id = grant_a.approval_id
    assert (await gateway_a.execute_envelope(envelope_a, context=_context())).outcome == "failed"
    assert (
        _sql(
            factory,
            "SELECT state_reason FROM action_effects WHERE effect_key=:k",
            k=envelope_a.effect_key,
        )
        == "not_applied"
    )

    adapter_b = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    gateway_b = _gateway(adapter_b, factory)
    grant_b = _unbound_one_shot_approval(gateway_b, envelope_a)
    if how == "revoked":
        _sql(factory, "UPDATE approvals SET revoked_at=now() WHERE id=:a", a=grant_b.approval_id)
    else:
        _sql(
            factory,
            "UPDATE approvals SET expires_at=now() - interval '1 second' WHERE id=:a",
            a=grant_b.approval_id,
        )
    envelope_b = envelope_a.model_copy(update={"approval_id": grant_b.approval_id})

    with pytest.raises(ApprovalInvalidError, match="approval_expired_or_revoked_or_exhausted"):
        await gateway_b.execute_envelope(envelope_b, context=_context())
    assert adapter_b.call_count == 0
    assert _used_count(factory, grant_a.approval_id) == 1
    assert _used_count(factory, grant_b.approval_id) == 0
    row = gateway_b.store.get(project_id=envelope_b.project_id, effect_key=envelope_b.effect_key)
    assert row is not None
    assert row["state"] == "failed"
    assert row["state_reason"] == "not_applied"
    assert row["attempt_count"] == 1
    assert row["approval_id"] == grant_a.approval_id


@pytest.mark.asyncio
async def test_in_memory_already_executing_does_not_consume_replacement_grant() -> None:
    store = InMemoryEffectStore()
    first_adapter = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    gateway_a = ConsequentialToolGateway(
        registry=_registry(first_adapter),
        store=store,
        fences=StaticFenceProvider(1, 0),
        policy=StaticPolicyProvider(SCOPES, "v17-policy-1"),
    )
    envelope_a = first_adapter.normalize(
        {
            "project_id": "proj_a",
            "destination": "mcp://echo/default",
            "body": "already-executing-admission",
            "lease_generation": 1,
            "cancellation_generation": 0,
        }
    )
    grant_a = gateway_a.make_approval(envelope_a, context=_context(), max_effect_count=1)
    envelope_a.approval_id = grant_a.approval_id
    store.reserve(envelope_a)
    store.begin_execution(envelope_a, executor_id="exe_first")
    assert store.get_approval(grant_a.approval_id, project_id="proj_a").used_count == 1

    second_adapter = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    gateway_b = ConsequentialToolGateway(
        registry=_registry(second_adapter),
        store=store,
        fences=StaticFenceProvider(1, 0),
        policy=StaticPolicyProvider(SCOPES, "v17-policy-1"),
    )
    grant_b = _unbound_one_shot_approval(gateway_b, envelope_a)
    envelope_b = envelope_a.model_copy(update={"approval_id": grant_b.approval_id})

    with pytest.raises(EffectConflictError, match="effect_already_executing"):
        store.begin_execution(envelope_b, executor_id="exe_rejected")
    assert second_adapter.call_count == 0
    assert store.get_approval(grant_b.approval_id, project_id="proj_a").used_count == 0
    row = store.get(project_id="proj_a", effect_key=envelope_a.effect_key)
    assert row is not None
    assert row["approval_id"] == grant_a.approval_id
    assert row["attempt_count"] == 1


@pytest.mark.asyncio
async def test_returning_to_consumed_grant_on_same_effect_does_not_consume_again(factory):
    adapter = RaisingAdapter()
    gateway = _gateway(adapter, factory)
    env = adapter.normalize({"project_id": "proj_a", "body": "A-B-A-retry"})
    env = bind_lease(factory, env)
    grant_a = gateway.make_approval(env, context=_context())
    grant_b = _unbound_one_shot_approval(gateway, env)
    for number, grant in enumerate((grant_a, grant_b, grant_a, grant_b), start=1):
        env.approval_id = grant.approval_id
        receipt = await gateway.execute_envelope(env, context=_context())
        assert receipt.outcome == "failed"
        assert receipt.approval_id == grant.approval_id
        assert receipt.attempt_number == number
        assert _used_count(factory, grant.approval_id) == 1
        assert (
            _sql(
                factory,
                "SELECT state_reason FROM action_effects WHERE effect_key=:k",
                k=env.effect_key,
            )
            == "not_applied"
        )
    row = gateway.store.get(project_id=env.project_id, effect_key=env.effect_key)
    assert set(row["consumed_approval_ids"]) == {grant_a.approval_id, grant_b.approval_id}
    assert row["approval_id"] == grant_b.approval_id


def test_durable_busy_effect_rolls_back_replacement_approval_and_ledger(factory):
    adapter = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    gateway = _gateway(adapter, factory)
    env = adapter.normalize({"project_id": "proj_a", "body": "busy-durable-rollback"})
    env = bind_lease(factory, env)
    grant_a = gateway.make_approval(env, context=_context())
    env.approval_id = grant_a.approval_id
    gateway.store.reserve(env)
    gateway.store.begin_execution(env, executor_id="original-executor")
    grant_b = _unbound_one_shot_approval(gateway, env)
    changed = env.model_copy(update={"approval_id": grant_b.approval_id})
    with pytest.raises(EffectConflictError, match="effect_already_executing"):
        gateway.store.begin_execution(changed, executor_id="rejected-executor")
    row = gateway.store.get(project_id=env.project_id, effect_key=env.effect_key)
    assert _used_count(factory, grant_b.approval_id) == 0
    assert row["approval_id"] == grant_a.approval_id
    assert row["consumed_approval_ids"] == [grant_a.approval_id]
    assert row["attempt_count"] == 1
    assert adapter.call_count == 0

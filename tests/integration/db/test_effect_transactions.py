"""R27c / ART-V17-APPROVAL-BINDING — repository-owned transactions (Postgres).

`begin_execution` is the committed admission point: the reservation is visible
to a real second OS process before the adapter runs, and a bounded-use approval
is consumed exactly once, atomically, inside that transaction.
"""

from __future__ import annotations

import multiprocessing as mp
import os
import threading
from typing import Any

import pytest
from sqlalchemy import text

from swarm.contracts.actions import ActionEnvelope, ActionReceiptV17
from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import Base
from swarm.tools.adapters.api_mcp import ApiMcpAdapter
from swarm.tools.effects import DurableEffectRepository, EffectConflictError
from swarm.tools.v17_gateway import ApprovalInvalidError, ConsequentialToolGateway
from tests.integration.db._effect_tx_child import run_paused_execution

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
            text("TRUNCATE action_receipts, action_effects, approvals RESTART IDENTITY CASCADE")
        )


class RaisingAdapter(ApiMcpAdapter):
    def execute(self, envelope: ActionEnvelope) -> dict[str, Any]:
        self._calls.append({"effect_key": envelope.effect_key})
        raise RuntimeError("transport_exploded")


def _gateway(adapter: ApiMcpAdapter, factory, project: str = "proj_a") -> ConsequentialToolGateway:
    return ConsequentialToolGateway(
        adapter,
        project_id=project,
        allowed_scopes=SCOPES,
        current_lease_generation=1,
        store=DurableEffectRepository(factory),
    )


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
    adapter = ApiMcpAdapter()
    gw = _gateway(adapter, factory)
    env = adapter.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "cross-process"}
    )
    env.approval_id = gw.make_approval(env).approval_id

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
            await gw.execute_envelope(env)
        assert adapter.call_count == 0
    finally:
        release.set()
        child.join(timeout=60)
    assert child.exitcode == 0
    outcome = results.get(timeout=10)
    assert outcome.get("outcome") == "succeeded", outcome
    # Now the replay from this process returns the child's original receipt.
    replay = await gw.execute_envelope(env)
    assert replay.receipt_id == outcome["receipt_id"]
    assert adapter.call_count == 0


def test_one_shot_approval_two_effect_keys_single_consume(factory) -> None:
    adapter = ApiMcpAdapter()
    gw = _gateway(adapter, factory)
    base = adapter.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "one-shot"}
    )
    grant = gw.make_approval(base, max_effect_count=1)
    grant = grant.model_copy(update={"effect_key": None})
    gw.store.put_approval(grant)  # rebind without an effect key: one use, any key

    def envelope_with_key(key: str) -> ActionEnvelope:
        env = base.model_copy(update={"effect_key": key, "idempotency_key": key})
        env.approval_id = grant.approval_id
        return env

    envelopes = [envelope_with_key("k1"), envelope_with_key("k2")]
    barrier = threading.Barrier(2)
    outcomes: list[Any] = [None, None]

    def run(index: int) -> None:
        import asyncio

        own_adapter = ApiMcpAdapter()
        own_gw = _gateway(own_adapter, factory)
        barrier.wait(timeout=10)
        try:
            receipt = asyncio.run(own_gw.execute_envelope(envelopes[index]))
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
    env.approval_id = gw.make_approval(env, max_effect_count=1).approval_id
    first = await gw.execute_envelope(env)
    assert first.outcome == "failed"
    assert _used_count(factory, env.approval_id) == 1
    # Until R28a nothing writes not_applied; simulate the provable non-application verdict.
    _sql(
        factory,
        "UPDATE action_effects SET state_reason='not_applied' WHERE effect_key=:k",
        k=env.effect_key,
    )
    working = ApiMcpAdapter()
    gw2 = _gateway(working, factory)
    second = await gw2.execute_envelope(env)
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
    env.approval_id = gw.make_approval(env, max_effect_count=1).approval_id
    assert (await gw.execute_envelope(env)).outcome == "failed"
    _sql(
        factory,
        "UPDATE action_effects SET state_reason='not_applied' WHERE effect_key=:k",
        k=env.effect_key,
    )
    if how == "revoked":
        _sql(factory, "UPDATE approvals SET revoked_at=now() WHERE id=:a", a=env.approval_id)
    else:
        _sql(
            factory,
            "UPDATE approvals SET expires_at=now() - interval '1 second' WHERE id=:a",
            a=env.approval_id,
        )
    working = ApiMcpAdapter()
    gw2 = _gateway(working, factory)
    with pytest.raises(ApprovalInvalidError, match="approval_expired_or_revoked_or_exhausted"):
        await gw2.execute_envelope(env)
    assert working.call_count == 0
    row = gw2.store.get(project_id="proj_a", effect_key=env.effect_key)
    assert row is not None and row["state"] == "failed" and row["attempt_count"] == 1


@pytest.mark.asyncio
async def test_denied_request_leaves_no_effect_row(factory) -> None:
    adapter = ApiMcpAdapter()
    gw = _gateway(adapter, factory)
    approved = adapter.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "approved-body"}
    )
    approval_id = gw.make_approval(approved).approval_id
    tampered = adapter.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "other-body"}
    )
    tampered.approval_id = approval_id
    with pytest.raises(ApprovalInvalidError, match="approval_payload_mismatch"):
        await gw.execute_envelope(tampered)
    assert adapter.call_count == 0
    assert gw.store.get(project_id="proj_a", effect_key=tampered.effect_key) is None
    assert _sql(factory, "SELECT count(*) FROM action_effects") == 0


@pytest.mark.asyncio
async def test_replay_of_succeeded_effect_works_after_approval_expiry(factory) -> None:
    adapter = ApiMcpAdapter()
    gw = _gateway(adapter, factory)
    env = adapter.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "replay-expired"}
    )
    env.approval_id = gw.make_approval(env).approval_id
    first = await gw.execute_envelope(env)
    assert first.outcome == "succeeded"
    _sql(
        factory,
        "UPDATE approvals SET expires_at=now() - interval '1 second' WHERE id=:a",
        a=env.approval_id,
    )
    replay = await gw.execute_envelope(env)
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
    ).ensure_hashes()
    reserved = repo.reserve(env)
    receipt = ActionReceiptV17(
        action_id=env.action_id,
        effect_key=env.effect_key,
        effect_id=reserved["effect_id"],
        project_id="proj_a",
        integration_id="mcp.echo",
        integration_version="1",
        operation="echo",
        destination=env.destination,
        outcome="succeeded",
    )
    with pytest.raises(EffectConflictError, match="finalize_state_conflict"):
        repo.finalize_with_receipt(
            project_id="proj_a", effect_key=env.effect_key, state="succeeded", receipt=receipt
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

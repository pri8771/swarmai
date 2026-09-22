"""R27e crash recovery: real PostgreSQL, real child termination, local file effects."""

from __future__ import annotations

import multiprocessing as mp
import os
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import text

from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import Base
from swarm.tools.adapter_registry import AdapterRegistry
from swarm.tools.effects import DurableEffectRepository, EffectConflictError, EffectStoreError
from swarm.tools.fences import ActorContext, LeaseFenceProvider, StaticPolicyProvider
from swarm.tools.manifests import manifest_digest
from swarm.tools.v17_gateway import (
    ApprovalInvalidError,
    ConsequentialToolGateway,
    ReconciliationRequiredError,
)
from tests.integration.db._effect_crash_child import FileEffectAdapter, run_crash
from tests.integration.db.effect_fixtures import bind_lease


def _registry(adapter):
    registry = AdapterRegistry()
    registry.register(adapter)
    return registry


pytestmark = pytest.mark.integration
DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)
CRASH_CONTEXT = ActorContext(actor="worker", project_id="crash_project")


@pytest.fixture(scope="module")
def engine():
    eng = create_db_engine(DATABASE_URL)
    try:
        ping(eng)
    except Exception as exc:
        pytest.skip(f"postgres_unavailable:{type(exc).__name__}")
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def factory(engine):
    yield make_session_factory(engine)
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE action_receipts, action_effects, approvals, missions, worker_leases "
                "RESTART IDENTITY CASCADE"
            )
        )


def setup_effect(factory, tmp_path, side_effect_class="consequential"):
    path = tmp_path / "effects.txt"
    adapter = FileEffectAdapter(str(path))
    store = DurableEffectRepository(factory)
    gateway = ConsequentialToolGateway(
        registry=_registry(adapter),
        store=store,
        fences=LeaseFenceProvider(factory),
        policy=StaticPolicyProvider({"network.https", "mcp.call"}, "v17-policy-1"),
        orphan_grace_seconds=0,
    )
    env = adapter.normalize({"project_id": "crash_project", "body": str(path)})
    env = bind_lease(factory, env)
    env.timeout_seconds = 1
    env.side_effect_class = side_effect_class
    env.approval_id = gateway.make_approval(env, context=CRASH_CONTEXT).approval_id
    return path, adapter, store, gateway, env


def row(store, env):
    return store.get(project_id=env.project_id, effect_key=env.effect_key)


def begin(store, env):
    store.reserve(env)
    return store.begin_execution(env, executor_id="executor_old")


def age(factory, env):
    # Only non-process adverse cases use this deterministic time seam.
    with factory.begin() as session:
        session.execute(
            text(
                "UPDATE action_effects SET started_at=clock_timestamp()-interval '60 seconds' "
                "WHERE effect_key=:key"
            ),
            {"key": env.effect_key},
        )


def recover(store, env):
    return store.recover_orphaned(
        project_id=env.project_id, effect_key=env.effect_key, timeout_seconds=1, grace_seconds=0
    )


def kill_at(phase, env, path):
    child = mp.get_context("spawn").Process(
        target=run_crash, args=(DATABASE_URL, env.model_dump_json(), str(path), phase)
    )
    child.start()
    child.join(timeout=15)
    if child.is_alive():
        child.kill()
        child.join(timeout=5)
        pytest.fail("child did not reach its crash seam")
    assert child.exitcode == 9
    print(f"real_spawn_crash phase={phase} exit={child.exitcode}")
    time.sleep(1.1)  # Real timeout, not a sleep-free clock mock; test-only grace=0.


@pytest.mark.asyncio
async def test_kill_after_side_effect_before_finalize_reconciles_to_succeeded_once(
    factory, tmp_path
):
    path, adapter, store, gateway, env = setup_effect(factory, tmp_path)
    kill_at("after", env, path)
    assert row(store, env)["state"] == "executing"
    result = await gateway.execute_envelope(env, context=CRASH_CONTEXT)
    assert result.outcome == "succeeded" and result.reconciliation_state == "reconciled"
    assert path.read_text().splitlines() == [env.effect_key]
    assert adapter.call_count == 0 and adapter.reconcile_calls == 1
    assert row(store, env)["attempt_count"] == 1
    receipts = store.list_receipts(project_id=env.project_id, effect_key=env.effect_key)
    assert [r.outcome for r in receipts] == ["succeeded"]
    assert (
        await gateway.execute_envelope(env, context=CRASH_CONTEXT)
    ).receipt_id == result.receipt_id
    assert len(path.read_text().splitlines()) == 1


@pytest.mark.asyncio
async def test_kill_before_side_effect_retries_exactly_once(factory, tmp_path):
    path, adapter, store, gateway, env = setup_effect(factory, tmp_path)
    kill_at("before", env, path)
    assert not path.exists()
    result = await gateway.execute_envelope(env, context=CRASH_CONTEXT)
    assert result.outcome == "succeeded"
    assert path.read_text().splitlines() == [env.effect_key]
    assert adapter.call_count == 1 and row(store, env)["attempt_count"] == 2
    receipts = store.list_receipts(project_id=env.project_id, effect_key=env.effect_key)
    assert [r.outcome for r in receipts] == ["failed", "succeeded"]
    assert [r.attempt_number for r in receipts] == [1, 2]
    assert receipts[0].reconciliation_state == "reconciled"
    assert store.get_approval(env.approval_id, project_id=env.project_id).used_count == 1
    await gateway.execute_envelope(env, context=CRASH_CONTEXT)
    assert adapter.call_count == 1


@pytest.mark.asyncio
async def test_live_executor_is_not_taken_over(factory, tmp_path):
    _, adapter, store, gateway, env = setup_effect(factory, tmp_path)
    begin(store, env)
    with pytest.raises(EffectConflictError, match="effect_already_executing"):
        await gateway.execute_envelope(env, context=CRASH_CONTEXT)
    assert adapter.call_count == 0 and adapter.reconcile_calls == 0
    assert row(store, env)["state"] == "executing"
    assert (
        ConsequentialToolGateway(
            registry=_registry(adapter),
            store=store,
            fences=LeaseFenceProvider(factory),
            policy=StaticPolicyProvider(set(), "v17-policy-1"),
        ).orphan_grace_seconds
        == 30
    )


def test_orphan_never_returns_to_reserved_and_recovery_has_one_winner(factory, tmp_path):
    _, _, store, _, env = setup_effect(factory, tmp_path)
    begin(store, env)
    age(factory, env)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: recover(store, env), range(2)))
    assert sorted(results) == [False, True]
    recovered = row(store, env)
    assert recovered["state"] == "unknown" and recovered["state_reason"] == "executor_lost"
    assert store.reserve(env)["state"] == "unknown"
    with pytest.raises(EffectConflictError, match="effect_unknown_requires_reconcile"):
        store.begin_execution(env, executor_id="not_admitted")


@pytest.mark.asyncio
async def test_irreversible_not_applied_requires_operator_rearm(factory, tmp_path):
    path, adapter, store, gateway, env = setup_effect(factory, tmp_path, "irreversible")
    begin(store, env)
    age(factory, env)
    for _ in range(2):
        with pytest.raises(
            ReconciliationRequiredError, match="irreversible_requires_operator_disposition"
        ):
            await gateway.execute_envelope(env, context=CRASH_CONTEXT)
    assert not path.exists() and adapter.call_count == 0
    assert adapter.reconcile_calls == 1
    for operator, reason in [("", "confirmed absent"), ("owner", "")]:
        with pytest.raises(EffectStoreError, match="operator_and_reason_required"):
            store.rearm_irreversible(
                project_id=env.project_id,
                effect_key=env.effect_key,
                operator=operator,
                reason=reason,
            )
    store.rearm_irreversible(
        project_id=env.project_id,
        effect_key=env.effect_key,
        operator="test_operator",
        reason="independently confirmed absent",
    )
    assert row(store, env)["reconciliation"]["operator_rearms"][0]["operator"] == "test_operator"
    with pytest.raises(EffectConflictError, match="irreversible_rearm_not_allowed"):
        store.rearm_irreversible(
            project_id=env.project_id,
            effect_key=env.effect_key,
            operator="test_operator",
            reason="duplicate",
        )
    assert (await gateway.execute_envelope(env, context=CRASH_CONTEXT)).outcome == "succeeded"
    assert len(path.read_text().splitlines()) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("verdict", ["unknown", "garbage", "failed"])
async def test_reconcile_garbage_verdict_stays_unknown_and_never_executes(
    factory, tmp_path, monkeypatch, verdict
):
    path, adapter, store, gateway, env = setup_effect(factory, tmp_path)
    begin(store, env)
    age(factory, env)
    monkeypatch.setattr(adapter, "reconcile", lambda *_: {"state": verdict})
    with pytest.raises(ReconciliationRequiredError, match="external_outcome_still_unknown"):
        await gateway.execute_envelope(env, context=CRASH_CONTEXT)
    assert row(store, env)["state"] == "unknown" and not path.exists()
    receipts = store.list_receipts(project_id=env.project_id, effect_key=env.effect_key)
    assert len(receipts) == 1 and receipts[0].reconciliation_state == "pending"


@pytest.mark.asyncio
async def test_reconciliation_does_not_restore_revoked_approval(factory, tmp_path):
    path, _, store, gateway, env = setup_effect(factory, tmp_path)
    begin(store, env)
    age(factory, env)
    gateway.revoke_approval(
        env.approval_id,
        context=ActorContext(actor="test_operator", project_id="crash_project"),
        reason="revoked",
    )
    with pytest.raises(ApprovalInvalidError):
        await gateway.execute_envelope(env, context=CRASH_CONTEXT)
    assert row(store, env)["state"] == "failed" and not path.exists()
    assert row(store, env)["attempt_count"] == 1


@pytest.mark.parametrize("new_attempt", [False, True])
def test_stale_executor_cannot_finalize_or_overwrite_observations(factory, tmp_path, new_attempt):
    _, adapter, store, gateway, env = setup_effect(factory, tmp_path)
    manifest_hash = manifest_digest(adapter.manifest)
    old = begin(store, env)
    age(factory, env)
    assert recover(store, env)
    if new_attempt:
        current = row(store, env)
        gateway._finalize(
            env,
            current,
            state="failed",
            outcome="failed",
            state_reason="not_applied",
            pre={},
            post={"state": "not_applied"},
            manifest_hash=manifest_hash,
        )
        store.begin_execution(env, executor_id="executor_new")
    before = row(store, env)
    receipts_before = store.list_receipts(project_id=env.project_id, effect_key=env.effect_key)
    with pytest.raises(EffectConflictError, match="finalize_state_conflict"):
        gateway._finalize(
            env,
            old,
            state="succeeded",
            outcome="succeeded",
            pre={},
            post={},
            manifest_hash=manifest_hash,
        )
    with pytest.raises(EffectConflictError, match="pre_observation_state_conflict"):
        store.attach_pre_observation(
            project_id=env.project_id,
            effect_key=env.effect_key,
            pre_observation={"stale": True},
            expected_execution=(old["executor_id"], old["attempt_count"], "executing"),
        )
    assert row(store, env) == before
    assert (
        store.list_receipts(project_id=env.project_id, effect_key=env.effect_key) == receipts_before
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "change, error",
    [
        ({"side_effect_class": "consequential"}, "effect_class_binding_mismatch"),
        ({"timeout_seconds": 2}, "effect_timeout_binding_mismatch"),
    ],
)
async def test_recovery_cannot_reclassify_effect_or_change_timeout(
    factory, tmp_path, change, error
):
    path, adapter, store, gateway, env = setup_effect(factory, tmp_path, "irreversible")
    begin(store, env)
    age(factory, env)
    with pytest.raises(EffectConflictError, match=error):
        await gateway.execute_envelope(env.model_copy(update=change), context=CRASH_CONTEXT)
    assert row(store, env)["state"] == "executing" and not path.exists()
    assert adapter.reconcile_calls == 0


def test_rearm_rejects_unknown_project_and_nonfailed_state(factory, tmp_path):
    _, _, store, _, env = setup_effect(factory, tmp_path, "irreversible")
    begin(store, env)
    with pytest.raises(EffectStoreError, match="effect_not_found"):
        store.rearm_irreversible(
            project_id="different_project",
            effect_key=env.effect_key,
            operator="operator",
            reason="reason",
        )
    with pytest.raises(EffectConflictError, match="irreversible_rearm_not_allowed"):
        store.rearm_irreversible(
            project_id=env.project_id,
            effect_key=env.effect_key,
            operator="operator",
            reason="reason",
        )


@pytest.mark.asyncio
async def test_reconcile_exception_is_retained_as_pending_receipt(factory, tmp_path, monkeypatch):
    path, adapter, store, gateway, env = setup_effect(factory, tmp_path)
    begin(store, env)
    age(factory, env)

    def fail_probe(*_):
        raise RuntimeError("synthetic private probe detail")

    monkeypatch.setattr(adapter, "reconcile", fail_probe)
    with pytest.raises(ReconciliationRequiredError, match="external_outcome_still_unknown"):
        await gateway.execute_envelope(env, context=CRASH_CONTEXT)
    receipts = store.list_receipts(project_id=env.project_id, effect_key=env.effect_key)
    assert len(receipts) == 1 and receipts[0].reconciliation_state == "pending"
    assert "synthetic private probe detail" not in receipts[0].model_dump_json()
    assert row(store, env)["state"] == "unknown" and not path.exists()


def test_concurrent_reconcile_has_one_terminal_disposition(factory, tmp_path, monkeypatch):
    import asyncio
    import threading

    path, adapter, store, gateway, env = setup_effect(factory, tmp_path)
    begin(store, env)
    path.write_text(env.effect_key + "\n")  # Existing external-effect fixture.
    age(factory, env)
    assert recover(store, env)
    barrier = threading.Barrier(2)

    def reconcile_once(*_):
        barrier.wait(timeout=5)
        return {"state": "succeeded"}

    monkeypatch.setattr(adapter, "reconcile", reconcile_once)

    def run(_):
        try:
            return asyncio.run(gateway.execute_envelope(env, context=CRASH_CONTEXT)).outcome
        except EffectConflictError as exc:
            return str(exc)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, range(2)))
    assert sorted(results) == ["finalize_state_conflict", "succeeded"]
    assert row(store, env)["state"] == "succeeded"
    assert len(store.list_receipts(project_id=env.project_id, effect_key=env.effect_key)) == 1
    assert path.read_text().splitlines() == [env.effect_key] and adapter.call_count == 0


def test_public_repository_rejects_missing_execution_token(factory, tmp_path):
    from swarm.contracts.actions import ActionReceiptV17

    _, _, store, _, env = setup_effect(factory, tmp_path)
    begin(store, env)
    age(factory, env)
    assert recover(store, env)
    receipt = ActionReceiptV17(
        action_id=env.action_id,
        effect_key=env.effect_key,
        project_id=env.project_id,
        integration_id=env.integration_id,
        integration_version=env.integration_version,
        manifest_digest="0" * 64,
        operation=env.operation,
        destination=env.destination,
        outcome="succeeded",
    )
    with pytest.raises(EffectConflictError, match="execution_token_required"):
        store.finalize_with_receipt(
            project_id=env.project_id, effect_key=env.effect_key, state="succeeded", receipt=receipt
        )
    with pytest.raises(EffectConflictError, match="execution_token_required"):
        store.attach_pre_observation(
            project_id=env.project_id, effect_key=env.effect_key, pre_observation={"stale": True}
        )
    assert row(store, env)["state"] == "unknown"
    assert store.list_receipts(project_id=env.project_id, effect_key=env.effect_key) == []


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_result", [None, [], "bad"])
async def test_malformed_reconcile_result_is_pending(factory, tmp_path, monkeypatch, bad_result):
    path, adapter, store, gateway, env = setup_effect(factory, tmp_path)
    begin(store, env)
    age(factory, env)
    monkeypatch.setattr(adapter, "reconcile", lambda *_: bad_result)
    with pytest.raises(ReconciliationRequiredError, match="external_outcome_still_unknown"):
        await gateway.execute_envelope(env, context=CRASH_CONTEXT)
    receipts = store.list_receipts(project_id=env.project_id, effect_key=env.effect_key)
    assert len(receipts) == 1 and receipts[0].reconciliation_state == "pending"
    assert row(store, env)["state"] == "unknown" and not path.exists()

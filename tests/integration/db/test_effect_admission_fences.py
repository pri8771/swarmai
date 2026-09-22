"""Gateway admission against real durable lease authority; simulated adapters only."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from swarm.contracts.common import new_id
from swarm.db.engine import make_session_factory
from swarm.db.lease_fencing import LeaseLifecycleService
from swarm.db.repositories import MissionRepository
from swarm.tools.adapters.api_mcp import ApiMcpAdapter
from swarm.tools.effects import EffectConflictError
from swarm.tools.v17_gateway import StaleLeaseError
from tests.integration.db.test_effect_transactions import (
    _gateway,
    _sql,
    _used_count,
)
from tests.integration.db.test_effect_transactions import (
    engine as engine,
)
from tests.integration.db.test_lease_claim_renew_expire import (
    _insert_ready_task,
    _register_worker,
    _unique_mission,
)

pytestmark = pytest.mark.integration


@pytest.fixture
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


def _leased_envelope(factory, adapter):
    with factory() as session:
        mission = _unique_mission()
        MissionRepository(session).insert(mission)
        session.flush()
        task = _insert_ready_task(session, mission=mission, required_capabilities=["code.read"])
        token = new_id("test_token_")
        worker_id = _register_worker(
            session, project_id=mission.project_id, capabilities=["code.read"], token=token
        )
        lease = LeaseLifecycleService(session).claim_eligible_attempt(
            worker_id=worker_id, membership_token=token, lease_seconds=300
        )
        assert lease is not None
        envelope = adapter.normalize(
            {
                "project_id": mission.project_id,
                "mission_id": mission.id,
                "task_id": task.id,
                "attempt_id": lease.attempt_id,
                "lease_generation": lease.worker_generation,
                "cancellation_generation": mission.cancellation_generation,
                "actor": worker_id,
                "body": "offline durable-fence regression",
            }
        )
        session.commit()
        return envelope


@pytest.mark.asyncio
async def test_gateway_admits_current_durable_lease(factory):
    adapter = ApiMcpAdapter()
    env = _leased_envelope(factory, adapter)
    gateway = _gateway(adapter, factory, project=env.project_id)
    env.approval_id = gateway.make_approval(env).approval_id
    receipt = await gateway.execute_envelope(env)
    assert receipt.outcome == "succeeded"
    assert adapter.call_count == 1
    assert _used_count(factory, env.approval_id) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["cancel", "worker_generation", "expire", "revoke", "missing"])
async def test_gateway_fences_durable_change_after_local_precheck(factory, monkeypatch, change):
    adapter = ApiMcpAdapter()
    env = _leased_envelope(factory, adapter)
    gateway = _gateway(adapter, factory, project=env.project_id)
    env.approval_id = gateway.make_approval(env).approval_id
    original_reserve = gateway.store.reserve

    def reserve_then_change(envelope):
        row = original_reserve(envelope)
        # A distinct, committed transaction changes authority AFTER the gateway's
        # local generation precheck. The gateway integers intentionally stay stale.
        if change == "cancel":
            with factory() as session:
                LeaseLifecycleService(session).revoke_mission_work(
                    mission_id=env.mission_id, notify_leases=False
                )
                session.commit()
        elif change == "worker_generation":
            _sql(
                factory,
                "UPDATE worker_leases SET lease_generation=lease_generation+1 WHERE worker_id=:w",
                w=env.actor,
            )
        elif change == "expire":
            _sql(
                factory,
                "UPDATE task_leases SET expires_at=now()-interval '1 second' WHERE attempt_id=:a",
                a=env.attempt_id,
            )
        elif change == "revoke":
            _sql(
                factory, "UPDATE worker_leases SET revoked_at=now() WHERE worker_id=:w", w=env.actor
            )
        else:
            _sql(factory, "DELETE FROM task_leases WHERE attempt_id=:a", a=env.attempt_id)
        return row

    monkeypatch.setattr(gateway.store, "reserve", reserve_then_change)
    with pytest.raises(EffectConflictError, match="fence_changed_before_execute"):
        await gateway.execute_envelope(env)
    assert adapter.call_count == 0
    assert _used_count(factory, env.approval_id) == 0
    row = gateway.store.get(project_id=env.project_id, effect_key=env.effect_key)
    assert row["state"] == "reserved"
    assert row["attempt_count"] == 0
    assert row["approval_consumed_at"] is None


@pytest.mark.asyncio
async def test_partial_lease_context_fails_closed(factory):
    adapter = ApiMcpAdapter()
    env = _leased_envelope(factory, adapter)
    env.attempt_id = None
    gateway = _gateway(adapter, factory, project=env.project_id)
    env.approval_id = gateway.make_approval(env).approval_id
    with pytest.raises(StaleLeaseError, match="fence_missing"):
        await gateway.execute_envelope(env)
    assert adapter.call_count == 0
    assert _used_count(factory, env.approval_id) == 0


@pytest.mark.asyncio
async def test_reserved_effect_cannot_strip_lease_binding(factory):
    adapter = ApiMcpAdapter()
    env = _leased_envelope(factory, adapter)
    gateway = _gateway(adapter, factory, project=env.project_id)
    env.approval_id = gateway.make_approval(env).approval_id
    gateway.store.reserve(env)
    stripped = env.model_copy(update={"mission_id": None, "task_id": None, "attempt_id": None})
    with pytest.raises(StaleLeaseError, match="fence_missing"):
        await gateway.execute_envelope(stripped)
    assert adapter.call_count == 0
    assert _used_count(factory, env.approval_id) == 0


def test_authority_lock_is_held_through_admission_commit(factory, monkeypatch):
    import asyncio
    import threading
    import time

    import swarm.tools.effects as effects

    adapter = ApiMcpAdapter()
    env = _leased_envelope(factory, adapter)
    gateway = _gateway(adapter, factory, project=env.project_id)
    env.approval_id = gateway.make_approval(env).approval_id
    at_cas, release, cancelled = threading.Event(), threading.Event(), threading.Event()
    errors = []
    original_cas = effects._cas_to_executing

    def paused_cas(session, **kwargs):
        at_cas.set()
        assert release.wait(10), "test did not release admission"
        return original_cas(session, **kwargs)

    def admit():
        try:
            asyncio.run(gateway.execute_envelope(env))
        except BaseException as exc:
            errors.append(exc)

    def cancel():
        try:
            with factory() as session:
                session.execute(text("SET application_name='codex_test_fence_cancel'"))
                LeaseLifecycleService(session).revoke_mission_work(
                    mission_id=env.mission_id, notify_leases=False
                )
                session.commit()
            cancelled.set()
        except BaseException as exc:
            errors.append(exc)

    monkeypatch.setattr(effects, "_cas_to_executing", paused_cas)
    admission = threading.Thread(target=admit)
    cancellation = threading.Thread(target=cancel)
    admission.start()
    try:
        assert at_cas.wait(10), "gateway never reached admission CAS"
        cancellation.start()
        deadline = time.monotonic() + 5
        lock_wait = None
        while time.monotonic() < deadline:
            lock_wait = _sql(
                factory,
                "SELECT wait_event_type FROM pg_stat_activity WHERE application_name='codex_test_fence_cancel' AND state='active'",
            )
            if lock_wait == "Lock":
                break
            time.sleep(0.01)
        assert lock_wait == "Lock", "cancellation did not wait on admission's authority lock"
        assert not cancelled.is_set()
        assert adapter.call_count == 0
    finally:
        release.set()
        admission.join(10)
        if cancellation.ident is not None:
            cancellation.join(10)
    assert not admission.is_alive() and not cancellation.is_alive()
    assert not errors
    assert cancelled.is_set()
    assert adapter.call_count == 1
    assert _used_count(factory, env.approval_id) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("outcome", ["succeeded", "unknown"])
async def test_terminal_or_unknown_effect_cannot_be_reused_by_another_mission(
    factory, monkeypatch, outcome
):
    adapter = ApiMcpAdapter()
    env = _leased_envelope(factory, adapter)
    if outcome == "unknown":
        env.normalized_payload["force_unknown"] = True
        env.payload_hash = ""
        env.effect_key = ""
        env.ensure_hashes()
    gateway = _gateway(adapter, factory, project=env.project_id)
    env.approval_id = gateway.make_approval(env).approval_id
    assert (await gateway.execute_envelope(env)).outcome == outcome

    def forbidden_reconcile(*args, **kwargs):
        pytest.fail("changed authority must be rejected before adapter reconciliation")

    monkeypatch.setattr(adapter, "reconcile", forbidden_reconcile)
    changed = env.model_copy(
        update={
            "mission_id": "another-mission",
            "task_id": "another-task",
            "attempt_id": "another-attempt",
        }
    )
    with pytest.raises(EffectConflictError, match="effect_authority_binding_mismatch"):
        await gateway.execute_envelope(changed)
    assert adapter.call_count == 1
    assert _used_count(factory, env.approval_id) == 1

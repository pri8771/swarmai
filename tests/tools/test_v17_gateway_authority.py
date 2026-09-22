"""R28b-2 authenticated actor, policy, and durable fence authority."""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import select, text
from tests.integration.db.effect_fixtures import bind_lease
from tests.integration.db.test_effect_transactions import engine as engine

from swarm.db.lease_fencing import (
    LeaseClaimError,
    LeaseLifecycleService,
    read_current_fence,
)
from swarm.db.models import ApprovalRow
from swarm.tools.adapter_registry import AdapterRegistry
from swarm.tools.adapters.api_mcp import ApiMcpAdapter
from swarm.tools.effects import DurableEffectRepository, EffectConflictError, InMemoryEffectStore
from swarm.tools.fences import (
    ActorContext,
    FenceState,
    LeaseFenceProvider,
    StaticFenceProvider,
    StaticPolicyProvider,
)
from swarm.tools.manifests import MANIFEST_DIR, load_manifest
from swarm.tools.v17_gateway import (
    CancellationFenceError,
    ConsequentialToolGateway,
    PolicyDeniedError,
    StaleLeaseError,
    ToolAuthorizationError,
)


def _registry(adapter):
    registry = AdapterRegistry()
    registry.register(adapter)
    return registry


pytestmark = pytest.mark.integration

SCOPES = {"network.https", "mcp.call"}
TRUSTED = ActorContext(actor="worker", project_id="proj_a")


@pytest.fixture()
def factory(engine):
    from swarm.db.engine import make_session_factory

    fac = make_session_factory(engine)
    yield fac
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE action_receipts, action_effects, approvals, missions, "
                "worker_leases RESTART IDENTITY CASCADE"
            )
        )


def leased(factory, adapter: ApiMcpAdapter):
    envelope = adapter.normalize({"project_id": "proj_a", "actor": "worker"})
    return bind_lease(factory, envelope)


def gateway(
    factory,
    adapter: ApiMcpAdapter,
    *,
    fences=None,
    scopes: set[str] = SCOPES,
    policy_version: str = "v17-policy-1",
):
    return ConsequentialToolGateway(
        registry=_registry(adapter),
        store=DurableEffectRepository(factory),
        fences=fences or LeaseFenceProvider(factory),
        policy=StaticPolicyProvider(scopes, policy_version),
    )


def used_count(factory, approval_id: str) -> int:
    with factory() as session:
        return int(
            session.scalar(select(ApprovalRow.used_count).where(ApprovalRow.id == approval_id))
        )


class ForbiddenFence:
    def current(self, **identity: Any):
        pytest.fail(f"fence provider reached before policy denial: {identity}")

    def reader(self, **identity: Any):
        pytest.fail(f"fence reader reached before policy denial: {identity}")


class ForbiddenStore(InMemoryEffectStore):
    def get(self, **identity: Any):
        pytest.fail(f"effect store reached before policy denial: {identity}")

    def reserve(self, envelope):
        pytest.fail(f"effect reservation reached before policy denial: {envelope.effect_key}")


@pytest.mark.asyncio
@pytest.mark.parametrize("entrypoint", ["execute", "reconcile"])
@pytest.mark.parametrize(
    ("case", "policy_version", "requested_scopes", "error", "reason"),
    [
        (
            "stale_policy",
            "v17-policy-2",
            ["network.https", "mcp.call"],
            PolicyDeniedError,
            "policy_version_stale",
        ),
        (
            "denied_scope",
            "v17-policy-1",
            ["network.https", "mcp.call", "tenant.extra"],
            ToolAuthorizationError,
            "denied_scopes:.*tenant.extra",
        ),
    ],
)
async def test_policy_denial_precedes_missing_fence_and_all_effect_boundaries(
    entrypoint, case, policy_version, requested_scopes, error, reason
):
    adapter = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    envelope = adapter.normalize(
        {
            "project_id": "proj_a",
            "actor": "worker",
            "policy_version": "v17-policy-1",
        }
    )
    assert envelope.mission_id is None and envelope.lease_generation is None
    envelope.requested_scopes = requested_scopes
    subject = ConsequentialToolGateway(
        registry=_registry(adapter),
        store=ForbiddenStore(),
        fences=ForbiddenFence(),
        policy=StaticPolicyProvider(SCOPES, policy_version),
    )

    with pytest.raises(error, match=reason):
        if entrypoint == "execute":
            await subject.execute_envelope(envelope, context=TRUSTED)
        else:
            await subject.reconcile(envelope, context=TRUSTED)

    assert case in {"stale_policy", "denied_scope"}
    assert adapter.call_count == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("context", "reason"),
    [
        (ActorContext(actor="worker", project_id="other-project"), "wrong_project"),
        (ActorContext(actor="forged", project_id="proj_a"), "actor_mismatch"),
    ],
)
async def test_context_denied_before_reservation(factory, context, reason):
    adapter = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    envelope = leased(factory, adapter)
    store = DurableEffectRepository(factory)
    subject = ConsequentialToolGateway(
        registry=_registry(adapter),
        store=store,
        fences=LeaseFenceProvider(factory),
        policy=StaticPolicyProvider(SCOPES, "v17-policy-1"),
    )

    with pytest.raises(ToolAuthorizationError, match=reason):
        await subject.execute_envelope(envelope, context=context)

    assert adapter.call_count == 0
    assert store.get(project_id=envelope.project_id, effect_key=envelope.effect_key) is None


@pytest.mark.asyncio
async def test_stale_policy_denied_before_reservation(factory):
    adapter = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    envelope = leased(factory, adapter)
    store = DurableEffectRepository(factory)
    subject = gateway(factory, adapter, policy_version="v17-policy-2")

    with pytest.raises(PolicyDeniedError, match="policy_version_stale"):
        await subject.execute_envelope(envelope, context=TRUSTED)

    assert adapter.call_count == 0
    assert store.get(project_id=envelope.project_id, effect_key=envelope.effect_key) is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("requested", "allowed", "missing"),
    [
        ([], {"network.https"}, "mcp.call"),
        (["network.https", "mcp.call", "tenant.extra"], SCOPES, "tenant.extra"),
    ],
)
async def test_policy_requires_declaration_union_requested(factory, requested, allowed, missing):
    adapter = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    envelope = leased(factory, adapter)
    envelope.requested_scopes = requested
    store = DurableEffectRepository(factory)
    subject = gateway(factory, adapter, scopes=allowed)

    with pytest.raises(ToolAuthorizationError, match=f"denied_scopes:.*{missing}"):
        await subject.execute_envelope(envelope, context=TRUSTED)

    assert adapter.call_count == 0
    assert store.get(project_id=envelope.project_id, effect_key=envelope.effect_key) is None


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["lease", "cancellation"])
async def test_provider_generation_is_authority(factory, field):
    adapter = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    envelope = leased(factory, adapter)
    lease = int(envelope.lease_generation)
    cancellation = int(envelope.cancellation_generation)
    fences = StaticFenceProvider(
        lease_generation=lease + (field == "lease"),
        cancellation_generation=cancellation + (field == "cancellation"),
    )
    store = DurableEffectRepository(factory)
    subject = gateway(factory, adapter, fences=fences)
    approval = subject.make_approval(envelope, context=TRUSTED)
    envelope.approval_id = approval.approval_id
    expected = StaleLeaseError if field == "lease" else CancellationFenceError
    reason = "stale_lease_generation" if field == "lease" else "cancellation_generation_mismatch"

    with pytest.raises(expected, match=reason):
        await subject.execute_envelope(envelope, context=TRUSTED)

    assert adapter.call_count == 0
    assert used_count(factory, approval.approval_id) == 0
    assert store.get(project_id=envelope.project_id, effect_key=envelope.effect_key) is None


@pytest.mark.parametrize(
    ("change", "value"),
    [
        ("mission_id", None),
        ("mission_id", "missing-mission"),
        ("attempt_id", None),
        ("attempt_id", "missing-attempt"),
        ("project_id", "other-project"),
        ("task_id", "wrong-task"),
    ],
)
def test_read_current_fence_rejects_missing_or_mismatched_binding(factory, change, value):
    envelope = leased(
        factory,
        ApiMcpAdapter(
            load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
        ),
    )
    identity = {
        "project_id": envelope.project_id,
        "mission_id": envelope.mission_id,
        "task_id": envelope.task_id,
        "attempt_id": envelope.attempt_id,
    }
    identity[change] = value

    with factory() as session, pytest.raises(LeaseClaimError, match="lease_not_current"):
        read_current_fence(session, **identity)


@pytest.mark.asyncio
async def test_cancellation_bump_between_precheck_and_begin_fails_closed(factory, monkeypatch):
    adapter = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    envelope = leased(factory, adapter)
    subject = gateway(factory, adapter)
    approval = subject.make_approval(envelope, context=TRUSTED)
    envelope.approval_id = approval.approval_id
    original_reserve = subject.store.reserve
    hook_called = False

    def reserve_then_cancel(candidate):
        nonlocal hook_called
        hook_called = True
        reserved = original_reserve(candidate)
        with factory() as session:
            LeaseLifecycleService(session).revoke_mission_work(
                mission_id=envelope.mission_id,
                notify_leases=False,
            )
            session.commit()
        return reserved

    monkeypatch.setattr(subject.store, "reserve", reserve_then_cancel)
    with pytest.raises(EffectConflictError, match="fence_changed_before_execute"):
        await subject.execute_envelope(envelope, context=TRUSTED)

    assert hook_called is True
    assert adapter.call_count == 0
    assert used_count(factory, approval.approval_id) == 0
    persisted = subject.store.get(project_id=envelope.project_id, effect_key=envelope.effect_key)
    assert persisted is not None
    assert persisted["state"] == "reserved"
    assert persisted["attempt_count"] == 0
    assert persisted["approval_consumed_at"] is None


class FutureAuthorityFence:
    def __init__(self, delegate: LeaseFenceProvider) -> None:
        self.delegate = delegate

    def current(self, **identity: Any) -> FenceState:
        current = self.delegate.current(**identity)
        return current.model_copy(update={"authority": {"site_epoch": 999, "grant_epoch": 31337}})

    def reader(self, **identity: Any):
        return self.delegate.reader(**identity)

    def admission_guard(self):
        return self.delegate.admission_guard()


@pytest.mark.asyncio
async def test_v17_does_not_consume_reserved_future_authority(factory):
    adapter = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    envelope = leased(factory, adapter)
    subject = gateway(factory, adapter, fences=FutureAuthorityFence(LeaseFenceProvider(factory)))
    approval = subject.make_approval(envelope, context=TRUSTED)
    envelope.approval_id = approval.approval_id

    receipt = await subject.execute_envelope(envelope, context=TRUSTED)

    assert receipt.outcome == "succeeded"
    assert adapter.call_count == 1
    assert used_count(factory, approval.approval_id) == 1

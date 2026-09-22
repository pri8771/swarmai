"""R28c single consequential path: legacy calls enter the durable V1.7 boundary."""

from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest
from sqlalchemy import text
from tests.integration.db.effect_fixtures import bind_lease

from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import Base
from swarm.tools.adapter_registry import AdapterRegistry
from swarm.tools.effects import DurableEffectRepository, EffectConflictError, InMemoryEffectStore
from swarm.tools.fences import (
    ActorContext,
    LeaseFenceProvider,
    StaticFenceProvider,
    StaticPolicyProvider,
)
from swarm.tools.gateway import (
    LegacyToolAuthorizationError,
    LegacyToolCallAdapter,
    ToolGateway,
)
from swarm.tools.registry import CapabilityRegistry, ToolSpec, hash_operation
from swarm.tools.v17_gateway import (
    CancellationFenceError,
    ConsequentialToolGateway,
    StaleLeaseError,
)

SOURCE = Path(__file__).resolve().parents[2] / "src" / "swarm"
DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)


@pytest.fixture(scope="module")
def engine():
    subject = create_db_engine(DATABASE_URL)
    try:
        ping(subject)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"postgres_unavailable:{type(exc).__name__}")
    Base.metadata.create_all(subject)
    yield subject
    subject.dispose()


@pytest.fixture()
def factory(engine):
    subject = make_session_factory(engine)
    yield subject
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE action_receipts, action_effects, approvals, missions, "
                "worker_leases RESTART IDENTITY CASCADE"
            )
        )


def _capability(handler) -> CapabilityRegistry:
    registry = CapabilityRegistry()
    registry.register(
        ToolSpec(
            name="legacy.send",
            version="1",
            required_scopes=("legacy.send",),
            side_effecting=True,
            description="Synthetic consequential legacy handler",
        ),
        handler,
    )
    return registry


def _call(*, operation_id: str = "op_legacy_once", body: str = "fixture"):
    from swarm.contracts.workspace import ToolCall

    args = {"body": body, "destination": "legacy.send"}
    return ToolCall(
        operation_id=operation_id,
        task_id="unbound-task",
        attempt_id="unbound-attempt",
        tool_version="legacy.send@1",
        normalized_args=args,
        payload_hash=hash_operation("legacy.send@1", args, "legacy.send"),
        scopes=["legacy.send"],
        lease_generation=1,
    )


def _action_gateway(factory, adapter: LegacyToolCallAdapter) -> ConsequentialToolGateway:
    registry = AdapterRegistry()
    registry.register(adapter)
    return ConsequentialToolGateway(
        registry=registry,
        store=DurableEffectRepository(factory),
        fences=LeaseFenceProvider(factory),
        policy=StaticPolicyProvider({"legacy.send"}, "v17-policy-1"),
    )


def _legacy_gateway(
    capability: CapabilityRegistry,
    action_gateway: ConsequentialToolGateway | None,
    *,
    context: ActorContext | None = None,
) -> ToolGateway:
    return ToolGateway(
        capability,
        allowed_scopes={"legacy.send"},
        current_lease_generation=1,
        action_gateway=action_gateway,
        context=context,
        mission_id="unbound-mission",
        cancellation_generation=0,
    )


def _bind_and_approve(factory, gateway: ToolGateway, call) -> None:
    assert gateway.action_gateway is not None and gateway.context is not None
    bound = bind_lease(factory, gateway.action_envelope(call))
    gateway.mission_id = bound.mission_id
    gateway.cancellation_generation = bound.cancellation_generation
    gateway.current_lease_generation = int(bound.lease_generation)
    call.task_id = str(bound.task_id)
    call.attempt_id = str(bound.attempt_id)
    call.lease_generation = int(bound.lease_generation)
    envelope = gateway.action_envelope(call)
    call.approval_id = gateway.action_gateway.make_approval(
        envelope, context=gateway.context
    ).approval_id


def test_no_process_local_dedupe_symbols() -> None:
    offenders = []
    for path in SOURCE.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Name) and node.id == "_seen_ops":
                offenders.append(f"{path.relative_to(SOURCE)}:{node.lineno}")
            if isinstance(node, ast.Attribute) and node.attr == "_seen_ops":
                offenders.append(f"{path.relative_to(SOURCE)}:{node.lineno}")
    assert offenders == []


def test_only_v17_gateway_calls_adapter_execute() -> None:
    references = []
    for path in SOURCE.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Attribute):
                continue
            if (
                node.attr == "execute"
                and isinstance(node.value, ast.Name)
                and node.value.id == "adapter"
            ):
                references.append((str(path.relative_to(SOURCE)), node.lineno))
    assert references
    assert {path for path, _line in references} == {"tools/v17_gateway.py"}


@pytest.mark.asyncio
async def test_legacy_side_effecting_without_boundary_denied() -> None:
    capability = _capability(lambda args: {"outcome": "succeeded"})
    gateway = _legacy_gateway(capability, None)
    with pytest.raises(
        LegacyToolAuthorizationError, match="^side_effecting_requires_v17_boundary$"
    ):
        await gateway.execute_or_reconcile(_call())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("context", "mission_id", "cancellation", "reason"),
    [
        (None, "mission", 0, "side_effecting_requires_actor_context"),
        (
            ActorContext(actor="worker", project_id="proj_a"),
            None,
            0,
            "side_effecting_requires_fence_binding",
        ),
        (
            ActorContext(actor="worker", project_id="proj_a"),
            "mission",
            None,
            "side_effecting_requires_fence_binding",
        ),
    ],
)
async def test_legacy_missing_trusted_context_or_fence_binding_denied(
    context, mission_id, cancellation, reason
) -> None:
    capability = _capability(lambda args: {"outcome": "succeeded"})
    adapter = LegacyToolCallAdapter(capability)
    registry = AdapterRegistry()
    registry.register(adapter)
    action_gateway = ConsequentialToolGateway(
        registry=registry,
        store=InMemoryEffectStore(),
        fences=StaticFenceProvider(1, 0),
        policy=StaticPolicyProvider({"legacy.send"}, "v17-policy-1"),
    )
    gateway = _legacy_gateway(capability, action_gateway, context=context)
    gateway.mission_id = mission_id
    gateway.cancellation_generation = cancellation
    with pytest.raises(LegacyToolAuthorizationError, match=f"^{reason}$"):
        await gateway.execute_or_reconcile(_call())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_legacy_exactly_once_across_fresh_gateway_instances(factory) -> None:
    calls = {"count": 0}

    def handler(args):
        calls["count"] += 1
        return {"outcome": "succeeded", "external_id": f"synthetic-{calls['count']}"}

    capability = _capability(handler)
    adapter = LegacyToolCallAdapter(capability)
    context = ActorContext(actor="worker", project_id="proj_legacy")
    first = _legacy_gateway(capability, _action_gateway(factory, adapter), context=context)
    call = _call()
    _bind_and_approve(factory, first, call)

    first_receipt = await first.execute_or_reconcile(call.model_copy(deep=True))
    second = _legacy_gateway(capability, _action_gateway(factory, adapter), context=context)
    second.mission_id = first.mission_id
    second.cancellation_generation = first.cancellation_generation
    second.current_lease_generation = first.current_lease_generation
    second_receipt = await second.execute_or_reconcile(call.model_copy(deep=True))

    assert calls["count"] == 1
    assert first_receipt.evidence_refs == second_receipt.evidence_refs
    assert first_receipt.external_id == second_receipt.external_id == "synthetic-1"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_legacy_payload_conflict_and_stale_claims_execute_zero_effects(factory) -> None:
    calls = {"count": 0}

    def handler(args):
        calls["count"] += 1
        return {"outcome": "succeeded", "external_id": "synthetic"}

    capability = _capability(handler)
    adapter = LegacyToolCallAdapter(capability)
    context = ActorContext(actor="worker", project_id="proj_legacy")
    gateway = _legacy_gateway(capability, _action_gateway(factory, adapter), context=context)
    call = _call(operation_id="op_binding")
    _bind_and_approve(factory, gateway, call)

    receipt = await gateway.execute_or_reconcile(call.model_copy(deep=True))
    assert receipt.outcome.value == "succeeded"
    assert calls["count"] == 1

    conflict = call.model_copy(deep=True)
    conflict.normalized_args["body"] = "changed"
    with pytest.raises(EffectConflictError, match="effect_key_binding_mismatch"):
        await gateway.execute_or_reconcile(conflict)
    assert calls["count"] == 1

    stale_lease = call.model_copy(deep=True, update={"operation_id": "op_stale_lease"})
    _bind_and_approve(factory, gateway, stale_lease)
    stale_lease.lease_generation += 1
    gateway.current_lease_generation = stale_lease.lease_generation
    with pytest.raises(StaleLeaseError, match="stale_lease_generation"):
        await gateway.execute_or_reconcile(stale_lease)
    assert calls["count"] == 1

    gateway.current_lease_generation -= 1
    stale_cancel = call.model_copy(deep=True, update={"operation_id": "op_stale_cancel"})
    _bind_and_approve(factory, gateway, stale_cancel)
    gateway.cancellation_generation = int(gateway.cancellation_generation) + 1
    with pytest.raises(CancellationFenceError, match="cancellation_generation_mismatch"):
        await gateway.execute_or_reconcile(stale_cancel)
    assert calls["count"] == 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_direct_v17_legacy_network_operation_retains_network_scope(factory) -> None:
    from swarm.contracts.actions import ActionEnvelope
    from swarm.tools.v17_gateway import ToolAuthorizationError

    calls = []
    capability = CapabilityRegistry()
    capability.register(
        ToolSpec(
            name="legacy.send",
            version="1",
            required_scopes=("legacy.send",),
            side_effecting=True,
            network=True,
            description="Synthetic network-class tool",
        ),
        lambda args: calls.append(args) or {"outcome": "succeeded"},
    )
    adapter = LegacyToolCallAdapter(capability)
    gateway = _action_gateway(factory, adapter)  # Policy grants legacy.send, not network.
    context = ActorContext(actor="worker", project_id="proj_network_bridge")
    envelope = bind_lease(
        factory,
        ActionEnvelope(
            project_id=context.project_id,
            actor=context.actor,
            integration_id="legacy.toolcall",
            integration_version="1",
            operation="legacy.send",
            destination="legacy.send",
            side_effect_class="consequential",
            risk_class="medium",
        ).ensure_hashes(),
    )
    envelope.approval_id = gateway.make_approval(envelope, context=context).approval_id
    with pytest.raises(ToolAuthorizationError, match="denied_scopes.*network"):
        await gateway.execute_envelope(envelope, context=context)
    assert calls == []
    assert adapter.manifest.network_allowed is True

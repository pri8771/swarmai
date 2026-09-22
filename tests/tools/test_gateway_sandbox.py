"""Tool gateway and sandbox tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.integration.db.effect_fixtures import bind_lease
from tests.tools.test_single_consequential_path import engine as engine
from tests.tools.test_single_consequential_path import factory as factory

from swarm.contracts.enums import ActionOutcome
from swarm.contracts.workspace import ToolCall
from swarm.tools.adapter_registry import AdapterRegistry
from swarm.tools.builtins import FakeExternalActionProvider, register_builtin_tools
from swarm.tools.effects import DurableEffectRepository
from swarm.tools.fences import ActorContext, LeaseFenceProvider, StaticPolicyProvider
from swarm.tools.gateway import (
    LegacyToolCallAdapter,
    StaleLeaseError,
    ToolAuthorizationError,
    ToolGateway,
)
from swarm.tools.registry import CapabilityRegistry, hash_operation
from swarm.tools.sandbox_runner import IsolatedCodeRunner, SandboxPolicyError, self_test
from swarm.tools.v17_gateway import (
    ApprovalInvalidError,
    ConsequentialToolGateway,
    PolicyDeniedError,
    ReconciliationRequiredError,
)


@pytest.fixture()
def registry() -> CapabilityRegistry:
    reg = CapabilityRegistry()
    register_builtin_tools(reg)
    return reg


def _call(
    tool_version: str,
    args: dict,
    *,
    lease: int = 1,
    approval_id: str | None = None,
) -> ToolCall:
    dest = args.get("destination", "local")
    return ToolCall(
        operation_id=args.get("operation_id", "op_1"),
        task_id="t1",
        attempt_id="a1",
        tool_version=tool_version,
        normalized_args=args,
        payload_hash=hash_operation(tool_version, args, dest),
        scopes=list(args.get("scopes", [])),
        approval_id=approval_id,
        lease_generation=lease,
    )


def _durable_gateway(registry: CapabilityRegistry, factory) -> ToolGateway:
    adapter = LegacyToolCallAdapter(registry)
    adapters = AdapterRegistry()
    adapters.register(adapter)
    action_gateway = ConsequentialToolGateway(
        registry=adapters,
        store=DurableEffectRepository(factory),
        fences=LeaseFenceProvider(factory),
        policy=StaticPolicyProvider({"artifact.write"}, "v17-policy-1"),
    )
    return ToolGateway(
        registry,
        allowed_scopes={"artifact.write"},
        current_lease_generation=1,
        action_gateway=action_gateway,
        context=ActorContext(actor="worker", project_id="proj_legacy_sandbox"),
        mission_id="unbound-mission",
        cancellation_generation=0,
    )


def _bind_and_approve(factory, gateway: ToolGateway, call: ToolCall, **approval_kwargs) -> None:
    assert gateway.action_gateway is not None and gateway.context is not None
    bound = bind_lease(factory, gateway.action_envelope(call))
    gateway.mission_id = bound.mission_id
    gateway.cancellation_generation = bound.cancellation_generation
    gateway.current_lease_generation = int(bound.lease_generation)
    call.task_id = str(bound.task_id)
    call.attempt_id = str(bound.attempt_id)
    call.lease_generation = int(bound.lease_generation)
    call.approval_id = gateway.action_gateway.make_approval(
        gateway.action_envelope(call), context=gateway.context, **approval_kwargs
    ).approval_id


@pytest.mark.asyncio
async def test_calc_and_workspace(registry: CapabilityRegistry) -> None:
    gw = ToolGateway(
        registry,
        allowed_scopes={"calc", "workspace.read"},
        current_lease_generation=1,
    )
    receipt = await gw.execute_or_reconcile(
        _call("calc.add@1", {"a": 2, "b": 3, "operation_id": "op_calc"})
    )
    assert receipt.outcome == ActionOutcome.SUCCEEDED
    assert receipt.after_observation["sum"] == 5.0


@pytest.mark.asyncio
async def test_unauthorized_network_and_scope(registry: CapabilityRegistry) -> None:
    gw = ToolGateway(registry, allowed_scopes=set(), current_lease_generation=1)
    with pytest.raises(ToolAuthorizationError):
        await gw.execute_or_reconcile(_call("calc.add@1", {"a": 1, "b": 1}))


@pytest.mark.asyncio
@pytest.mark.integration
async def test_approval_required_and_payload_change(
    registry: CapabilityRegistry, factory
) -> None:
    args = {"uri": "memory://x", "destination": "local", "operation_id": "op_pub"}
    registry.handlers["artifact.publish@1"] = lambda _args: {
        "outcome": "succeeded",
        "external_id": "artifact-op_pub",
    }
    gateway = _durable_gateway(registry, factory)
    call = _call("artifact.publish@1", args)
    with pytest.raises(PolicyDeniedError, match="approval_required"):
        await gateway.execute_or_reconcile(call.model_copy(deep=True))

    _bind_and_approve(factory, gateway, call)
    changed = dict(args)
    changed["uri"] = "memory://changed"
    changed_call = call.model_copy(deep=True, update={"normalized_args": changed})
    with pytest.raises(ApprovalInvalidError, match="approval_payload_mismatch"):
        await gateway.execute_or_reconcile(changed_call)

    receipt = await gateway.execute_or_reconcile(call.model_copy(deep=True))
    assert receipt.outcome == ActionOutcome.SUCCEEDED


@pytest.mark.asyncio
@pytest.mark.integration
async def test_expired_and_revoked_approval(registry: CapabilityRegistry, factory) -> None:
    args = {"uri": "memory://x", "destination": "local", "operation_id": "op_rev"}
    revoked_gateway = _durable_gateway(registry, factory)
    revoked_call = _call("artifact.publish@1", args)
    _bind_and_approve(factory, revoked_gateway, revoked_call)
    assert revoked_gateway.action_gateway is not None
    assert revoked_gateway.context is not None
    revoked_gateway.action_gateway.revoke_approval(
        revoked_call.approval_id,
        context=revoked_gateway.context,
        reason="synthetic_revocation",
    )
    with pytest.raises(ApprovalInvalidError, match="approval_expired_or_revoked_or_exhausted"):
        await revoked_gateway.execute_or_reconcile(revoked_call)

    expired_gateway = _durable_gateway(registry, factory)
    expired_call = _call(
        "artifact.publish@1", {**args, "operation_id": "op_expired"}
    )
    _bind_and_approve(factory, expired_gateway, expired_call, expires_in_seconds=-1)
    with pytest.raises(ApprovalInvalidError, match="approval_expired_or_revoked_or_exhausted"):
        await expired_gateway.execute_or_reconcile(expired_call)


@pytest.mark.asyncio
async def test_stale_lease_cannot_act(registry: CapabilityRegistry) -> None:
    gw = ToolGateway(registry, allowed_scopes={"calc"}, current_lease_generation=2)
    with pytest.raises(StaleLeaseError):
        await gw.execute_or_reconcile(_call("calc.add@1", {"a": 1, "b": 1}, lease=1))


@pytest.mark.asyncio
@pytest.mark.integration
async def test_idempotent_action_not_duplicated(registry: CapabilityRegistry, factory) -> None:
    args = {"uri": "memory://x", "destination": "local", "operation_id": "op_once"}
    calls = {"count": 0}

    def publish(payload):
        calls["count"] += 1
        return {"outcome": "succeeded", "external_id": f"artifact-{calls['count']}"}

    registry.handlers["artifact.publish@1"] = publish
    gateway = _durable_gateway(registry, factory)
    call = _call("artifact.publish@1", args)
    _bind_and_approve(factory, gateway, call)
    first = await gateway.execute_or_reconcile(call.model_copy(deep=True))
    second = await gateway.execute_or_reconcile(call.model_copy(deep=True))
    assert calls["count"] == 1
    assert first.operation_id == second.operation_id
    assert first.external_id == second.external_id == "artifact-1"
    assert first.evidence_refs == second.evidence_refs


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unknown_outcome_pauses_and_reconciles(
    registry: CapabilityRegistry, factory
) -> None:
    external = FakeExternalActionProvider()
    external.force_unknown_once.add("idem-1")

    async def publish(args: dict) -> dict:
        return external.execute(idempotency_key=args["operation_id"], payload=args)

    registry.handlers["artifact.publish@1"] = publish
    args = {"uri": "memory://x", "destination": "local", "operation_id": "idem-1"}
    gateway = _durable_gateway(registry, factory)
    call = _call("artifact.publish@1", args)
    _bind_and_approve(factory, gateway, call)
    receipt = await gateway.execute_or_reconcile(call.model_copy(deep=True))
    assert receipt.outcome == ActionOutcome.UNKNOWN
    assert "reconcile" in receipt.reconciliation_steps
    with pytest.raises(ReconciliationRequiredError, match="external_outcome_still_unknown"):
        await gateway.execute_or_reconcile(call.model_copy(deep=True))


def test_sandbox_blocks_traversal_and_symlink(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    outside = tmp_path / "secret.txt"
    outside.write_text("nope")
    runner = IsolatedCodeRunner(work)
    with pytest.raises(SandboxPolicyError):
        runner._assert_path_allowed(work / ".." / "secret.txt")
    link = work / "escape"
    link.symlink_to(outside)
    with pytest.raises(SandboxPolicyError):
        runner._assert_path_allowed(link)


def test_sandbox_timeout(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    (work / "slow.py").write_text("import time\ntime.sleep(5)\n")
    runner = IsolatedCodeRunner(work, timeout_seconds=0.2)
    result = runner.run_python("slow.py")
    assert result.timed_out is True


def test_sandbox_self_test() -> None:
    out = self_test(network="off")
    assert out["ok"] is True
    assert out["network"] == "off"
    assert out["docker_socket_mounted"] is False
    with pytest.raises(SandboxPolicyError):
        self_test(network="on")

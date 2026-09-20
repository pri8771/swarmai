"""Tool gateway and sandbox tests."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from swarm.contracts.common import utc_now
from swarm.contracts.enums import ActionOutcome
from swarm.contracts.workspace import ToolCall
from swarm.tools.builtins import FakeExternalActionProvider, register_builtin_tools
from swarm.tools.gateway import (
    ApprovalInvalidError,
    StaleLeaseError,
    ToolAuthorizationError,
    ToolGateway,
    make_approval,
)
from swarm.tools.registry import CapabilityRegistry, hash_operation
from swarm.tools.sandbox_runner import IsolatedCodeRunner, SandboxPolicyError, self_test


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
async def test_approval_required_and_payload_change(registry: CapabilityRegistry) -> None:
    args = {"uri": "memory://x", "destination": "local", "operation_id": "op_pub"}
    approval = make_approval(tool_version="artifact.publish@1", args=args, destination="local")
    gw = ToolGateway(
        registry,
        allowed_scopes={"artifact.write"},
        current_lease_generation=1,
        approvals={approval.id: approval},
    )
    ok = await gw.execute_or_reconcile(
        _call("artifact.publish@1", args, approval_id=approval.id)
    )
    assert ok.outcome == ActionOutcome.SUCCEEDED

    changed = dict(args)
    changed["uri"] = "memory://changed"
    with pytest.raises(ApprovalInvalidError):
        await gw.execute_or_reconcile(
            _call("artifact.publish@1", changed, approval_id=approval.id, lease=1)
        )


@pytest.mark.asyncio
async def test_expired_and_revoked_approval(registry: CapabilityRegistry) -> None:
    args = {"uri": "memory://x", "destination": "local", "operation_id": "op_rev"}
    approval = make_approval(
        tool_version="artifact.publish@1", args=args, destination="local", revoked=True
    )
    gw = ToolGateway(
        registry,
        allowed_scopes={"artifact.write"},
        current_lease_generation=1,
        approvals={approval.id: approval},
    )
    with pytest.raises(ApprovalInvalidError):
        await gw.execute_or_reconcile(_call("artifact.publish@1", args, approval_id=approval.id))

    expired = make_approval(
        tool_version="artifact.publish@1",
        args=args,
        destination="local",
        expires_in_seconds=-1,
    )
    # Force expiry in the past.
    expired.expires_at = utc_now() - timedelta(seconds=1)
    gw.approvals[expired.id] = expired
    with pytest.raises(ApprovalInvalidError):
        await gw.execute_or_reconcile(_call("artifact.publish@1", args, approval_id=expired.id))


@pytest.mark.asyncio
async def test_stale_lease_cannot_act(registry: CapabilityRegistry) -> None:
    gw = ToolGateway(registry, allowed_scopes={"calc"}, current_lease_generation=2)
    with pytest.raises(StaleLeaseError):
        await gw.execute_or_reconcile(_call("calc.add@1", {"a": 1, "b": 1}, lease=1))


@pytest.mark.asyncio
async def test_idempotent_action_not_duplicated(registry: CapabilityRegistry) -> None:
    args = {"uri": "memory://x", "destination": "local", "operation_id": "op_once"}
    approval = make_approval(tool_version="artifact.publish@1", args=args, destination="local")
    gw = ToolGateway(
        registry,
        allowed_scopes={"artifact.write"},
        current_lease_generation=1,
        approvals={approval.id: approval},
    )
    first = await gw.execute_or_reconcile(
        _call("artifact.publish@1", args, approval_id=approval.id)
    )
    second = await gw.execute_or_reconcile(
        _call("artifact.publish@1", args, approval_id=approval.id)
    )
    assert first.operation_id == second.operation_id
    assert first.after_observation["artifact_id"] == second.after_observation["artifact_id"]


@pytest.mark.asyncio
async def test_unknown_outcome_pauses_and_reconciles(registry: CapabilityRegistry) -> None:
    external = FakeExternalActionProvider()
    external.force_unknown_once.add("idem-1")

    async def publish(args: dict) -> dict:
        return external.execute(idempotency_key=args["operation_id"], payload=args)

    registry.handlers["artifact.publish@1"] = publish
    args = {"uri": "memory://x", "destination": "local", "operation_id": "idem-1"}
    approval = make_approval(tool_version="artifact.publish@1", args=args, destination="local")
    gw = ToolGateway(
        registry,
        allowed_scopes={"artifact.write"},
        current_lease_generation=1,
        approvals={approval.id: approval},
        external=external,
    )
    receipt = await gw.execute_or_reconcile(
        _call("artifact.publish@1", args, approval_id=approval.id)
    )
    assert receipt.outcome == ActionOutcome.UNKNOWN
    assert "reconcile" in receipt.reconciliation_steps
    reconciled = external.execute(idempotency_key="idem-1", payload=args)
    assert reconciled["outcome"] == "succeeded"


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

"""Tool gateway: validate, authorize, execute/reconcile, receipts."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import ActionOutcome
from swarm.contracts.workspace import ActionReceipt, Approval, ToolCall
from swarm.tools.registry import CapabilityRegistry, hash_operation, normalize_args


class ToolAuthorizationError(PermissionError):
    pass


class ApprovalInvalidError(PermissionError):
    pass


class StaleLeaseError(PermissionError):
    pass


class ToolGateway:
    def __init__(
        self,
        registry: CapabilityRegistry,
        *,
        allowed_scopes: set[str],
        current_lease_generation: int,
        approvals: dict[str, Approval] | None = None,
        external: Any | None = None,
    ) -> None:
        self.registry = registry
        self.allowed_scopes = allowed_scopes
        self.current_lease_generation = current_lease_generation
        self.approvals = approvals or {}
        self.external = external
        self.receipts: dict[str, ActionReceipt] = {}
        self._seen_ops: set[str] = set()

    async def validate(self, call: ToolCall) -> ToolCall:
        name, version = call.tool_version.split("@", 1)
        spec = self.registry.get(name, version)
        call.normalized_args = normalize_args(call.normalized_args)
        call.payload_hash = hash_operation(
            call.tool_version,
            call.normalized_args,
            destination=call.normalized_args.get("destination", "local"),
        )
        if spec.network and "network" not in self.allowed_scopes:
            raise ToolAuthorizationError("network tools not permitted")
        return call

    async def authorize(self, call: ToolCall) -> ToolCall:
        if call.lease_generation != self.current_lease_generation:
            raise StaleLeaseError("stale worker lease generation")
        name, version = call.tool_version.split("@", 1)
        spec = self.registry.get(name, version)
        missing = set(spec.required_scopes) - self.allowed_scopes
        if missing:
            raise ToolAuthorizationError(f"missing scopes: {sorted(missing)}")
        if spec.side_effecting:
            if not call.approval_id:
                raise ApprovalInvalidError("side-effecting tool requires approval")
            approval = self.approvals.get(call.approval_id)
            if approval is None:
                raise ApprovalInvalidError("unknown approval")
            now = utc_now()
            if approval.revoked_at is not None or approval.expires_at <= now:
                raise ApprovalInvalidError("approval expired or revoked")
            if approval.payload_hash != call.payload_hash:
                raise ApprovalInvalidError("payload changed since approval")
            if approval.permitted_operation != call.tool_version:
                raise ApprovalInvalidError("approval operation mismatch")
        return call

    async def execute_or_reconcile(self, call: ToolCall) -> ActionReceipt:
        call = await self.validate(call)
        call = await self.authorize(call)
        # Re-check approval hash immediately before side effects.
        if call.approval_id:
            approval = self.approvals[call.approval_id]
            if approval.payload_hash != call.payload_hash:
                raise ApprovalInvalidError("approval invalidated before execution")

        if call.operation_id in self._seen_ops:
            # Idempotent: do not duplicate after timeout/retry.
            return self.receipts[call.operation_id]

        name, version = call.tool_version.split("@", 1)
        handler = self.registry.handler_for(name, version)
        before = {"state": "ready"}
        try:
            result = handler(dict(call.normalized_args))
            if hasattr(result, "__await__"):
                result = await result
            assert isinstance(result, dict)
            if result.get("outcome") == "unknown":
                receipt = ActionReceipt(
                    operation_id=call.operation_id,
                    before_observation=before,
                    after_observation=result,
                    outcome=ActionOutcome.UNKNOWN,
                    reconciliation_steps=["pause", "poll_external", "reconcile"],
                )
            else:
                receipt = ActionReceipt(
                    operation_id=call.operation_id,
                    before_observation=before,
                    after_observation=result,
                    external_id=result.get("external_id"),
                    outcome=ActionOutcome.SUCCEEDED,
                )
        except Exception as exc:  # noqa: BLE001
            receipt = ActionReceipt(
                operation_id=call.operation_id,
                before_observation=before,
                after_observation={"error": str(exc)},
                outcome=ActionOutcome.FAILED,
            )
        self._seen_ops.add(call.operation_id)
        self.receipts[call.operation_id] = receipt
        return receipt

    async def receipt(self, operation_id: str) -> ActionReceipt:
        return self.receipts[operation_id]


def make_approval(
    *,
    tool_version: str,
    args: dict[str, Any],
    destination: str,
    grantor: str = "operator",
    project_id: str = "proj_demo",
    expires_in_seconds: int = 300,
    revoked: bool = False,
) -> Approval:
    payload = hash_operation(tool_version, args, destination)
    now = utc_now()
    return Approval(
        id=new_id("apr_"),
        payload_hash=payload,
        permitted_operation=tool_version,
        destination=destination,
        grantor=grantor,
        project_id=project_id,
        expires_at=now + timedelta(seconds=expires_in_seconds),
        revoked_at=now if revoked else None,
    )

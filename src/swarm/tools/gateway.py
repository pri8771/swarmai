"""Tool gateway: validate, authorize, execute/reconcile, receipts."""

from __future__ import annotations

import asyncio
import inspect
from datetime import timedelta
from typing import Any

from swarm.contracts.actions import ActionEnvelope, ActionReceiptV17, AdapterManifest, OperationDecl
from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import ActionOutcome
from swarm.contracts.workspace import ActionReceipt, Approval, ToolCall
from swarm.tools.fences import ActorContext
from swarm.tools.registry import CapabilityRegistry, hash_operation, normalize_args
from swarm.tools.v17_gateway import ConsequentialToolGateway


class LegacyToolAuthorizationError(PermissionError):
    pass


ToolAuthorizationError = LegacyToolAuthorizationError


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
        action_gateway: ConsequentialToolGateway | None = None,
        context: ActorContext | None = None,
        mission_id: str | None = None,
        cancellation_generation: int | None = None,
    ) -> None:
        self.registry = registry
        self.allowed_scopes = allowed_scopes
        self.current_lease_generation = current_lease_generation
        self.approvals = approvals or {}
        self.external = external
        self.receipts: dict[str, ActionReceipt] = {}
        self.action_gateway = action_gateway
        self.context = context
        self.mission_id = mission_id
        self.cancellation_generation = cancellation_generation

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
            self._require_action_boundary()
        return call

    async def execute_or_reconcile(self, call: ToolCall) -> ActionReceipt:
        call = await self.validate(call)
        call = await self.authorize(call)
        name, version = call.tool_version.split("@", 1)
        if self.registry.get(name, version).side_effecting:
            envelope = self.action_envelope(call)
            assert self.action_gateway is not None and self.context is not None
            current = await self.action_gateway.execute_envelope(envelope, context=self.context)
            # The frozen receipt has three outcomes. Preserve richer V1.7
            # disposition and receipt identity in evidence, never call denial success.
            outcome = (
                ActionOutcome.SUCCEEDED
                if current.outcome == "succeeded"
                else ActionOutcome.UNKNOWN
                if current.outcome == "unknown"
                else ActionOutcome.FAILED
            )
            receipt = ActionReceipt(
                operation_id=call.operation_id,
                before_observation=current.pre_observation,
                after_observation={**current.post_observation, "v17_outcome": current.outcome},
                external_id=current.external_id,
                outcome=outcome,
                reconciliation_steps=["reconcile"] if current.outcome == "unknown" else [],
                evidence_refs=[current.receipt_id],
            )
            self.receipts[call.operation_id] = receipt
            return receipt

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
        self.receipts[call.operation_id] = receipt
        return receipt

    def _require_action_boundary(self) -> None:
        if self.action_gateway is None:
            raise LegacyToolAuthorizationError("side_effecting_requires_v17_boundary")
        if self.context is None:
            raise LegacyToolAuthorizationError("side_effecting_requires_actor_context")
        if (
            not self.mission_id
            or not self.mission_id.strip()
            or self.cancellation_generation is None
        ):
            raise LegacyToolAuthorizationError("side_effecting_requires_fence_binding")

    def action_envelope(self, call: ToolCall) -> ActionEnvelope:
        """Bind the frozen call to explicitly supplied actor and fence claims."""
        self._require_action_boundary()
        assert self.context is not None and self.action_gateway is not None
        name, version = call.tool_version.split("@", 1)
        spec = self.registry.get(name, version)
        key = f"{self.context.project_id}:legacy:{call.operation_id}"
        return ActionEnvelope(
            project_id=self.context.project_id,
            actor=self.context.actor,
            mission_id=self.mission_id,
            task_id=call.task_id,
            attempt_id=call.attempt_id,
            integration_id="legacy.toolcall",
            integration_version="1",
            operation=name,
            destination=name,
            normalized_payload=normalize_args(call.normalized_args),
            requested_scopes=sorted(set(spec.required_scopes) | set(call.scopes)),
            side_effect_class="consequential",
            risk_class="medium",
            effect_key=key,
            idempotency_key=key,
            lease_generation=call.lease_generation,
            cancellation_generation=self.cancellation_generation,
            policy_version=self.action_gateway.policy.current_policy_version(
                project_id=self.context.project_id
            ),
            approval_id=call.approval_id,
            timeout_seconds=call.timeout_seconds,
        ).ensure_hashes()

    async def receipt(self, operation_id: str) -> ActionReceipt:
        return self.receipts[operation_id]


class LegacyToolCallAdapter:
    """Bridge registered legacy handlers into the durable V1.7 action boundary."""

    def __init__(self, registry: CapabilityRegistry) -> None:
        self._handlers = {}
        operations = {}
        for key, spec in registry.tools.items():
            if not spec.side_effecting:
                continue
            if spec.name in operations:
                raise ValueError("legacy_operation_version_ambiguous")
            self._handlers[spec.name] = registry.handlers[key]
            operations[spec.name] = OperationDecl(
                side_effect_class="consequential",
                risk_class="medium",
                scopes=sorted(set(spec.required_scopes) | ({"network"} if spec.network else set())),
                read_data_classes=[],
                write_data_classes=["legacy_effect"],
            )
        self.manifest = AdapterManifest(
            integration_id="legacy.toolcall",
            integration_version="1",
            adapter_class="local_sandbox",
            operations=operations,
            network_allowed=any(
                spec.network and spec.side_effecting for spec in registry.tools.values()
            ),
            side_effect_class="consequential",
            risk_class="medium",
        )

    def normalize(self, request: dict[str, Any]) -> ActionEnvelope:
        return ActionEnvelope.model_validate(request).ensure_hashes()

    def validate(self, envelope: ActionEnvelope) -> None:
        if (envelope.integration_id, envelope.integration_version) != ("legacy.toolcall", "1"):
            raise LegacyToolAuthorizationError("legacy_integration_mismatch")
        if envelope.operation not in self._handlers or envelope.destination != envelope.operation:
            raise LegacyToolAuthorizationError("legacy_operation_not_registered")

    def observe_pre_state(self, envelope: ActionEnvelope) -> dict[str, Any]:
        return {"operation": envelope.operation, "state": "ready"}

    def execute(self, envelope: ActionEnvelope) -> dict[str, Any]:
        result = self._handlers[envelope.operation](dict(envelope.normalized_payload))
        if inspect.isawaitable(result):

            async def complete() -> dict[str, Any]:
                return await result

            return asyncio.run(complete())
        # Missing or invalid outcome remains unknown at the V1.7 gateway.
        return result

    def observe_post_state(
        self, envelope: ActionEnvelope, execution_result: dict[str, Any]
    ) -> dict[str, Any]:
        return execution_result

    def reconcile(
        self, envelope: ActionEnvelope, prior_receipts: list[ActionReceiptV17]
    ) -> dict[str, Any]:
        return {"state": "unknown", "reason": "legacy_effect_requires_independent_readback"}


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

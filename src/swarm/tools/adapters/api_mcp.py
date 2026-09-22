"""API/MCP-style adapter — network-scoped, no filesystem."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from swarm.contracts.actions import ActionEnvelope, ActionReceiptV17, AdapterManifest
from swarm.contracts.common import new_id, utc_now


class ApiMcpAdapter:
    """Simulated MCP/API tool; inject transport for tests."""

    def __init__(
        self,
        manifest: AdapterManifest,
        *,
        transport: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None,
    ) -> None:
        self._transport = transport or self._default_transport
        self._calls: list[dict[str, Any]] = []
        if manifest.adapter_class != "api_mcp":
            raise ValueError("adapter_class_mismatch")
        self.manifest = AdapterManifest.model_validate(manifest.model_dump())

    @staticmethod
    def _default_transport(operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("force_unknown"):
            return {"outcome": "unknown", "external_id": None}
        return {
            "outcome": "succeeded",
            "external_id": new_id("ext_"),
            "echo": payload.get("body"),
            "operation": operation,
        }

    def normalize(self, request: dict[str, Any]) -> ActionEnvelope:
        dest = str(request.get("destination") or "mcp://echo/default")
        operation = str(request.get("operation", "echo"))
        declaration = self.manifest.operations[operation]
        env = ActionEnvelope(
            project_id=str(request["project_id"]),
            actor=str(request.get("actor", "worker")),
            integration_id=self.manifest.integration_id,
            integration_version=self.manifest.integration_version,
            operation=operation,
            destination=dest,
            normalized_payload={
                "body": request.get("body"),
                "force_unknown": bool(request.get("force_unknown", False)),
            },
            requested_scopes=list(declaration.scopes),
            side_effect_class=declaration.side_effect_class,
            risk_class=declaration.risk_class,
            lease_generation=request.get("lease_generation"),
            cancellation_generation=request.get("cancellation_generation"),
            policy_version=str(request.get("policy_version", "v17-policy-1")),
            mission_id=request.get("mission_id"),
            task_id=request.get("task_id"),
            attempt_id=request.get("attempt_id"),
            approval_id=request.get("approval_id"),
        )
        return env.ensure_hashes()

    def validate(self, envelope: ActionEnvelope) -> None:
        if not envelope.destination.startswith("mcp://"):
            raise PermissionError("destination_scheme_denied")
        if ".." in envelope.destination or envelope.destination.startswith("mcp://evil"):
            raise PermissionError("unsafe_redirect_denied")

    def observe_pre_state(self, envelope: ActionEnvelope) -> dict[str, Any]:
        return {"transport": "ready", "at": utc_now().isoformat()}

    def execute(self, envelope: ActionEnvelope) -> dict[str, Any]:
        self._calls.append({"effect_key": envelope.effect_key, "at": utc_now().isoformat()})
        return self._transport(envelope.operation, dict(envelope.normalized_payload))

    def observe_post_state(
        self, envelope: ActionEnvelope, execution_result: dict[str, Any]
    ) -> dict[str, Any]:
        return {"result": execution_result, "call_count": len(self._calls)}

    def reconcile(
        self, envelope: ActionEnvelope, prior_receipts: list[ActionReceiptV17]
    ) -> dict[str, Any]:
        for receipt in reversed(prior_receipts):
            if receipt.effect_key == envelope.effect_key and receipt.outcome == "succeeded":
                return {"state": "succeeded", "external_id": receipt.external_id}
        return {"state": "unknown", "reason": "destination_not_observable"}

    @property
    def call_count(self) -> int:
        return len(self._calls)

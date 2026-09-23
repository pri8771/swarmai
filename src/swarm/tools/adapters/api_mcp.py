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
        *,
        transport: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None,
    ) -> None:
        self._transport = transport or self._default_transport
        self._calls: list[dict[str, Any]] = []
        self.manifest = AdapterManifest(
            integration_id="api.mcp.echo",
            integration_version="1.0",
            adapter_class="api_mcp",
            read_data_classes=["remote_resource"],
            write_data_classes=["remote_resource"],
            scopes=["network.https", "mcp.call"],
            secrets_required=["mcp_token_ref"],
            network_allowed=True,
            filesystem_allowed=False,
            side_effect_class="consequential",
            risk_class="medium",
            sandbox_required=False,
        )

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
        env = ActionEnvelope(
            project_id=str(request["project_id"]),
            actor=str(request.get("actor", "worker")),
            integration_id=self.manifest.integration_id,
            integration_version=self.manifest.integration_version,
            operation=str(request.get("operation", "echo")),
            destination=dest,
            normalized_payload={
                "body": request.get("body"),
                "force_unknown": bool(request.get("force_unknown", False)),
            },
            requested_scopes=list(self.manifest.scopes),
            side_effect_class=self.manifest.side_effect_class,
            risk_class=self.manifest.risk_class,
            lease_generation=int(request.get("lease_generation", 1)),
            cancellation_generation=int(request.get("cancellation_generation", 0)),
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
            if receipt.effect_key == envelope.effect_key and receipt.outcome == "unknown":
                # Still unknown — do not invent success.
                return {"state": "unknown", "reason": "external_outcome_unconfirmed"}
        return {"state": "failed", "reason": "no_prior_success"}

    @property
    def call_count(self) -> int:
        return len(self._calls)

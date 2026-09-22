"""Browser/session-aware adapter — safe aliases only; login ≠ submit."""

from __future__ import annotations

from typing import Any

from swarm.contracts.actions import (
    ActionEnvelope,
    ActionReceiptV17,
    AdapterManifest,
    BrowserSessionRef,
    OperationDecl,
)
from swarm.contracts.common import utc_now


class BrowserSessionAdapter:
    def __init__(self) -> None:
        self.sessions: dict[str, BrowserSessionRef] = {}
        self._submitted: set[str] = set()
        self.manifest = AdapterManifest(
            integration_id="browser.session",
            integration_version="1.0",
            adapter_class="browser_session",
            operations={
                "navigate": OperationDecl(
                    side_effect_class="none",
                    risk_class="low",
                    scopes=["browser.session"],
                    read_data_classes=["page_dom"],
                    write_data_classes=[],
                ),
                "submit": OperationDecl(
                    side_effect_class="consequential",
                    risk_class="high",
                    scopes=["browser.session"],
                    read_data_classes=["page_dom"],
                    write_data_classes=["form_submit"],
                ),
            },
            read_data_classes=["page_dom"],
            write_data_classes=["form_submit"],
            scopes=["browser.session"],
            secrets_required=[],  # cookies/credentials never in Git / never in envelope
            network_allowed=True,
            filesystem_allowed=False,
            side_effect_class="consequential",
            risk_class="high",
            sandbox_required=False,
            user_interaction_consequential=True,
            host_requirements=["browser_runtime"],
        )

    def normalize(self, request: dict[str, Any]) -> ActionEnvelope:
        dest = str(request.get("destination") or request.get("intended_destination") or "")
        operation = str(request.get("operation", "navigate"))
        # Navigation/recovery is non-submitting; submit remains consequential.
        side = "none" if operation == "navigate" else self.manifest.side_effect_class
        risk = "low" if operation == "navigate" else self.manifest.risk_class
        env = ActionEnvelope(
            project_id=str(request["project_id"]),
            actor=str(request.get("actor", "worker")),
            integration_id=self.manifest.integration_id,
            integration_version=self.manifest.integration_version,
            operation=operation,
            destination=dest,
            normalized_payload={
                "session_alias": str(request.get("session_alias", "sess_local")),
                "profile_alias": str(request.get("profile_alias", "profile_safe")),
                "site_origin": str(request.get("site_origin", "https://example.test")),
                "form": dict(request.get("form") or {}),
            },
            requested_scopes=list(self.manifest.scopes),
            side_effect_class=side,
            risk_class=risk,
            lease_generation=request.get("lease_generation"),
            cancellation_generation=request.get("cancellation_generation"),
            policy_version=str(request.get("policy_version", "v17-policy-1")),
            mission_id=request.get("mission_id"),
            task_id=request.get("task_id"),
            attempt_id=request.get("attempt_id"),
            approval_id=request.get("approval_id") if operation != "navigate" else None,
        )
        return env.ensure_hashes()

    def validate(self, envelope: ActionEnvelope) -> None:
        origin = str(envelope.normalized_payload.get("site_origin", ""))
        if not envelope.destination.startswith(origin):
            raise PermissionError("unsafe_redirect_or_destination_mismatch")
        if "javascript:" in envelope.destination.lower():
            raise PermissionError("unsafe_redirect_denied")

    def observe_pre_state(self, envelope: ActionEnvelope) -> dict[str, Any]:
        alias = str(envelope.normalized_payload.get("session_alias"))
        ref = self.sessions.get(alias)
        return {
            "signed_out": True if ref is None else ref.signed_out,
            "session_alias": alias,
            "at": utc_now().isoformat(),
        }

    def execute(self, envelope: ActionEnvelope) -> dict[str, Any]:
        alias = str(envelope.normalized_payload.get("session_alias"))
        ref = self.sessions.get(alias)
        if ref is None or ref.signed_out:
            return {
                "outcome": "denied",
                "reason": "signed_out",
                "requires_human_auth": True,
                "preserve_destination": envelope.destination,
            }
        if envelope.operation == "submit":
            if envelope.effect_key in self._submitted:
                return {
                    "outcome": "succeeded",
                    "duplicate": True,
                    "external_id": envelope.effect_key,
                }
            self._submitted.add(envelope.effect_key)
            return {
                "outcome": "succeeded",
                "submitted": True,
                "external_id": envelope.effect_key,
            }
        if envelope.operation == "navigate":
            return {
                "outcome": "succeeded",
                "navigated_to": envelope.destination,
                "external_id": f"nav:{envelope.destination}",
            }
        return {"outcome": "denied", "reason": f"unknown_operation:{envelope.operation}"}

    def observe_post_state(
        self, envelope: ActionEnvelope, execution_result: dict[str, Any]
    ) -> dict[str, Any]:
        return {"result": execution_result}

    def reconcile(
        self, envelope: ActionEnvelope, prior_receipts: list[ActionReceiptV17]
    ) -> dict[str, Any]:
        if envelope.effect_key in self._submitted:
            return {"state": "succeeded", "external_id": envelope.effect_key}
        return {"state": "unknown", "reason": "browser_outcome_unconfirmed"}

    def register_session(self, ref: BrowserSessionRef) -> BrowserSessionRef:
        self.sessions[ref.session_alias] = ref
        return ref

    def mark_signed_out(self, session_alias: str) -> None:
        ref = self.sessions.get(session_alias)
        if ref is not None:
            self.sessions[session_alias] = ref.model_copy(update={"signed_out": True})

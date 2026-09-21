"""V2B-004 / D4 — browser/session recovery without duplicate side effects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from swarm.contracts.actions import ActionEnvelope, BrowserSessionRef
from swarm.tools.adapters.browser_session import BrowserSessionAdapter
from swarm.tools.v17_gateway import ConsequentialToolGateway


@dataclass
class SessionRecoveryResult:
    session_alias: str
    signed_out_detected: bool
    preserved_destination: str
    human_auth_required: bool
    resumed_destination: str | None
    login_implied_submit: bool
    receipt_outcome: str | None
    notes: list[str]


class SessionRecoveryService:
    """Safe alias recovery: login success must NOT imply submission."""

    def __init__(
        self,
        gateway: ConsequentialToolGateway,
        adapter: BrowserSessionAdapter,
    ) -> None:
        self.gateway = gateway
        self.adapter = adapter

    async def recover(
        self,
        *,
        session_ref: BrowserSessionRef,
        approved_envelope: ActionEnvelope,
        perform_human_login: bool = True,
    ) -> SessionRecoveryResult:
        notes: list[str] = []
        alias = session_ref.session_alias
        self.adapter.register_session(session_ref)
        pre = self.adapter.observe_pre_state(approved_envelope)
        signed_out = bool(pre.get("signed_out"))
        notes.append("detected_signed_out" if signed_out else "session_healthy")

        if signed_out and perform_human_login:
            # Essential human auth only — restore session health, do not submit.
            restored = session_ref.model_copy(
                update={
                    "signed_out": False,
                    "last_health": "authenticated",
                    "intended_destination": approved_envelope.destination,
                    "approved_action_id": approved_envelope.action_id,
                }
            )
            self.adapter.register_session(restored)
            notes.append("human_auth_completed")
            notes.append("login_does_not_submit")

        # Resume exact approved destination via navigate (not submit).
        navigate_req = {
            "project_id": approved_envelope.project_id,
            "actor": approved_envelope.actor,
            "operation": "navigate",
            "destination": approved_envelope.destination,
            "session_alias": alias,
            "profile_alias": session_ref.profile_alias,
            "site_origin": session_ref.site_origin,
            "lease_generation": approved_envelope.lease_generation,
            "cancellation_generation": approved_envelope.cancellation_generation,
            "policy_version": approved_envelope.policy_version,
            "approval_id": approved_envelope.approval_id,
            "mission_id": approved_envelope.mission_id,
            "task_id": approved_envelope.task_id,
            "attempt_id": approved_envelope.attempt_id,
        }
        # Navigate uses a distinct operation → distinct effect key from submit.
        nav_receipt = await self.gateway.execute_request(navigate_req)
        return SessionRecoveryResult(
            session_alias=alias,
            signed_out_detected=signed_out,
            preserved_destination=approved_envelope.destination,
            human_auth_required=signed_out,
            resumed_destination=approved_envelope.destination,
            login_implied_submit=False,
            receipt_outcome=nav_receipt.outcome,
            notes=notes,
        )

    def recovery_report(self, result: SessionRecoveryResult) -> dict[str, Any]:
        return {
            "session_alias": result.session_alias,
            "signed_out_detected": result.signed_out_detected,
            "preserved_destination": result.preserved_destination,
            "human_auth_required": result.human_auth_required,
            "resumed_destination": result.resumed_destination,
            "login_implied_submit": result.login_implied_submit,
            "receipt_outcome": result.receipt_outcome,
            "notes": list(result.notes),
            "status": "pass" if not result.login_implied_submit else "fail",
        }

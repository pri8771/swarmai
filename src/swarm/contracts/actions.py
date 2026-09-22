"""ART-V17 / V2B-004a — ActionEnvelope, ApprovalGrant, ActionReceipt contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from swarm.contracts.common import StrictModel, new_id, payload_hash, utc_now

SideEffectClass = Literal["none", "idempotent", "consequential", "irreversible"]
RiskClass = Literal["low", "medium", "high", "critical"]
EffectState = Literal[
    "reserved",
    "executing",
    "unknown",
    "succeeded",
    "failed",
    "denied",
    "cancelled",
    "reconciled",
]
ActionOutcomeV17 = Literal["succeeded", "failed", "unknown", "denied", "cancelled", "reconciled"]


class ActionEnvelope(StrictModel):
    schema_version: str = "1.0"
    action_id: str = Field(default_factory=lambda: new_id("act_"))
    mission_id: str | None = None
    task_id: str | None = None
    attempt_id: str | None = None
    project_id: str
    actor: str
    integration_id: str
    integration_version: str
    operation: str
    destination: str
    normalized_payload: dict[str, Any] = Field(default_factory=dict)
    payload_hash: str = ""
    requested_scopes: list[str] = Field(default_factory=list)
    side_effect_class: SideEffectClass = "none"
    risk_class: RiskClass = "low"
    effect_key: str = ""
    idempotency_key: str = ""
    lease_generation: int | None = None
    cancellation_generation: int | None = None
    policy_version: str = "v17-policy-1"
    approval_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    timeout_seconds: int = 30

    def ensure_hashes(self) -> ActionEnvelope:
        """Fill payload_hash / effect_key / idempotency_key when empty."""
        data = dict(self.normalized_payload)
        if not self.payload_hash:
            object.__setattr__(
                self,
                "payload_hash",
                payload_hash(
                    {
                        "integration": f"{self.integration_id}@{self.integration_version}",
                        "operation": self.operation,
                        "destination": self.destination,
                        "payload": data,
                    }
                ),
            )
        if not self.effect_key:
            object.__setattr__(
                self,
                "effect_key",
                f"{self.project_id}:{self.integration_id}:{self.operation}:"
                f"{self.destination}:{self.payload_hash}",
            )
        if not self.idempotency_key:
            object.__setattr__(self, "idempotency_key", self.effect_key)
        return self


class ApprovalGrant(StrictModel):
    schema_version: str = "1.0"
    approval_id: str = Field(default_factory=lambda: new_id("apr_"))
    project_id: str
    actor: str | None = None
    grantor: str
    integration_id: str
    integration_version: str
    operation: str
    destination: str
    payload_hash: str
    effect_key: str | None = None
    max_effect_count: int = 1
    used_count: int = 0
    expires_at: datetime
    revoked_at: datetime | None = None
    policy_version: str = "v17-policy-1"
    constraints: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)

    def is_active(self, *, now: datetime | None = None, ignore_usage: bool = False) -> bool:
        clock = now or utc_now()
        if self.revoked_at is not None:
            return False
        if self.expires_at <= clock:
            return False
        if not ignore_usage and self.used_count >= self.max_effect_count:
            return False
        return True


class ActionReceiptV17(StrictModel):
    schema_version: str = "1.0"
    receipt_id: str = Field(default_factory=lambda: new_id("arc_"))
    action_id: str
    effect_key: str
    effect_id: str | None = None
    approval_id: str | None = None
    project_id: str
    integration_id: str
    integration_version: str
    operation: str
    destination: str
    pre_observation: dict[str, Any] = Field(default_factory=dict)
    post_observation: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    external_id: str | None = None
    outcome: ActionOutcomeV17
    # Older persisted receipts predate effective classification; do not invent it.
    effective_side_effect_class: SideEffectClass | None = None
    effective_risk_class: RiskClass | None = None
    reconciliation_state: str = "none"
    attempt_number: int = 0
    attempt_refs: list[str] = Field(default_factory=list)
    evidence_digest: str | None = None
    authorized_artifacts: list[str] = Field(default_factory=list)


class OperationDecl(StrictModel):
    side_effect_class: SideEffectClass
    risk_class: RiskClass
    scopes: list[str]
    read_data_classes: list[str]
    write_data_classes: list[str]


class AdapterManifest(StrictModel):
    schema_version: str = "1.0"
    integration_id: str
    integration_version: str
    adapter_class: Literal["local_sandbox", "api_mcp", "browser_session"]
    operations: dict[str, OperationDecl] = Field(default_factory=dict)
    read_data_classes: list[str] = Field(default_factory=list)
    write_data_classes: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)
    secrets_required: list[str] = Field(default_factory=list)
    network_allowed: bool = False
    filesystem_allowed: bool = False
    filesystem_roots: list[str] = Field(default_factory=list)
    side_effect_class: SideEffectClass = "none"
    risk_class: RiskClass = "low"
    sandbox_required: bool = False
    host_requirements: list[str] = Field(default_factory=list)
    user_interaction_consequential: bool = False


class BrowserSessionRef(StrictModel):
    """Safe browser/session alias only — never cookies/credentials."""

    schema_version: str = "1.0"
    session_alias: str
    profile_alias: str
    site_origin: str
    intended_destination: str
    approved_action_id: str | None = None
    signed_out: bool = False
    last_health: str = "unknown"

"""Provider, route, quota, and inference receipt contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field, field_validator, model_validator

from swarm.contracts.common import Envelope, StrictModel, new_id, utc_now
from swarm.contracts.enums import (
    AccountStatus,
    AvailabilityStatus,
    BillingMode,
    ErrorClass,
    PurposeEligibility,
    QuotaDimension,
    ReservationPhase,
    ReservationState,
    SettlementState,
    WindowType,
)


class ProviderAccount(StrictModel):
    schema_version: str = "1.0"
    id: str = Field(default_factory=lambda: new_id("pa_"))
    service_id: str
    account_alias: str
    secret_ref_names: list[str] = Field(default_factory=list)
    owner: str
    account_status: AccountStatus = AccountStatus.CATALOGED
    purpose_eligibility: PurposeEligibility = PurposeEligibility.UNKNOWN
    billing_mode: BillingMode = BillingMode.UNKNOWN
    billing_group_id: str | None = None
    shared_quota_group_ids: list[str] = Field(default_factory=list)
    charge_prevention_evidence_ref: str | None = None
    verified_at: datetime | None = None
    expires_at: datetime | None = None

    @field_validator("secret_ref_names")
    @classmethod
    def _refs_only(cls, value: list[str]) -> list[str]:
        for name in value:
            if "=" in name or name.startswith("sk-") or len(name) > 128:
                raise ValueError("secret_ref_names must be env/keychain names, never secret values")
        return value


class RouteSnapshot(StrictModel):
    schema_version: str = "1.0"
    route_id: str = Field(default_factory=lambda: new_id("rt_"))
    provider: str
    account_id: str
    model_id: str
    resolved_model_revision: str | None = None
    endpoint: str
    region: str | None = None
    hosted_by: str | None = None
    billing_origin: str
    capability_claims: list[str] = Field(default_factory=list)
    observed_capabilities: list[str] = Field(default_factory=list)
    availability_status: AvailabilityStatus = AvailabilityStatus.UNKNOWN
    quota_bucket_ids: list[str] = Field(default_factory=list)
    privacy_policy_ref: str | None = None
    model_terms_ref: str | None = None
    status: str = "cataloged"
    observed_at: datetime = Field(default_factory=utc_now)


class QuotaBucket(StrictModel):
    schema_version: str = "1.0"
    bucket_id: str = Field(default_factory=lambda: new_id("qb_"))
    scope_type: str
    scope_id: str
    dimension: QuotaDimension
    limit: int | None = None
    remaining: int | None = None
    window_type: WindowType = WindowType.UNKNOWN
    reset_at: datetime | None = None
    reset_timezone: str | None = None
    observed_at: datetime = Field(default_factory=utc_now)
    source: str = "unknown"
    confidence: str = "unknown"
    version: int = 1

    @model_validator(mode="after")
    def _unknown_stays_null(self) -> QuotaBucket:
        # Unknown quota remains null; do not invent zeros.
        return self


class BucketAmount(StrictModel):
    bucket_id: str
    dimension: QuotaDimension
    amount: int


class Reservation(StrictModel):
    schema_version: str = "1.0"
    reservation_id: str = Field(default_factory=lambda: new_id("rsv_"))
    logical_call_id: str
    attempt_id: str
    route_id: str
    bucket_amounts: list[BucketAmount] = Field(default_factory=list)
    state: ReservationState = ReservationState.OPEN
    phase: ReservationPhase = ReservationPhase.RESERVED
    expires_at: datetime
    fence_token: str = Field(default_factory=lambda: new_id("ft_"))


class NormalizedUsage(StrictModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    uncached_tokens: int | None = None
    requests: int = 1
    extras: dict[str, Any] = Field(default_factory=dict)


class AttemptReceipt(StrictModel):
    schema_version: str = "1.0"
    logical_call_id: str
    network_attempt_id: str = Field(default_factory=lambda: new_id("na_"))
    idempotency_key: str | None = None
    provider_request_id: str | None = None
    started_at: datetime = Field(default_factory=utc_now)
    send_phase: ReservationPhase
    finished_at: datetime | None = None
    usage_raw_ref: str | None = None
    normalized_usage: NormalizedUsage | None = None
    pricing_snapshot_ref: str | None = None
    actual_route: str
    error_class: ErrorClass | None = None
    settlement_state: SettlementState = SettlementState.PENDING


class InferenceRequest(Envelope):
    """Broker-facing request; never carries raw secrets."""

    attempt_id: str
    route_id: str | None = None
    purpose: str
    messages: list[dict[str, Any]]
    estimated_input_tokens: int | None = None
    max_output_tokens: int | None = Field(default=None, strict=True, gt=0)
    tools_requested: list[str] = Field(default_factory=list)
    secret_ref_names: list[str] = Field(default_factory=list)

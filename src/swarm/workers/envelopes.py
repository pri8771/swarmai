"""ART-V15-WORKER-PROTOCOL / V2A-004 transport-independent envelopes."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from swarm.contracts.common import StrictModel, new_id, utc_now

PROTOCOL_VERSION = "1.0"
SUPPORTED_PROTOCOL_RANGE = ("1.0", "1.0")


class WorkerSoftwareInfo(StrictModel):
    swarm_version: str = "1.0.0rc1"
    worker_build_sha: str | None = None
    protocol_schema_version: str = PROTOCOL_VERSION


class WorkerResources(StrictModel):
    worker_slots: int = 1
    local_inference_slots: int = 0
    memory_mb: int | None = None
    gpu_classes: list[str] = Field(default_factory=list)
    named_local_routes: list[str] = Field(default_factory=list)


class ArtifactTransportInfo(StrictModel):
    schemes: list[str] = Field(default_factory=lambda: ["control_upload"])
    max_inline_bytes: int = 65536


class EnrollmentRequest(StrictModel):
    protocol_version: str = PROTOCOL_VERSION
    worker_nonce: str = Field(default_factory=lambda: new_id("nonce_"))
    host_alias: str
    project_id: str
    software: WorkerSoftwareInfo = Field(default_factory=WorkerSoftwareInfo)
    scopes_requested: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    trust_class: str = "compute_only"
    resources: WorkerResources = Field(default_factory=WorkerResources)
    artifact_transport: ArtifactTransportInfo = Field(default_factory=ArtifactTransportInfo)
    # Prefer platform.arch when provided; default unknown (no Apple Silicon bias).
    architecture: str = "unknown"
    runtime_version: str = "unknown"
    capacity_units: float = 1.0
    privacy_classes: list[str] = Field(default_factory=lambda: ["local"])
    labels: list[str] = Field(default_factory=list)
    policy_version: str | None = None
    # Portable identity extensions (optional for backward compatibility).
    platform: dict[str, Any] | None = None
    runtimes: list[dict[str, Any]] = Field(default_factory=list)
    resource_limits: dict[str, Any] | None = None
    data_locality: dict[str, Any] | None = None
    workspace_grant_ids: list[str] = Field(default_factory=list)
    # Optional re-enrollment under existing worker_id (generation bump).
    worker_id: str | None = None


class EnrollmentResponse(StrictModel):
    protocol_version: str = PROTOCOL_VERSION
    worker_id: str
    generation: int
    membership_token: str
    token_id: str
    scopes_granted: list[str] = Field(default_factory=list)
    capabilities_granted: list[str] = Field(default_factory=list)
    capabilities_claimed: list[str] = Field(default_factory=list)
    capabilities_verified: bool = False
    trust_class: str
    heartbeat_interval_seconds: int = 30
    lease_defaults: dict[str, int] = Field(
        default_factory=lambda: {
            "duration_seconds": 60,
            "renew_after_seconds": 30,
            "max_total_lease_seconds": 3600,
        }
    )
    server_protocol_version: str = PROTOCOL_VERSION
    policy_version: str | None = None
    project_id: str
    workspace_grant_ids: list[str] = Field(default_factory=list)
    platform: dict[str, Any] | None = None
    data_locality: dict[str, Any] | None = None


class WorkerHeartbeatRequest(StrictModel):
    """Worker-side progress heartbeat (not CURSOR-V17-SINGLE coordination heartbeat)."""

    protocol_version: str = PROTOCOL_VERSION
    worker_id: str
    generation: int
    membership_token: str
    observed_at: datetime = Field(default_factory=utc_now)
    worker_state: str = "active"
    active_lease_ids: list[str] = Field(default_factory=list)
    available: dict[str, Any] = Field(default_factory=dict)
    health: dict[str, Any] = Field(default_factory=dict)
    capability_changes: list[str] = Field(default_factory=list)
    progress_class: str | None = None


class WorkerHeartbeatResponse(StrictModel):
    protocol_version: str = PROTOCOL_VERSION
    worker_id: str
    generation: int
    status: str
    server_received_at: datetime
    active_lease_ids: list[str] = Field(default_factory=list)
    cancel_notices: list[str] = Field(default_factory=list)


class CapabilityAdvertisement(StrictModel):
    protocol_version: str = PROTOCOL_VERSION
    worker_id: str
    generation: int
    membership_token: str
    capabilities: list[str] | None = None
    capacity_units: float | None = None
    privacy_classes: list[str] | None = None


class ClaimDispatchRequest(StrictModel):
    protocol_version: str = PROTOCOL_VERSION
    worker_id: str
    generation: int
    membership_token: str
    agent_profile_id: str = "ap_default"


class ClaimDispatchResponse(StrictModel):
    protocol_version: str = PROTOCOL_VERSION
    claimed: bool
    lease_id: str | None = None
    attempt_id: str | None = None
    task_id: str | None = None
    mission_id: str | None = None
    project_id: str | None = None
    worker_generation: int | None = None
    task_revision: int | None = None
    expires_at: datetime | None = None
    state: str | None = None


class RenewLeaseRequest(StrictModel):
    protocol_version: str = PROTOCOL_VERSION
    lease_id: str
    worker_id: str
    generation: int
    membership_token: str
    progress_class: str = "running"
    extend_seconds: int | None = None


class RenewLeaseResponse(StrictModel):
    protocol_version: str = PROTOCOL_VERSION
    lease_id: str
    state: str
    expires_at: datetime
    renewable_until: datetime | None = None


class ResultSubmitRequest(StrictModel):
    protocol_version: str = PROTOCOL_VERSION
    lease_id: str
    worker_id: str
    generation: int
    membership_token: str
    status: str
    summary: str | None = None
    artifact_manifest: dict[str, Any] = Field(default_factory=dict)
    checks: dict[str, Any] = Field(default_factory=dict)
    usage: dict[str, Any] = Field(default_factory=dict)
    effect_receipts: list[Any] = Field(default_factory=list)
    result_id: str | None = None


class ResultSubmitResponse(StrictModel):
    protocol_version: str = PROTOCOL_VERSION
    result_id: str
    acceptance_state: str
    attempt_id: str
    lease_id: str
    submitted_at: datetime


class DrainRequest(StrictModel):
    protocol_version: str = PROTOCOL_VERSION
    worker_id: str
    generation: int
    membership_token: str


class DrainResponse(StrictModel):
    protocol_version: str = PROTOCOL_VERSION
    worker_id: str
    status: str
    active_lease_ids: list[str] = Field(default_factory=list)
    drain_requested_at: datetime | None = None


class CancelLeaseRequest(StrictModel):
    protocol_version: str = PROTOCOL_VERSION
    lease_id: str
    reason: str = "cancelled"


class CancelLeaseResponse(StrictModel):
    protocol_version: str = PROTOCOL_VERSION
    lease_id: str
    state: str


class ReconnectRequest(StrictModel):
    """Restart/reconnect: reconstruct durable ownership without local process memory."""

    protocol_version: str = PROTOCOL_VERSION
    worker_id: str
    generation: int
    membership_token: str


class ReconnectResponse(StrictModel):
    protocol_version: str = PROTOCOL_VERSION
    worker_id: str
    generation: int
    status: str
    active_leases: list[dict[str, Any]] = Field(default_factory=list)

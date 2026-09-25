"""Evaluation, workspace, worker, tool, and event contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from swarm.contracts.common import Envelope, StrictModel, new_id, utc_now
from swarm.contracts.enums import ActionOutcome, FindingStatus, RoutingState, WorkerStatus
from swarm.contracts.mission import SizeFeatures


class EvalResult(StrictModel):
    schema_version: str = "1.0"
    distinct_case_id: str
    split: str
    route_fingerprint: str
    model_fingerprint: str
    exact_prompt_hash: str
    run_seed: int | None = None
    outcome: str
    grader_version: str
    score_components: dict[str, float] = Field(default_factory=dict)
    correctness: bool | None = None
    policy_violation: bool = False
    latency_ms: int | None = None
    usage: dict[str, Any] = Field(default_factory=dict)
    retry_count: int = 0
    artifact_refs: list[str] = Field(default_factory=list)


class CapabilityProfile(StrictModel):
    schema_version: str = "1.0"
    profile_key: str
    route_fingerprint: str
    task_family: str
    size_features: SizeFeatures
    harness_version: str
    prompt_version: str
    decoding_settings: dict[str, Any] = Field(default_factory=dict)
    tool_protocol: str
    dataset_version: str
    distinct_case_count: int = 0
    repeated_run_count: int = 0
    pass_count: int = 0
    confidence_method: str = "wilson"
    lower_bound: float | None = None
    routing_state: RoutingState = RoutingState.UNASSESSED
    max_supported_features: SizeFeatures | None = None
    recheck_at: datetime | None = None


class Finding(Envelope):
    content: str | None = None
    artifact_ref: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    author: str
    task_id: str
    status: FindingStatus = FindingStatus.HYPOTHESIS
    confidence: float | None = None
    supersedes: str | None = None
    acl: list[str] = Field(default_factory=list)


class ArtifactRef(StrictModel):
    schema_version: str = "1.0"
    id: str = Field(default_factory=lambda: new_id("art_"))
    content_hash: str
    uri: str
    media_type: str
    byte_length: int
    owner_scope: str
    retention_class: str
    created_at: datetime = Field(default_factory=utc_now)


class ContextBundle(StrictModel):
    schema_version: str = "1.0"
    id: str = Field(default_factory=lambda: new_id("ctx_"))
    mission_id: str
    task_id: str
    graph_revision: int
    excerpts: list[dict[str, Any]] = Field(default_factory=list)
    provenance: list[str] = Field(default_factory=list)
    omission_notes: list[str] = Field(default_factory=list)
    token_estimate: int | None = None
    policy_version: str
    created_at: datetime = Field(default_factory=utc_now)


class WorkerLease(StrictModel):
    schema_version: str = "1.0"
    worker_id: str = Field(default_factory=lambda: new_id("wk_"))
    node_identity: str
    architecture: str
    labels: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    runtime_version: str
    capacity_units: float
    lease_generation: int = 1
    heartbeat_at: datetime = Field(default_factory=utc_now)
    status: WorkerStatus = WorkerStatus.ONLINE
    # Portable identity (optional; omitted by older clients).
    platform: dict[str, Any] | None = None
    runtimes: list[dict[str, Any]] = Field(default_factory=list)
    claimed_capabilities: list[str] = Field(default_factory=list)
    capabilities_verified: bool = False
    workspace_grant_ids: list[str] = Field(default_factory=list)
    data_locality: dict[str, Any] | None = None
    resource_limits: dict[str, Any] | None = None


class ToolCall(StrictModel):
    schema_version: str = "1.0"
    operation_id: str = Field(default_factory=lambda: new_id("op_"))
    task_id: str
    attempt_id: str
    tool_version: str
    normalized_args: dict[str, Any] = Field(default_factory=dict)
    payload_hash: str
    scopes: list[str] = Field(default_factory=list)
    approval_id: str | None = None
    lease_generation: int
    timeout_seconds: int = 30
    resource_limits: dict[str, Any] = Field(default_factory=dict)


class Approval(StrictModel):
    schema_version: str = "1.0"
    id: str = Field(default_factory=lambda: new_id("apr_"))
    payload_hash: str
    permitted_operation: str
    destination: str
    grantor: str
    project_id: str
    expires_at: datetime
    revoked_at: datetime | None = None
    constraints: dict[str, Any] = Field(default_factory=dict)


class ActionReceipt(StrictModel):
    schema_version: str = "1.0"
    operation_id: str
    before_observation: dict[str, Any] = Field(default_factory=dict)
    after_observation: dict[str, Any] = Field(default_factory=dict)
    external_id: str | None = None
    outcome: ActionOutcome
    reconciliation_steps: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class EventEnvelope(StrictModel):
    schema_version: str = "1.0"
    id: str = Field(default_factory=lambda: new_id("ev_"))
    occurred_at: datetime = Field(default_factory=utc_now)
    mission_id: str | None = None
    task_id: str | None = None
    attempt_id: str | None = None
    project_id: str
    actor: str
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    causation_id: str | None = None
    correlation_id: str | None = None
    dedupe_key: str | None = None

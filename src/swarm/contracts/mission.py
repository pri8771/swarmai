"""Mission, task, and graph contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from swarm.contracts.common import Envelope, StrictModel, new_id, utc_now
from swarm.contracts.enums import (
    AttemptStatus,
    GraphOperation,
    MissionStatus,
    Modality,
    RiskLevel,
    TaskStatus,
)


class SizeFeatures(StrictModel):
    input_tokens_estimate: int | None = None
    observed_input_tokens: int | None = None
    entity_count: int | None = None
    file_count: int | None = None
    required_output_items: int | None = None
    dependency_depth: int | None = None
    tool_steps_estimate: int | None = None
    modality: Modality = Modality.TEXT
    language: str | None = None
    risk_level: RiskLevel = RiskLevel.MEDIUM
    source_complexity: str | None = None


class Mission(Envelope):
    objective: str
    acceptance_criteria: list[str] = Field(default_factory=list)
    allowed_capabilities: list[str] = Field(default_factory=list)
    data_scope_ids: list[str] = Field(default_factory=list)
    resource_policy_id: str
    max_wall_time_seconds: int
    max_graph_nodes: int
    max_active_sessions: int
    max_model_calls: int
    total_token_envelope: int | None = None
    status: MissionStatus = MissionStatus.DRAFT
    revision: int = 1
    cancellation_generation: int = 0
    acceptance_receipt_id: str | None = None

    @field_validator("max_graph_nodes", "max_active_sessions", "max_model_calls")
    @classmethod
    def _positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("safety envelope bounds must be >= 1")
        return value


class TaskSpec(Envelope):
    mission_id: str
    parent_task_id: str | None = None
    objective: str
    task_family: str
    size_features: SizeFeatures = Field(default_factory=SizeFeatures)
    inputs: dict[str, Any] = Field(default_factory=dict)
    artifact_refs: list[str] = Field(default_factory=list)
    output_schema_id: str
    acceptance_check_ids: list[str] = Field(default_factory=list)
    dependency_ids: list[str] = Field(default_factory=list)
    role_hint: str | None = None
    required_capabilities: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)
    quality_policy_id: str
    priority: int = 100
    deadline: datetime | None = None
    attempt_limit: int = 3
    graph_revision: int = 1
    status: TaskStatus = TaskStatus.PROPOSED


class TaskAttempt(StrictModel):
    schema_version: str = "1.0"
    attempt_id: str = Field(default_factory=lambda: new_id("att_"))
    task_id: str
    agent_profile_id: str
    selected_route_id: str | None = None
    worker_id: str | None = None
    lease_generation: int = 0
    status: AttemptStatus = AttemptStatus.PENDING
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    result_artifact_id: str | None = None
    verification_receipt_id: str | None = None
    blocked_reason: str | None = None


class AgentProfile(StrictModel):
    schema_version: str = "1.0"
    id: str = Field(default_factory=lambda: new_id("ap_"))
    role: str
    instructions_version: str
    tool_scope: list[str] = Field(default_factory=list)
    context_policy: str
    delegation_policy: str
    quality_requirements: list[str] = Field(default_factory=list)


class AgentSession(StrictModel):
    schema_version: str = "1.0"
    id: str = Field(default_factory=lambda: new_id("as_"))
    agent_profile_id: str
    assigned_task_id: str | None = None
    checkpoint_ref: str | None = None
    profile_revision: int = 1
    route_history: list[str] = Field(default_factory=list)
    status: str = "idle"
    created_at: datetime = Field(default_factory=utc_now)


class GraphProposal(Envelope):
    proposal_id: str = Field(default_factory=lambda: new_id("gp_"))
    mission_id: str
    based_on_revision: int
    author_session_id: str
    operation: GraphOperation
    task_specs: list[TaskSpec] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    rationale_summary: str
    projected_resource_envelope: dict[str, Any] = Field(default_factory=dict)

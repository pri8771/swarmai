"""Request/response schemas for the product API."""

from __future__ import annotations

from typing import Any

from pydantic import ConfigDict, Field

from swarm.contracts.common import StrictModel
from swarm.contracts.mission import Mission


class MissionCreateRequest(StrictModel):
    mission: Mission
    task_family: str | None = None
    required_checks: dict[str, Any] | None = None
    idempotency_key: str | None = None


class CancelRequest(StrictModel):
    reason: str | None = None
    idempotency_key: str | None = None


class MissionReviewRequest(StrictModel):
    """Independent review controls acceptance — not decorative post-success notes."""

    produced: dict[str, Any] = Field(default_factory=dict)
    required_checks: dict[str, Any] | None = None
    force_wrong: bool = False
    idempotency_key: str | None = None


class MissionArtifactPublishRequest(StrictModel):
    """Publish a content-addressed artifact into durable managed storage.

    ``str_strip_whitespace`` is disabled so content bytes (and their hashes)
    are not silently altered by the strict product schema defaults.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

    kind: str = "result"
    content_text: str | None = None
    content_base64: str | None = None
    media_type: str = "text/plain"
    owner_scope: str | None = None
    retention_class: str = "mission"
    summary: str | None = None
    expected_hash: str | None = None
    idempotency_key: str | None = None


class WorkerEnrollRequest(StrictModel):
    project_id: str
    capabilities: list[str] = Field(default_factory=lambda: ["chat", "tools"])
    capacity_units: float = 1.0
    privacy_classes: list[str] = Field(default_factory=lambda: ["local"])
    named_inference_urls: list[str] = Field(default_factory=list)
    idempotency_key: str | None = None


class WorkerHeartbeatRequest(StrictModel):
    worker_id: str
    generation: int
    token: str


class WorkerClaimRequest(StrictModel):
    worker_id: str
    generation: int
    token: str
    agent_profile_id: str = "ap_default"


class WorkerRenewRequest(StrictModel):
    lease_id: str
    worker_id: str
    generation: int
    token: str
    progress_class: str = "running"
    extend_seconds: int | None = None


class WorkerSubmitResultRequest(StrictModel):
    lease_id: str
    worker_id: str
    generation: int
    token: str
    status: str = "completed"
    checks: dict[str, Any] = Field(default_factory=dict)
    artifact_manifest: dict[str, Any] = Field(default_factory=dict)
    usage: dict[str, Any] = Field(default_factory=dict)
    summary: str | None = None
    result_id: str | None = None
    idempotency_key: str | None = None


class WorkerCancelLeaseRequest(StrictModel):
    lease_id: str
    reason: str = "cancelled"


class WorkerReconnectRequest(StrictModel):
    worker_id: str
    generation: int
    token: str


class WorkerEnqueueTaskRequest(StrictModel):
    """Control-plane enqueue of a TaskSpec for outbound connector claim."""

    task: dict[str, Any]
    idempotency_key: str | None = None


class ApprovalResolveRequest(StrictModel):
    accept: bool
    payload: dict[str, Any] | None = None
    idempotency_key: str | None = None


class ProbeRequest(StrictModel):
    """Bounded provider probe — requires canary policy admission."""

    purpose: str = "prototype"
    idempotency_key: str | None = None


class EvaluationCreateRequest(StrictModel):
    suite: str = "starter"
    mode: str = "mock"
    max_cases: int = 8
    idempotency_key: str | None = None


class PageMeta(StrictModel):
    limit: int
    cursor: str | None = None
    has_more: bool = False


class ProjectCreateRequest(StrictModel):
    name: str
    repo_path: str
    project_id: str | None = None
    allowed_tools: list[str] | None = None
    provider_policy: dict[str, Any] | None = None
    budgets: dict[str, Any] | None = None
    defaults: dict[str, Any] | None = None
    env_refs: list[str] | None = None
    safety: dict[str, Any] | None = None
    idempotency_key: str | None = None


class ProjectUpdateRequest(StrictModel):
    name: str | None = None
    allowed_tools: list[str] | None = None
    provider_policy: dict[str, Any] | None = None
    budgets: dict[str, Any] | None = None
    defaults: dict[str, Any] | None = None
    safety: dict[str, Any] | None = None
    idempotency_key: str | None = None


class GoalCreateRequest(StrictModel):
    project_id: str
    desired_outcome: str
    verification_criteria: list[str] = Field(default_factory=list)
    kind: str = "finite"  # finite|ongoing
    scope: dict[str, Any] = Field(default_factory=dict)
    constraints: dict[str, Any] = Field(default_factory=dict)
    resource_envelope: dict[str, Any] = Field(default_factory=dict)
    authority_envelope: dict[str, Any] = Field(default_factory=dict)
    owner: str = "operator"
    permitted_agents: list[str] = Field(default_factory=list)
    strategy: str = ""
    stop_conditions: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    review_cadence: str | None = None
    expires_at: str | None = None
    idempotency_key: str | None = None


class GoalTransitionRequest(StrictModel):
    status: str
    reason: str = ""
    idempotency_key: str | None = None


class GoalLifecycleRequest(StrictModel):
    reason: str = ""
    idempotency_key: str | None = None


class GoalLinkMissionRequest(StrictModel):
    mission_id: str
    idempotency_key: str | None = None


class GoalMissionOutcomeRequest(StrictModel):
    mission_id: str
    outcome: str
    notes: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    idempotency_key: str | None = None


class GoalProgressRequest(StrictModel):
    summary: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None


class GoalTriggerRequest(StrictModel):
    dedupe_key: str
    trigger_kind: str = "manual"
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None


class PursuitTickRequest(StrictModel):
    force: bool = False
    idempotency_key: str | None = None


class PursuitLessonProposeRequest(StrictModel):
    summary: str
    scope: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    strategy_delta: str = ""
    idempotency_key: str | None = None


class PursuitLessonEvaluateRequest(StrictModel):
    holdout_check_id: str
    holdout_passed: bool
    idempotency_key: str | None = None

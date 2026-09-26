"""SQLAlchemy ORM models for Swarm domain persistence."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class MissionRow(Base):
    __tablename__ = "missions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    schema_version: Mapped[str] = mapped_column(String(16), default="1.0")
    objective: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), index=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    cancellation_generation: Mapped[int] = mapped_column(Integer, default=0)
    resource_policy_id: Mapped[str] = mapped_column(String(64))
    max_wall_time_seconds: Mapped[int] = mapped_column(Integer)
    max_graph_nodes: Mapped[int] = mapped_column(Integer)
    max_active_sessions: Mapped[int] = mapped_column(Integer)
    max_model_calls: Mapped[int] = mapped_column(Integer)
    total_token_envelope: Mapped[int | None] = mapped_column(Integer, nullable=True)
    acceptance_receipt_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class GraphRevisionRow(Base):
    __tablename__ = "graph_revisions"
    __table_args__ = (UniqueConstraint("mission_id", "revision", name="uq_graph_mission_revision"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    mission_id: Mapped[str] = mapped_column(ForeignKey("missions.id"), index=True)
    revision: Mapped[int] = mapped_column(Integer)
    based_on_revision: Mapped[int] = mapped_column(Integer)
    author_session_id: Mapped[str] = mapped_column(String(64))
    operation: Mapped[str] = mapped_column(String(32))
    rationale_summary: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TaskRow(Base):
    __tablename__ = "tasks"
    __table_args__ = (Index("ix_tasks_mission_status", "mission_id", "status"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    mission_id: Mapped[str] = mapped_column(ForeignKey("missions.id"), index=True)
    parent_task_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    objective: Mapped[str] = mapped_column(Text)
    task_family: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    graph_revision: Mapped[int] = mapped_column(Integer, default=1)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    scopes: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    dependency_ids: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TaskAttemptRow(Base):
    __tablename__ = "task_attempts"
    __table_args__ = (
        Index("ix_task_attempts_project_status", "project_id", "status"),
        Index("ix_task_attempts_mission_id", "mission_id"),
    )

    attempt_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    # V2A-003a / ART-V15 durable fencing fields (nullable for legacy rows).
    project_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    mission_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("missions.id"), nullable=True
    )
    agent_profile_id: Mapped[str] = mapped_column(String(64))
    selected_route_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    worker_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lease_generation: Mapped[int] = mapped_column(Integer, default=0)
    task_revision: Mapped[int] = mapped_column(Integer, default=1)
    input_digest: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_revision: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cancellation_generation: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    terminal_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result_artifact_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    verification_receipt_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    accepted_result_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    blocked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class FindingRow(Base):
    __tablename__ = "findings"
    __table_args__ = (Index("ix_findings_project_task", "project_id", "task_id"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    task_id: Mapped[str] = mapped_column(String(64), index=True)
    mission_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    author: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), index=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    artifact_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    acl: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    scopes: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ArtifactMetaRow(Base):
    __tablename__ = "artifact_metadata"
    __table_args__ = (
        UniqueConstraint("content_hash", "owner_scope", name="uq_artifact_hash_scope"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    content_hash: Mapped[str] = mapped_column(String(128), index=True)
    uri: Mapped[str] = mapped_column(Text)
    media_type: Mapped[str] = mapped_column(String(128))
    byte_length: Mapped[int] = mapped_column(BigInteger)
    owner_scope: Mapped[str] = mapped_column(String(64), index=True)
    retention_class: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProviderAccountRow(Base):
    __tablename__ = "provider_accounts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    service_id: Mapped[str] = mapped_column(String(64), index=True)
    account_alias: Mapped[str] = mapped_column(String(128))
    owner: Mapped[str] = mapped_column(String(64))
    account_status: Mapped[str] = mapped_column(String(32))
    purpose_eligibility: Mapped[str] = mapped_column(String(32))
    billing_mode: Mapped[str] = mapped_column(String(32))
    secret_ref_names: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RouteSnapshotRow(Base):
    __tablename__ = "route_snapshots"

    route_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    model_id: Mapped[str] = mapped_column(String(128))
    endpoint: Mapped[str] = mapped_column(Text)
    billing_origin: Mapped[str] = mapped_column(String(64))
    availability_status: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class QuotaBucketRow(Base):
    __tablename__ = "quota_buckets"

    bucket_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scope_type: Mapped[str] = mapped_column(String(32))
    scope_id: Mapped[str] = mapped_column(String(64), index=True)
    dimension: Mapped[str] = mapped_column(String(32))
    limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    remaining: Mapped[int | None] = mapped_column(Integer, nullable=True)
    window_type: Mapped[str] = mapped_column(String(32))
    version: Mapped[int] = mapped_column(Integer, default=1)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ReservationRow(Base):
    __tablename__ = "reservations"
    __table_args__ = (UniqueConstraint("logical_call_id", name="uq_reservation_logical_call"),)

    reservation_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    logical_call_id: Mapped[str] = mapped_column(String(64))
    attempt_id: Mapped[str] = mapped_column(String(64), index=True)
    route_id: Mapped[str] = mapped_column(String(64), index=True)
    state: Mapped[str] = mapped_column(String(32))
    phase: Mapped[str] = mapped_column(String(32))
    fence_token: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class AttemptReceiptRow(Base):
    __tablename__ = "attempt_receipts"
    __table_args__ = (
        UniqueConstraint("logical_call_id", "network_attempt_id", name="uq_receipt_call_attempt"),
        UniqueConstraint("idempotency_key", name="uq_receipt_idempotency"),
    )

    network_attempt_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    logical_call_id: Mapped[str] = mapped_column(String(64), index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    provider_request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    actual_route: Mapped[str] = mapped_column(String(64))
    send_phase: Mapped[str] = mapped_column(String(32))
    settlement_state: Mapped[str] = mapped_column(String(32), index=True)
    error_class: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class CapabilityProfileRow(Base):
    __tablename__ = "capability_profiles"
    __table_args__ = (UniqueConstraint("profile_key", name="uq_capability_profile_key"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    profile_key: Mapped[str] = mapped_column(String(512))
    route_fingerprint: Mapped[str] = mapped_column(String(128), index=True)
    task_family: Mapped[str] = mapped_column(String(64), index=True)
    routing_state: Mapped[str] = mapped_column(String(32))
    distinct_case_count: Mapped[int] = mapped_column(Integer, default=0)
    pass_count: Mapped[int] = mapped_column(Integer, default=0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class ApprovalRow(Base):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload_hash: Mapped[str] = mapped_column(String(128), index=True)
    permitted_operation: Mapped[str] = mapped_column(String(64))
    destination: Mapped[str] = mapped_column(String(256))
    grantor: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    # V2B-004a / ART-V17-DURABLE-EFFECT-SCHEMA extensions (nullable for legacy).
    project_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    actor: Mapped[str | None] = mapped_column(String(64), nullable=True)
    integration_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    integration_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    operation: Mapped[str | None] = mapped_column(String(64), nullable=True)
    effect_key: Mapped[str | None] = mapped_column(String(192), nullable=True, index=True)
    max_effect_count: Mapped[int] = mapped_column(Integer, default=1)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    policy_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, server_default=func.now()
    )
    constraints: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class ActionEffectRow(Base):
    """Durable consequential effect reservation / reconciliation row."""

    __tablename__ = "action_effects"
    __table_args__ = (
        UniqueConstraint("project_id", "effect_key", name="uq_action_effect_project_key"),
        Index("ix_action_effects_project_state", "project_id", "state"),
    )

    effect_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    effect_key: Mapped[str] = mapped_column(String(192), index=True)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    mission_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    task_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    attempt_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    action_id: Mapped[str] = mapped_column(String(64), index=True)
    approval_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    integration_id: Mapped[str] = mapped_column(String(64))
    integration_version: Mapped[str] = mapped_column(String(32))
    operation: Mapped[str] = mapped_column(String(64))
    destination_digest: Mapped[str] = mapped_column(String(128))
    payload_hash: Mapped[str] = mapped_column(String(128))
    state: Mapped[str] = mapped_column(String(32), index=True, default="reserved")
    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lease_generation: Mapped[int] = mapped_column(Integer, default=1)
    cancellation_generation: Mapped[int] = mapped_column(Integer, default=0)
    pre_observation: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    post_observation: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    reconciliation: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    # R27a bookkeeping (used by R27b/R27c/R27e): why a terminal state was reached,
    # how many execution attempts were admitted, who admitted the current one, and
    # when the bound approval was consumed for this effect.
    state_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    executor_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    approval_consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class ActionReceiptRow(Base):
    """Immutable per-attempt action receipt (R27a). Insert-only; never updated."""

    __tablename__ = "action_receipts"
    __table_args__ = (
        UniqueConstraint("effect_id", "attempt_number", name="uq_action_receipt_effect_attempt"),
        Index("ix_action_receipts_project_effect_key", "project_id", "effect_key"),
    )

    receipt_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    effect_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("action_effects.effect_id", name="fk_action_receipt_effect")
    )
    effect_key: Mapped[str] = mapped_column(String(192))
    action_id: Mapped[str] = mapped_column(String(64), index=True)
    attempt_number: Mapped[int] = mapped_column(Integer)
    outcome: Mapped[str] = mapped_column(String(32))
    reconciliation_state: Mapped[str] = mapped_column(
        String(32), default="none", server_default="none"
    )
    evidence_digest: Mapped[str] = mapped_column(String(128))
    receipt: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WorkerLeaseRow(Base):
    """Durable worker registration / generation row (not a per-task lease).

    Per ART-V15-DURABLE-SCHEMA-DELTA: this table remains worker-state identity.
    Per-task leases live in TaskLeaseRow / ``task_leases``.
    Membership credentials are stored as token_hash + token_id only (V2A-H2).
    """

    __tablename__ = "worker_leases"
    __table_args__ = (Index("ix_worker_leases_project_status", "project_id", "status"),)

    worker_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    node_identity: Mapped[str] = mapped_column(String(128), index=True)
    architecture: Mapped[str] = mapped_column(String(32))
    runtime_version: Mapped[str] = mapped_column(String(32))
    capacity_units: Mapped[float] = mapped_column(Float)
    lease_generation: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), index=True)
    heartbeat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    labels: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    capabilities: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    # V2A-003a / V2A-H2 extensions
    project_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    trust_class: Mapped[str | None] = mapped_column(String(32), nullable=True)
    token_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    token_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    registered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, server_default=func.now(), onupdate=func.now()
    )
    drain_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    policy_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    software_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    build_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    privacy_classes: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    resource_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class TaskLeaseRow(Base):
    """Per-attempt task lease — authoritative fencing row for claim/renew/expire."""

    __tablename__ = "task_leases"
    __table_args__ = (Index("ix_task_leases_project_state", "project_id", "state"),)

    lease_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    attempt_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("task_attempts.attempt_id"), index=True
    )
    task_id: Mapped[str] = mapped_column(String(64), ForeignKey("tasks.id"), index=True)
    mission_id: Mapped[str] = mapped_column(String(64), ForeignKey("missions.id"), index=True)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    worker_id: Mapped[str] = mapped_column(String(64), index=True)
    worker_generation: Mapped[int] = mapped_column(Integer)
    task_revision: Mapped[int] = mapped_column(Integer, default=1)
    input_digest: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_revision: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cancellation_generation: Mapped[int] = mapped_column(Integer, default=0)
    state: Mapped[str] = mapped_column(String(32), index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    renewable_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reservation_refs: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    effect_scope: Mapped[str | None] = mapped_column(String(64), nullable=True)
    policy_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class WorkerResultRow(Base):
    """Durable worker result submission — immutable except acceptance disposition."""

    __tablename__ = "worker_results"
    __table_args__ = (
        Index("ix_worker_results_project_acceptance", "project_id", "acceptance_state"),
    )

    result_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    attempt_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("task_attempts.attempt_id"), index=True
    )
    lease_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("task_leases.lease_id"), index=True
    )
    task_id: Mapped[str] = mapped_column(String(64), index=True)
    mission_id: Mapped[str] = mapped_column(String(64), index=True)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    worker_id: Mapped[str] = mapped_column(String(64), index=True)
    worker_generation: Mapped[int] = mapped_column(Integer)
    task_revision: Mapped[int] = mapped_column(Integer, default=1)
    input_digest: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_revision: Mapped[str | None] = mapped_column(String(128), nullable=True)
    result_status: Mapped[str] = mapped_column(String(32))
    artifact_manifest: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    checks: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    usage: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    effect_receipts: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    acceptance_state: Mapped[str] = mapped_column(String(32), index=True, default="submitted")
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EventRow(Base):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("dedupe_key", name="uq_event_dedupe"),
        Index("ix_events_project_occurred", "project_id", "occurred_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64))
    type: Mapped[str] = mapped_column(String(64), index=True)
    actor: Mapped[str] = mapped_column(String(64))
    mission_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    task_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    attempt_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    causation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dedupe_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class OutboxRow(Base):
    """Transactional outbox bridging domain commits to DBOS enqueue."""

    __tablename__ = "outbox"
    __table_args__ = (
        UniqueConstraint("stable_workflow_id", name="uq_outbox_workflow_id"),
        Index("ix_outbox_status_created", "status", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    stable_workflow_id: Mapped[str] = mapped_column(String(128))
    aggregate_type: Mapped[str] = mapped_column(String(64))
    aggregate_id: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class KnowledgeItemRow(Base):
    """V1.6 / ART-V16 versioned reusable knowledge item (not FindingRow)."""

    __tablename__ = "knowledge_items"
    __table_args__ = (
        UniqueConstraint("item_id", "version", name="uq_knowledge_item_version"),
        Index("ix_knowledge_items_project_class_state", "project_id", "class", "acceptance_state"),
        Index("ix_knowledge_items_project_item", "project_id", "item_id"),
    )

    row_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    item_id: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[int] = mapped_column(Integer)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    mission_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    class_: Mapped[str] = mapped_column("class", String(32), index=True)
    topic: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    acceptance_state: Mapped[str] = mapped_column(String(32), index=True, default="unreviewed")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    producer_type: Mapped[str] = mapped_column(String(32), default="system")
    producer_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    permission_labels: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    retrieval_labels: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    source_digests: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    provenance_refs: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    content_digest: Mapped[str] = mapped_column(String(128))
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class KnowledgeLinkRow(Base):
    """Project-scoped knowledge relation (cross-project links forbidden)."""

    __tablename__ = "knowledge_links"
    __table_args__ = (
        Index("ix_knowledge_links_project_from", "project_id", "from_item_id"),
        Index("ix_knowledge_links_project_to", "project_id", "to_item_id"),
    )

    link_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    from_item_id: Mapped[str] = mapped_column(String(64), index=True)
    from_version: Mapped[int] = mapped_column(Integer)
    relation: Mapped[str] = mapped_column(String(32), index=True)
    to_item_id: Mapped[str] = mapped_column(String(64), index=True)
    to_version: Mapped[int] = mapped_column(Integer)
    evidence_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class KnowledgeTombstoneRow(Base):
    """Deletion tombstone so caches/index rebuilds cannot resurrect content."""

    __tablename__ = "knowledge_tombstones"
    __table_args__ = (
        UniqueConstraint("project_id", "item_id", "deleted_version", name="uq_knowledge_tombstone"),
        Index("ix_knowledge_tombstones_project_item", "project_id", "item_id"),
    )

    tombstone_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    item_id: Mapped[str] = mapped_column(String(64), index=True)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    deleted_version: Mapped[int] = mapped_column(Integer)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reason_class: Mapped[str] = mapped_column(String(64))
    replacement_item_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    replacement_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class SiteAuthorityRow(Base):
    """V1.8 site authority / epoch — only one active epoch authorizes work."""

    __tablename__ = "site_authority"
    __table_args__ = (UniqueConstraint("site_id", "epoch", name="uq_site_authority_epoch"),)

    authority_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    site_id: Mapped[str] = mapped_column(String(64), index=True)
    epoch: Mapped[int] = mapped_column(Integer, index=True)
    state: Mapped[str] = mapped_column(String(32), index=True, default="active")
    activated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fenced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_site_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    recovery_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    policy_version: Mapped[str] = mapped_column(String(64), default="v18")
    content_digest: Mapped[str] = mapped_column(String(128), default="")
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class AuthorityTransitionReceiptRow(Base):
    __tablename__ = "authority_transition_receipts"

    receipt_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    site_id: Mapped[str] = mapped_column(String(64), index=True)
    from_epoch: Mapped[int] = mapped_column(Integer)
    to_epoch: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class BackupManifestRow(Base):
    __tablename__ = "backup_manifests"

    backup_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_site_id: Mapped[str] = mapped_column(String(64), index=True)
    source_epoch: Mapped[int] = mapped_column(Integer)
    source_commit_sha: Mapped[str] = mapped_column(String(64))
    schema_revision: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    integrity_digest: Mapped[str] = mapped_column(String(128))
    secret_refs: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class RecoveryRunRow(Base):
    __tablename__ = "recovery_runs"

    recovery_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    backup_id: Mapped[str] = mapped_column(String(64), index=True)
    old_site_id: Mapped[str] = mapped_column(String(64))
    old_epoch: Mapped[int] = mapped_column(Integer)
    new_site_id: Mapped[str] = mapped_column(String(64))
    new_epoch: Mapped[int] = mapped_column(Integer)
    final_state: Mapped[str] = mapped_column(String(32), default="pending")
    evidence_digest: Mapped[str] = mapped_column(String(128), default="")
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExtensionManifestRow(Base):
    __tablename__ = "extension_manifests"
    __table_args__ = (
        UniqueConstraint("extension_id", "version", name="uq_extension_id_version"),
    )

    manifest_pk: Mapped[str] = mapped_column(String(64), primary_key=True)
    extension_id: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[str] = mapped_column(String(32))
    content_digest: Mapped[str] = mapped_column(String(128))
    risk_class: Mapped[str] = mapped_column(String(32), default="low")
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class ProjectExtensionGrantRow(Base):
    __tablename__ = "project_extension_grants"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "extension_id", "version", name="uq_project_extension_grant"
        ),
    )

    grant_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    extension_id: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[str] = mapped_column(String(32))
    enabled: Mapped[str] = mapped_column(String(16), default="true")
    state: Mapped[str] = mapped_column(String(32), default="enabled")
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class ProductCandidateRow(Base):
    __tablename__ = "product_candidates"

    candidate_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_sha: Mapped[str] = mapped_column(String(64), index=True)
    schema_revision: Mapped[str] = mapped_column(String(64))
    dependency_lock_digest: Mapped[str] = mapped_column(String(128))
    frozen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class SchedulerPolicyRow(Base):
    __tablename__ = "scheduler_policies"

    policy_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    version: Mapped[str] = mapped_column(String(32))
    digest: Mapped[str] = mapped_column(String(128))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class ProjectSchedulingStateRow(Base):
    __tablename__ = "project_scheduling_state"

    project_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    fairness_debt: Mapped[float] = mapped_column(Float, default=0.0)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    site_epoch: Mapped[int] = mapped_column(Integer, default=0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class ResourceReservationIntentRow(Base):
    __tablename__ = "resource_reservation_intents"
    __table_args__ = (
        UniqueConstraint("attempt_id", name="uq_reservation_attempt"),
    )

    intent_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    mission_id: Mapped[str] = mapped_column(String(64), index=True)
    attempt_id: Mapped[str] = mapped_column(String(64), index=True)
    site_epoch: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(32), default="reserved")
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class CapabilityPackRow(Base):
    __tablename__ = "capability_packs"
    __table_args__ = (
        UniqueConstraint("pack_id", "version", name="uq_capability_pack_version"),
    )

    pack_pk: Mapped[str] = mapped_column(String(64), primary_key=True)
    pack_id: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[str] = mapped_column(String(32))
    content_digest: Mapped[str] = mapped_column(String(128))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class ObjectiveRow(Base):
    __tablename__ = "objectives"

    objective_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    state: Mapped[str] = mapped_column(String(32), default="active")
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class ObjectiveVersionRow(Base):
    __tablename__ = "objective_versions"
    __table_args__ = (
        UniqueConstraint("objective_id", "version", name="uq_objective_version"),
    )

    version_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    objective_id: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[int] = mapped_column(Integer)
    goal: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TriggerReceiptRow(Base):
    __tablename__ = "trigger_receipts"
    __table_args__ = (
        UniqueConstraint("objective_id", "dedupe_key", name="uq_trigger_dedupe"),
    )

    receipt_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    objective_id: Mapped[str] = mapped_column(String(64), index=True)
    dedupe_key: Mapped[str] = mapped_column(String(192))
    trigger_kind: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class MissionProposalRow(Base):
    __tablename__ = "mission_proposals"

    proposal_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    objective_id: Mapped[str] = mapped_column(String(64), index=True)
    objective_version: Mapped[int] = mapped_column(Integer)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    state: Mapped[str] = mapped_column(String(32), default="proposed")
    mission_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class LearningProposalRow(Base):
    __tablename__ = "learning_proposals"

    proposal_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    state: Mapped[str] = mapped_column(String(32), default="proposed")
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


# --- V2 pursuit / goal durable authority (PC-02 / R20-04) ---


class GoalRow(Base):
    """Authoritative goal record for operational PostgreSQL path."""

    __tablename__ = "goals"
    __table_args__ = (Index("ix_goals_project_status", "project_id", "status"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    kind: Mapped[str] = mapped_column(String(16), default="finite")
    revision: Mapped[int] = mapped_column(Integer, default=1)
    # synthetic | verified | None — never silently promote synthetic to verified
    achievement_authority: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class GoalCriterionVerdictRow(Base):
    __tablename__ = "goal_criterion_verdicts"
    __table_args__ = (
        UniqueConstraint("goal_id", "criterion_key", "goal_revision", name="uq_goal_criterion_rev"),
    )

    verdict_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    goal_id: Mapped[str] = mapped_column(ForeignKey("goals.id"), index=True)
    criterion_key: Mapped[str] = mapped_column(String(256))
    goal_revision: Mapped[int] = mapped_column(Integer, default=1)
    state: Mapped[str] = mapped_column(String(32), default="met")  # met|unmet|invalidated
    authority: Mapped[str] = mapped_column(String(32), default="synthetic")  # synthetic|verified
    evidence_digest: Mapped[str | None] = mapped_column(String(128), nullable=True)
    verifier_receipt_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PursuitCycleRow(Base):
    __tablename__ = "pursuit_cycles"
    __table_args__ = (Index("ix_pursuit_cycles_goal_at", "goal_id", "created_at"),)

    cycle_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    goal_id: Mapped[str] = mapped_column(String(64), index=True)
    phase: Mapped[str] = mapped_column(String(32))
    decided_kind: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PursuitScheduleRow(Base):
    __tablename__ = "pursuit_schedules"

    goal_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    next_due_at: Mapped[float] = mapped_column(Float)
    backoff_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    consecutive_no_progress: Mapped[int] = mapped_column(Integer, default=0)
    last_cycle_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    wait_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PursuitDedupeRow(Base):
    __tablename__ = "pursuit_dedupe"
    __table_args__ = (UniqueConstraint("dedupe_key", name="uq_pursuit_dedupe_key"),)

    dedupe_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    goal_id: Mapped[str] = mapped_column(String(64), index=True)
    dedupe_key: Mapped[str] = mapped_column(String(64))
    proposal_id: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())





# --- V2.3 operations platform (ART-V23) + V2.0 durable holds/lessons -----------
# Row shape rule: key/index columns + ``version`` + full model JSON in ``payload``.
# Repositories read ``payload`` back with ``Model.model_validate(row.payload)``.


class V23ProjectQueueStateRow(Base):
    __tablename__ = "v23_project_queue_state"

    project_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class V23MissionQueueStateRow(Base):
    __tablename__ = "v23_mission_queue_state"

    mission_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    lifecycle: Mapped[str] = mapped_column(String(32), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class V23SchedulerReceiptRow(Base):
    __tablename__ = "v23_scheduler_receipts"
    __table_args__ = (UniqueConstraint("sequence", name="uq_v23_scheduler_receipts_sequence"),)

    receipt_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    sequence: Mapped[int] = mapped_column(BigInteger)
    project_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    decision: Mapped[str] = mapped_column(String(16))
    reason_code: Mapped[str] = mapped_column(String(48))
    digest: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class V23DispatchIntentRow(Base):
    __tablename__ = "v23_dispatch_intents"
    __table_args__ = (UniqueConstraint("attempt_id", name="uq_v23_dispatch_intents_attempt"),)

    intent_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    attempt_id: Mapped[str] = mapped_column(String(64))
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    state: Mapped[str] = mapped_column(String(32), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class V23SchedulerEpochRow(Base):
    __tablename__ = "v23_scheduler_epochs"

    site_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    epoch: Mapped[int] = mapped_column(BigInteger, default=0)
    holder_id: Mapped[str] = mapped_column(String(128))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class V23PackInstallRow(Base):
    __tablename__ = "v23_pack_installs"
    __table_args__ = (
        UniqueConstraint("pack_id", "pack_version", "project_id", name="uq_v23_pack_installs"),
    )

    install_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    pack_id: Mapped[str] = mapped_column(String(128), index=True)
    pack_version: Mapped[str] = mapped_column(String(64))
    project_id: Mapped[str] = mapped_column(String(64))  # "*" = install-level record
    state: Mapped[str] = mapped_column(String(32))
    version: Mapped[int] = mapped_column(Integer, default=1)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class V23OpsEventRow(Base):
    __tablename__ = "v23_ops_events"
    __table_args__ = (Index("ix_v23_ops_events_project_at", "project_id", "at"),)

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kind: Mapped[str] = mapped_column(String(64), index=True)
    component: Mapped[str] = mapped_column(String(64))
    project_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tenant_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    site_epoch: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class V20GoalUsageHoldRow(Base):
    __tablename__ = "v20_goal_usage_holds"

    hold_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    goal_id: Mapped[str] = mapped_column(String(64), index=True)
    mission_id: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(16), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class V20PursuitLessonRow(Base):
    __tablename__ = "v20_pursuit_lessons"

    lesson_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    goal_id: Mapped[str] = mapped_column(String(64), index=True)
    state: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

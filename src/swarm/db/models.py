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

    attempt_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    agent_profile_id: Mapped[str] = mapped_column(String(64))
    selected_route_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    worker_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lease_generation: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result_artifact_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    verification_receipt_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
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


class WorkerLeaseRow(Base):
    __tablename__ = "worker_leases"

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

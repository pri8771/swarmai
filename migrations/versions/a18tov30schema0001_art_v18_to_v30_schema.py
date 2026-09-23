"""Alembic migration: V1.8–V3.0 durable schema group."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a18tov30schema0001"
down_revision: str | Sequence[str] | None = "a17effect004b0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "site_authority",
        sa.Column("authority_id", sa.String(length=64), nullable=False),
        sa.Column("site_id", sa.String(length=64), nullable=False),
        sa.Column("epoch", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fenced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_site_id", sa.String(length=64), nullable=True),
        sa.Column("recovery_id", sa.String(length=64), nullable=True),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("content_digest", sa.String(length=128), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("authority_id"),
        sa.UniqueConstraint("site_id", "epoch", name="uq_site_authority_epoch"),
    )
    op.create_index("ix_site_authority_site_id", "site_authority", ["site_id"])

    op.create_table(
        "authority_transition_receipts",
        sa.Column("receipt_id", sa.String(length=64), nullable=False),
        sa.Column("site_id", sa.String(length=64), nullable=False),
        sa.Column("from_epoch", sa.Integer(), nullable=False),
        sa.Column("to_epoch", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("receipt_id"),
    )

    op.create_table(
        "backup_manifests",
        sa.Column("backup_id", sa.String(length=64), nullable=False),
        sa.Column("source_site_id", sa.String(length=64), nullable=False),
        sa.Column("source_epoch", sa.Integer(), nullable=False),
        sa.Column("source_commit_sha", sa.String(length=64), nullable=False),
        sa.Column("schema_revision", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("integrity_digest", sa.String(length=128), nullable=False),
        sa.Column("secret_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("backup_id"),
    )

    op.create_table(
        "recovery_runs",
        sa.Column("recovery_id", sa.String(length=64), nullable=False),
        sa.Column("backup_id", sa.String(length=64), nullable=False),
        sa.Column("old_site_id", sa.String(length=64), nullable=False),
        sa.Column("old_epoch", sa.Integer(), nullable=False),
        sa.Column("new_site_id", sa.String(length=64), nullable=False),
        sa.Column("new_epoch", sa.Integer(), nullable=False),
        sa.Column("final_state", sa.String(length=32), nullable=False),
        sa.Column("evidence_digest", sa.String(length=128), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("recovery_id"),
    )

    op.create_table(
        "extension_manifests",
        sa.Column("manifest_pk", sa.String(length=64), nullable=False),
        sa.Column("extension_id", sa.String(length=64), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("content_digest", sa.String(length=128), nullable=False),
        sa.Column("risk_class", sa.String(length=32), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("manifest_pk"),
        sa.UniqueConstraint("extension_id", "version", name="uq_extension_id_version"),
    )

    op.create_table(
        "project_extension_grants",
        sa.Column("grant_id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("extension_id", sa.String(length=64), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("enabled", sa.String(length=16), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("grant_id"),
        sa.UniqueConstraint("project_id", "extension_id", "version", name="uq_project_extension_grant"),
    )

    op.create_table(
        "product_candidates",
        sa.Column("candidate_id", sa.String(length=64), nullable=False),
        sa.Column("source_sha", sa.String(length=64), nullable=False),
        sa.Column("schema_revision", sa.String(length=64), nullable=False),
        sa.Column("dependency_lock_digest", sa.String(length=128), nullable=False),
        sa.Column("frozen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("candidate_id"),
    )

    op.create_table(
        "scheduler_policies",
        sa.Column("policy_id", sa.String(length=64), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("digest", sa.String(length=128), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("policy_id"),
    )

    op.create_table(
        "project_scheduling_state",
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("fairness_debt", sa.Float(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("site_epoch", sa.Integer(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("project_id"),
    )

    op.create_table(
        "resource_reservation_intents",
        sa.Column("intent_id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("mission_id", sa.String(length=64), nullable=False),
        sa.Column("attempt_id", sa.String(length=64), nullable=False),
        sa.Column("site_epoch", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("intent_id"),
        sa.UniqueConstraint("attempt_id", name="uq_reservation_attempt"),
    )

    op.create_table(
        "capability_packs",
        sa.Column("pack_pk", sa.String(length=64), nullable=False),
        sa.Column("pack_id", sa.String(length=64), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("content_digest", sa.String(length=128), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("pack_pk"),
        sa.UniqueConstraint("pack_id", "version", name="uq_capability_pack_version"),
    )

    op.create_table(
        "objectives",
        sa.Column("objective_id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("current_version", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("objective_id"),
    )

    op.create_table(
        "objective_versions",
        sa.Column("version_id", sa.String(length=64), nullable=False),
        sa.Column("objective_id", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("version_id"),
        sa.UniqueConstraint("objective_id", "version", name="uq_objective_version"),
    )

    op.create_table(
        "trigger_receipts",
        sa.Column("receipt_id", sa.String(length=64), nullable=False),
        sa.Column("objective_id", sa.String(length=64), nullable=False),
        sa.Column("dedupe_key", sa.String(length=192), nullable=False),
        sa.Column("trigger_kind", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("receipt_id"),
        sa.UniqueConstraint("objective_id", "dedupe_key", name="uq_trigger_dedupe"),
    )

    op.create_table(
        "mission_proposals",
        sa.Column("proposal_id", sa.String(length=64), nullable=False),
        sa.Column("objective_id", sa.String(length=64), nullable=False),
        sa.Column("objective_version", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("mission_id", sa.String(length=64), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("proposal_id"),
    )

    op.create_table(
        "learning_proposals",
        sa.Column("proposal_id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("proposal_id"),
    )


def downgrade() -> None:
    for table in (
        "learning_proposals",
        "mission_proposals",
        "trigger_receipts",
        "objective_versions",
        "objectives",
        "capability_packs",
        "resource_reservation_intents",
        "project_scheduling_state",
        "scheduler_policies",
        "product_candidates",
        "project_extension_grants",
        "extension_manifests",
        "recovery_runs",
        "backup_manifests",
        "authority_transition_receipts",
        "site_authority",
    ):
        op.drop_table(table)

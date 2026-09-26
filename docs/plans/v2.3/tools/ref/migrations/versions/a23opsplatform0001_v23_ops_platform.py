"""Alembic migration: V2.3 operations platform + V2.0 durable holds/lessons."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a23opsplatform0001"
down_revision: str | Sequence[str] | None = "a20pursuitpersist0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _jsonb() -> postgresql.JSONB:
    return postgresql.JSONB(astext_type=sa.Text())


def _ts(name: str) -> sa.Column:
    return sa.Column(
        name, sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )


def upgrade() -> None:
    op.create_table(
        "v23_project_queue_state",
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", _jsonb(), nullable=False),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("project_id"),
    )
    op.create_index(
        "ix_v23_project_queue_state_tenant_id", "v23_project_queue_state", ["tenant_id"]
    )

    op.create_table(
        "v23_mission_queue_state",
        sa.Column("mission_id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("lifecycle", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", _jsonb(), nullable=False),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("mission_id"),
    )
    op.create_index(
        "ix_v23_mission_queue_state_project_id", "v23_mission_queue_state", ["project_id"]
    )
    op.create_index(
        "ix_v23_mission_queue_state_lifecycle", "v23_mission_queue_state", ["lifecycle"]
    )

    op.create_table(
        "v23_scheduler_receipts",
        sa.Column("receipt_id", sa.String(length=64), nullable=False),
        sa.Column("sequence", sa.BigInteger(), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=True),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column("reason_code", sa.String(length=48), nullable=False),
        sa.Column("digest", sa.String(length=64), nullable=False),
        sa.Column("payload", _jsonb(), nullable=False),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("receipt_id"),
        sa.UniqueConstraint("sequence", name="uq_v23_scheduler_receipts_sequence"),
    )
    op.create_index(
        "ix_v23_scheduler_receipts_project_id", "v23_scheduler_receipts", ["project_id"]
    )

    op.create_table(
        "v23_dispatch_intents",
        sa.Column("intent_id", sa.String(length=64), nullable=False),
        sa.Column("attempt_id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", _jsonb(), nullable=False),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("intent_id"),
        sa.UniqueConstraint("attempt_id", name="uq_v23_dispatch_intents_attempt"),
    )
    op.create_index(
        "ix_v23_dispatch_intents_project_id", "v23_dispatch_intents", ["project_id"]
    )
    op.create_index("ix_v23_dispatch_intents_state", "v23_dispatch_intents", ["state"])

    op.create_table(
        "v23_scheduler_epochs",
        sa.Column("site_id", sa.String(length=64), nullable=False),
        sa.Column("epoch", sa.BigInteger(), nullable=False),
        sa.Column("holder_id", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("site_id"),
    )

    op.create_table(
        "v23_pack_installs",
        sa.Column("install_id", sa.String(length=64), nullable=False),
        sa.Column("pack_id", sa.String(length=128), nullable=False),
        sa.Column("pack_version", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", _jsonb(), nullable=False),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("install_id"),
        sa.UniqueConstraint(
            "pack_id", "pack_version", "project_id", name="uq_v23_pack_installs"
        ),
    )
    op.create_index("ix_v23_pack_installs_pack_id", "v23_pack_installs", ["pack_id"])

    op.create_table(
        "v23_ops_events",
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("component", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=True),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
        sa.Column("site_epoch", sa.BigInteger(), nullable=True),
        sa.Column("payload", _jsonb(), nullable=False),
        _ts("at"),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_v23_ops_events_kind", "v23_ops_events", ["kind"])
    op.create_index("ix_v23_ops_events_trace_id", "v23_ops_events", ["trace_id"])
    op.create_index("ix_v23_ops_events_project_at", "v23_ops_events", ["project_id", "at"])

    op.create_table(
        "v20_goal_usage_holds",
        sa.Column("hold_id", sa.String(length=64), nullable=False),
        sa.Column("goal_id", sa.String(length=64), nullable=False),
        sa.Column("mission_id", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", _jsonb(), nullable=False),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("hold_id"),
    )
    op.create_index("ix_v20_goal_usage_holds_goal_id", "v20_goal_usage_holds", ["goal_id"])
    op.create_index("ix_v20_goal_usage_holds_state", "v20_goal_usage_holds", ["state"])

    op.create_table(
        "v20_pursuit_lessons",
        sa.Column("lesson_id", sa.String(length=64), nullable=False),
        sa.Column("goal_id", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("payload", _jsonb(), nullable=False),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("lesson_id"),
    )
    op.create_index("ix_v20_pursuit_lessons_goal_id", "v20_pursuit_lessons", ["goal_id"])


def downgrade() -> None:
    op.drop_index("ix_v20_pursuit_lessons_goal_id", table_name="v20_pursuit_lessons")
    op.drop_table("v20_pursuit_lessons")
    op.drop_index("ix_v20_goal_usage_holds_state", table_name="v20_goal_usage_holds")
    op.drop_index("ix_v20_goal_usage_holds_goal_id", table_name="v20_goal_usage_holds")
    op.drop_table("v20_goal_usage_holds")
    op.drop_index("ix_v23_ops_events_project_at", table_name="v23_ops_events")
    op.drop_index("ix_v23_ops_events_trace_id", table_name="v23_ops_events")
    op.drop_index("ix_v23_ops_events_kind", table_name="v23_ops_events")
    op.drop_table("v23_ops_events")
    op.drop_index("ix_v23_pack_installs_pack_id", table_name="v23_pack_installs")
    op.drop_table("v23_pack_installs")
    op.drop_table("v23_scheduler_epochs")
    op.drop_index("ix_v23_dispatch_intents_state", table_name="v23_dispatch_intents")
    op.drop_index("ix_v23_dispatch_intents_project_id", table_name="v23_dispatch_intents")
    op.drop_table("v23_dispatch_intents")
    op.drop_index("ix_v23_scheduler_receipts_project_id", table_name="v23_scheduler_receipts")
    op.drop_table("v23_scheduler_receipts")
    op.drop_index("ix_v23_mission_queue_state_lifecycle", table_name="v23_mission_queue_state")
    op.drop_index("ix_v23_mission_queue_state_project_id", table_name="v23_mission_queue_state")
    op.drop_table("v23_mission_queue_state")
    op.drop_index("ix_v23_project_queue_state_tenant_id", table_name="v23_project_queue_state")
    op.drop_table("v23_project_queue_state")

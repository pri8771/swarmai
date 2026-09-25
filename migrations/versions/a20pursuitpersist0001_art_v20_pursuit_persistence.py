"""Alembic migration: V2 pursuit / goal durable authority (PC-02 / R20-04)."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a20pursuitpersist0001"
down_revision: str | Sequence[str] | None = "a18tov30schema0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "goals",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("achievement_authority", sa.String(length=32), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_goals_project_id", "goals", ["project_id"])
    op.create_index("ix_goals_status", "goals", ["status"])
    op.create_index("ix_goals_project_status", "goals", ["project_id", "status"])

    op.create_table(
        "goal_criterion_verdicts",
        sa.Column("verdict_id", sa.String(length=64), nullable=False),
        sa.Column("goal_id", sa.String(length=64), nullable=False),
        sa.Column("criterion_key", sa.String(length=256), nullable=False),
        sa.Column("goal_revision", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("authority", sa.String(length=32), nullable=False),
        sa.Column("evidence_digest", sa.String(length=128), nullable=True),
        sa.Column("verifier_receipt_id", sa.String(length=64), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"]),
        sa.PrimaryKeyConstraint("verdict_id"),
        sa.UniqueConstraint(
            "goal_id", "criterion_key", "goal_revision", name="uq_goal_criterion_rev"
        ),
    )
    op.create_index(
        "ix_goal_criterion_verdicts_goal_id", "goal_criterion_verdicts", ["goal_id"]
    )

    op.create_table(
        "pursuit_cycles",
        sa.Column("cycle_id", sa.String(length=64), nullable=False),
        sa.Column("goal_id", sa.String(length=64), nullable=False),
        sa.Column("phase", sa.String(length=32), nullable=False),
        sa.Column("decided_kind", sa.String(length=32), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("cycle_id"),
    )
    op.create_index("ix_pursuit_cycles_goal_id", "pursuit_cycles", ["goal_id"])
    op.create_index(
        "ix_pursuit_cycles_goal_at", "pursuit_cycles", ["goal_id", "created_at"]
    )

    op.create_table(
        "pursuit_schedules",
        sa.Column("goal_id", sa.String(length=64), nullable=False),
        sa.Column("next_due_at", sa.Float(), nullable=False),
        sa.Column("backoff_seconds", sa.Float(), nullable=False),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False),
        sa.Column("consecutive_no_progress", sa.Integer(), nullable=False),
        sa.Column("last_cycle_at", sa.Float(), nullable=True),
        sa.Column("wait_reason", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("goal_id"),
    )

    op.create_table(
        "pursuit_dedupe",
        sa.Column("dedupe_id", sa.String(length=64), nullable=False),
        sa.Column("goal_id", sa.String(length=64), nullable=False),
        sa.Column("dedupe_key", sa.String(length=64), nullable=False),
        sa.Column("proposal_id", sa.String(length=64), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("dedupe_id"),
        sa.UniqueConstraint("dedupe_key", name="uq_pursuit_dedupe_key"),
    )
    op.create_index("ix_pursuit_dedupe_goal_id", "pursuit_dedupe", ["goal_id"])


def downgrade() -> None:
    op.drop_index("ix_pursuit_dedupe_goal_id", table_name="pursuit_dedupe")
    op.drop_table("pursuit_dedupe")
    op.drop_table("pursuit_schedules")
    op.drop_index("ix_pursuit_cycles_goal_at", table_name="pursuit_cycles")
    op.drop_index("ix_pursuit_cycles_goal_id", table_name="pursuit_cycles")
    op.drop_table("pursuit_cycles")
    op.drop_index("ix_goal_criterion_verdicts_goal_id", table_name="goal_criterion_verdicts")
    op.drop_table("goal_criterion_verdicts")
    op.drop_index("ix_goals_project_status", table_name="goals")
    op.drop_index("ix_goals_status", table_name="goals")
    op.drop_index("ix_goals_project_id", table_name="goals")
    op.drop_table("goals")

"""V2B-004a / ART-V17-DURABLE-EFFECT-SCHEMA — approvals + action_effects."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a17effect004a0001"
down_revision: str | Sequence[str] | None = "a16know003a0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("approvals", sa.Column("project_id", sa.String(length=64), nullable=True))
    op.add_column("approvals", sa.Column("actor", sa.String(length=64), nullable=True))
    op.add_column("approvals", sa.Column("integration_id", sa.String(length=64), nullable=True))
    op.add_column(
        "approvals", sa.Column("integration_version", sa.String(length=32), nullable=True)
    )
    op.add_column("approvals", sa.Column("operation", sa.String(length=64), nullable=True))
    op.add_column("approvals", sa.Column("effect_key", sa.String(length=192), nullable=True))
    op.add_column(
        "approvals",
        sa.Column("max_effect_count", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column(
        "approvals", sa.Column("used_count", sa.Integer(), server_default="0", nullable=False)
    )
    op.add_column("approvals", sa.Column("policy_version", sa.String(length=64), nullable=True))
    op.add_column(
        "approvals",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
    )
    op.add_column(
        "approvals",
        sa.Column(
            "constraints",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.create_index("ix_approvals_project_id", "approvals", ["project_id"])
    op.create_index("ix_approvals_effect_key", "approvals", ["effect_key"])

    op.create_table(
        "action_effects",
        sa.Column("effect_id", sa.String(length=64), nullable=False),
        sa.Column("effect_key", sa.String(length=192), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("mission_id", sa.String(length=64), nullable=True),
        sa.Column("task_id", sa.String(length=64), nullable=True),
        sa.Column("attempt_id", sa.String(length=64), nullable=True),
        sa.Column("action_id", sa.String(length=64), nullable=False),
        sa.Column("approval_id", sa.String(length=64), nullable=True),
        sa.Column("integration_id", sa.String(length=64), nullable=False),
        sa.Column("integration_version", sa.String(length=32), nullable=False),
        sa.Column("operation", sa.String(length=64), nullable=False),
        sa.Column("destination_digest", sa.String(length=128), nullable=False),
        sa.Column("payload_hash", sa.String(length=128), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=True),
        sa.Column("lease_generation", sa.Integer(), nullable=False),
        sa.Column("cancellation_generation", sa.Integer(), nullable=False),
        sa.Column(
            "pre_observation",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "post_observation",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "reconciliation",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reconciled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("effect_id"),
        sa.UniqueConstraint("project_id", "effect_key", name="uq_action_effect_project_key"),
    )
    op.create_index("ix_action_effects_effect_key", "action_effects", ["effect_key"])
    op.create_index("ix_action_effects_project_id", "action_effects", ["project_id"])
    op.create_index("ix_action_effects_action_id", "action_effects", ["action_id"])
    op.create_index("ix_action_effects_state", "action_effects", ["state"])
    op.create_index(
        "ix_action_effects_project_state", "action_effects", ["project_id", "state"]
    )


def downgrade() -> None:
    op.drop_table("action_effects")
    op.drop_index("ix_approvals_effect_key", table_name="approvals")
    op.drop_index("ix_approvals_project_id", table_name="approvals")
    for col in (
        "constraints",
        "created_at",
        "policy_version",
        "used_count",
        "max_effect_count",
        "effect_key",
        "operation",
        "integration_version",
        "integration_id",
        "actor",
        "project_id",
    ):
        op.drop_column("approvals", col)

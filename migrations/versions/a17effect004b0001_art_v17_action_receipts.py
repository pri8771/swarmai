"""R27a / ART-V17-APPROVAL-BINDING — durable immutable action receipts + effect bookkeeping."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a17effect004b0001"
down_revision: str | Sequence[str] | None = "a17effect004a0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "action_effects", sa.Column("state_reason", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "action_effects",
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "action_effects", sa.Column("executor_id", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "action_effects",
        sa.Column("approval_consumed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "action_receipts",
        sa.Column("receipt_id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("effect_id", sa.String(length=64), nullable=False),
        sa.Column("effect_key", sa.String(length=192), nullable=False),
        sa.Column("action_id", sa.String(length=64), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column(
            "reconciliation_state",
            sa.String(length=32),
            nullable=False,
            server_default="none",
        ),
        sa.Column("evidence_digest", sa.String(length=128), nullable=False),
        sa.Column("receipt", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("receipt_id"),
        sa.ForeignKeyConstraint(
            ["effect_id"], ["action_effects.effect_id"], name="fk_action_receipt_effect"
        ),
        sa.UniqueConstraint(
            "effect_id", "attempt_number", name="uq_action_receipt_effect_attempt"
        ),
    )
    op.create_index("ix_action_receipts_project_id", "action_receipts", ["project_id"])
    op.create_index("ix_action_receipts_action_id", "action_receipts", ["action_id"])
    op.create_index(
        "ix_action_receipts_project_effect_key",
        "action_receipts",
        ["project_id", "effect_key"],
    )


def downgrade() -> None:
    op.drop_table("action_receipts")
    for col in ("approval_consumed_at", "executor_id", "attempt_count", "state_reason"):
        op.drop_column("action_effects", col)

"""V2A-003a / ART-V15-LEASE-FENCING — durable schema delta migration.

Extends worker_leases + task_attempts; adds task_leases + worker_results.
Preserves legacy rows (new columns nullable / defaulted).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a15lease003a0001"
down_revision: str | Sequence[str] | None = "9eb193b10f4e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Delta A: worker_leases (registration) ---
    op.add_column("worker_leases", sa.Column("project_id", sa.String(length=64), nullable=True))
    op.add_column("worker_leases", sa.Column("trust_class", sa.String(length=32), nullable=True))
    op.add_column("worker_leases", sa.Column("token_hash", sa.String(length=128), nullable=True))
    op.add_column("worker_leases", sa.Column("token_id", sa.String(length=64), nullable=True))
    op.add_column(
        "worker_leases",
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
    )
    op.add_column(
        "worker_leases",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
    )
    op.add_column(
        "worker_leases",
        sa.Column("drain_requested_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "worker_leases", sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "worker_leases", sa.Column("policy_version", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "worker_leases", sa.Column("software_version", sa.String(length=64), nullable=True)
    )
    op.add_column("worker_leases", sa.Column("build_sha", sa.String(length=64), nullable=True))
    op.add_column(
        "worker_leases",
        sa.Column(
            "privacy_classes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "worker_leases",
        sa.Column(
            "resource_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_worker_leases_project_id"), "worker_leases", ["project_id"], unique=False
    )
    op.create_index(op.f("ix_worker_leases_token_id"), "worker_leases", ["token_id"], unique=False)
    op.create_index(
        "ix_worker_leases_project_status",
        "worker_leases",
        ["project_id", "status"],
        unique=False,
    )

    # --- Delta B: task_attempts ---
    op.add_column("task_attempts", sa.Column("project_id", sa.String(length=64), nullable=True))
    op.add_column("task_attempts", sa.Column("mission_id", sa.String(length=64), nullable=True))
    op.add_column(
        "task_attempts",
        sa.Column("task_revision", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column(
        "task_attempts", sa.Column("input_digest", sa.String(length=128), nullable=True)
    )
    op.add_column(
        "task_attempts", sa.Column("source_revision", sa.String(length=128), nullable=True)
    )
    op.add_column(
        "task_attempts",
        sa.Column("cancellation_generation", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "task_attempts",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "task_attempts", sa.Column("terminal_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "task_attempts", sa.Column("accepted_result_id", sa.String(length=64), nullable=True)
    )
    op.create_foreign_key(
        "fk_task_attempts_mission_id",
        "task_attempts",
        "missions",
        ["mission_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_task_attempts_project_id"), "task_attempts", ["project_id"], unique=False
    )
    op.create_index(
        "ix_task_attempts_mission_id", "task_attempts", ["mission_id"], unique=False
    )
    op.create_index(
        "ix_task_attempts_project_status",
        "task_attempts",
        ["project_id", "status"],
        unique=False,
    )

    # --- Delta C: task_leases ---
    op.create_table(
        "task_leases",
        sa.Column("lease_id", sa.String(length=64), nullable=False),
        sa.Column("attempt_id", sa.String(length=64), nullable=False),
        sa.Column("task_id", sa.String(length=64), nullable=False),
        sa.Column("mission_id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("worker_id", sa.String(length=64), nullable=False),
        sa.Column("worker_generation", sa.Integer(), nullable=False),
        sa.Column("task_revision", sa.Integer(), nullable=False),
        sa.Column("input_digest", sa.String(length=128), nullable=True),
        sa.Column("source_revision", sa.String(length=128), nullable=True),
        sa.Column("cancellation_generation", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("renewable_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "reservation_refs",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("effect_scope", sa.String(length=64), nullable=True),
        sa.Column("policy_version", sa.String(length=64), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["attempt_id"], ["task_attempts.attempt_id"]),
        sa.ForeignKeyConstraint(["mission_id"], ["missions.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"]),
        sa.PrimaryKeyConstraint("lease_id"),
    )
    op.create_index(op.f("ix_task_leases_attempt_id"), "task_leases", ["attempt_id"], unique=False)
    op.create_index(op.f("ix_task_leases_mission_id"), "task_leases", ["mission_id"], unique=False)
    op.create_index(op.f("ix_task_leases_project_id"), "task_leases", ["project_id"], unique=False)
    op.create_index(op.f("ix_task_leases_state"), "task_leases", ["state"], unique=False)
    op.create_index(op.f("ix_task_leases_task_id"), "task_leases", ["task_id"], unique=False)
    op.create_index(op.f("ix_task_leases_worker_id"), "task_leases", ["worker_id"], unique=False)
    op.create_index(
        "ix_task_leases_project_state",
        "task_leases",
        ["project_id", "state"],
        unique=False,
    )

    # --- Delta D: worker_results ---
    op.create_table(
        "worker_results",
        sa.Column("result_id", sa.String(length=64), nullable=False),
        sa.Column("attempt_id", sa.String(length=64), nullable=False),
        sa.Column("lease_id", sa.String(length=64), nullable=False),
        sa.Column("task_id", sa.String(length=64), nullable=False),
        sa.Column("mission_id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("worker_id", sa.String(length=64), nullable=False),
        sa.Column("worker_generation", sa.Integer(), nullable=False),
        sa.Column("task_revision", sa.Integer(), nullable=False),
        sa.Column("input_digest", sa.String(length=128), nullable=True),
        sa.Column("source_revision", sa.String(length=128), nullable=True),
        sa.Column("result_status", sa.String(length=32), nullable=False),
        sa.Column(
            "artifact_manifest",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("checks", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("usage", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "effect_receipts",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("acceptance_state", sa.String(length=32), nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["attempt_id"], ["task_attempts.attempt_id"]),
        sa.ForeignKeyConstraint(["lease_id"], ["task_leases.lease_id"]),
        sa.PrimaryKeyConstraint("result_id"),
    )
    op.create_index(
        op.f("ix_worker_results_acceptance_state"),
        "worker_results",
        ["acceptance_state"],
        unique=False,
    )
    op.create_index(
        op.f("ix_worker_results_attempt_id"), "worker_results", ["attempt_id"], unique=False
    )
    op.create_index(
        op.f("ix_worker_results_lease_id"), "worker_results", ["lease_id"], unique=False
    )
    op.create_index(
        op.f("ix_worker_results_mission_id"), "worker_results", ["mission_id"], unique=False
    )
    op.create_index(
        op.f("ix_worker_results_project_id"), "worker_results", ["project_id"], unique=False
    )
    op.create_index(
        op.f("ix_worker_results_task_id"), "worker_results", ["task_id"], unique=False
    )
    op.create_index(
        op.f("ix_worker_results_worker_id"), "worker_results", ["worker_id"], unique=False
    )
    op.create_index(
        "ix_worker_results_project_acceptance",
        "worker_results",
        ["project_id", "acceptance_state"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_worker_results_project_acceptance", table_name="worker_results")
    op.drop_index(op.f("ix_worker_results_worker_id"), table_name="worker_results")
    op.drop_index(op.f("ix_worker_results_task_id"), table_name="worker_results")
    op.drop_index(op.f("ix_worker_results_project_id"), table_name="worker_results")
    op.drop_index(op.f("ix_worker_results_mission_id"), table_name="worker_results")
    op.drop_index(op.f("ix_worker_results_lease_id"), table_name="worker_results")
    op.drop_index(op.f("ix_worker_results_attempt_id"), table_name="worker_results")
    op.drop_index(op.f("ix_worker_results_acceptance_state"), table_name="worker_results")
    op.drop_table("worker_results")

    op.drop_index("ix_task_leases_project_state", table_name="task_leases")
    op.drop_index(op.f("ix_task_leases_worker_id"), table_name="task_leases")
    op.drop_index(op.f("ix_task_leases_task_id"), table_name="task_leases")
    op.drop_index(op.f("ix_task_leases_state"), table_name="task_leases")
    op.drop_index(op.f("ix_task_leases_project_id"), table_name="task_leases")
    op.drop_index(op.f("ix_task_leases_mission_id"), table_name="task_leases")
    op.drop_index(op.f("ix_task_leases_attempt_id"), table_name="task_leases")
    op.drop_table("task_leases")

    op.drop_index("ix_task_attempts_project_status", table_name="task_attempts")
    op.drop_index("ix_task_attempts_mission_id", table_name="task_attempts")
    op.drop_index(op.f("ix_task_attempts_project_id"), table_name="task_attempts")
    op.drop_constraint("fk_task_attempts_mission_id", "task_attempts", type_="foreignkey")
    op.drop_column("task_attempts", "accepted_result_id")
    op.drop_column("task_attempts", "terminal_at")
    op.drop_column("task_attempts", "created_at")
    op.drop_column("task_attempts", "cancellation_generation")
    op.drop_column("task_attempts", "source_revision")
    op.drop_column("task_attempts", "input_digest")
    op.drop_column("task_attempts", "task_revision")
    op.drop_column("task_attempts", "mission_id")
    op.drop_column("task_attempts", "project_id")

    op.drop_index("ix_worker_leases_project_status", table_name="worker_leases")
    op.drop_index(op.f("ix_worker_leases_token_id"), table_name="worker_leases")
    op.drop_index(op.f("ix_worker_leases_project_id"), table_name="worker_leases")
    op.drop_column("worker_leases", "resource_payload")
    op.drop_column("worker_leases", "privacy_classes")
    op.drop_column("worker_leases", "build_sha")
    op.drop_column("worker_leases", "software_version")
    op.drop_column("worker_leases", "policy_version")
    op.drop_column("worker_leases", "revoked_at")
    op.drop_column("worker_leases", "drain_requested_at")
    op.drop_column("worker_leases", "updated_at")
    op.drop_column("worker_leases", "registered_at")
    op.drop_column("worker_leases", "token_id")
    op.drop_column("worker_leases", "token_hash")
    op.drop_column("worker_leases", "trust_class")
    op.drop_column("worker_leases", "project_id")

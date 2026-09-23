"""V2B-003a / ART-V16-DURABLE-SCHEMA — knowledge_items/links/tombstones."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a16know003a0001"
down_revision: str | Sequence[str] | None = "a15lease003a0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "knowledge_items",
        sa.Column("row_id", sa.String(length=64), nullable=False),
        sa.Column("item_id", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("mission_id", sa.String(length=64), nullable=True),
        sa.Column("class", sa.String(length=32), nullable=False),
        sa.Column("topic", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("acceptance_state", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("producer_type", sa.String(length=32), nullable=False),
        sa.Column("producer_ref", sa.String(length=128), nullable=True),
        sa.Column(
            "permission_labels",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "retrieval_labels",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "source_digests",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "provenance_refs",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("content_digest", sa.String(length=128), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("row_id"),
        sa.UniqueConstraint("item_id", "version", name="uq_knowledge_item_version"),
    )
    op.create_index("ix_knowledge_items_item_id", "knowledge_items", ["item_id"])
    op.create_index("ix_knowledge_items_project_id", "knowledge_items", ["project_id"])
    op.create_index("ix_knowledge_items_mission_id", "knowledge_items", ["mission_id"])
    op.create_index("ix_knowledge_items_class", "knowledge_items", ["class"])
    op.create_index(
        "ix_knowledge_items_acceptance_state", "knowledge_items", ["acceptance_state"]
    )
    op.create_index(
        "ix_knowledge_items_project_class_state",
        "knowledge_items",
        ["project_id", "class", "acceptance_state"],
    )
    op.create_index(
        "ix_knowledge_items_project_item", "knowledge_items", ["project_id", "item_id"]
    )

    op.create_table(
        "knowledge_links",
        sa.Column("link_id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("from_item_id", sa.String(length=64), nullable=False),
        sa.Column("from_version", sa.Integer(), nullable=False),
        sa.Column("relation", sa.String(length=32), nullable=False),
        sa.Column("to_item_id", sa.String(length=64), nullable=False),
        sa.Column("to_version", sa.Integer(), nullable=False),
        sa.Column("evidence_ref", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("link_id"),
    )
    op.create_index("ix_knowledge_links_project_id", "knowledge_links", ["project_id"])
    op.create_index("ix_knowledge_links_from_item_id", "knowledge_links", ["from_item_id"])
    op.create_index("ix_knowledge_links_to_item_id", "knowledge_links", ["to_item_id"])
    op.create_index("ix_knowledge_links_relation", "knowledge_links", ["relation"])
    op.create_index(
        "ix_knowledge_links_project_from", "knowledge_links", ["project_id", "from_item_id"]
    )
    op.create_index(
        "ix_knowledge_links_project_to", "knowledge_links", ["project_id", "to_item_id"]
    )

    op.create_table(
        "knowledge_tombstones",
        sa.Column("tombstone_id", sa.String(length=64), nullable=False),
        sa.Column("item_id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("deleted_version", sa.Integer(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason_class", sa.String(length=64), nullable=False),
        sa.Column("replacement_item_id", sa.String(length=64), nullable=True),
        sa.Column("replacement_version", sa.Integer(), nullable=True),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("tombstone_id"),
        sa.UniqueConstraint(
            "project_id", "item_id", "deleted_version", name="uq_knowledge_tombstone"
        ),
    )
    op.create_index("ix_knowledge_tombstones_item_id", "knowledge_tombstones", ["item_id"])
    op.create_index(
        "ix_knowledge_tombstones_project_id", "knowledge_tombstones", ["project_id"]
    )
    op.create_index(
        "ix_knowledge_tombstones_project_item",
        "knowledge_tombstones",
        ["project_id", "item_id"],
    )


def downgrade() -> None:
    op.drop_table("knowledge_tombstones")
    op.drop_table("knowledge_links")
    op.drop_table("knowledge_items")

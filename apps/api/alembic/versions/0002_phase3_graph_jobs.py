"""Phase 3 knowledge graph + reminders."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_phase3"
down_revision: Union[str, None] = "0001_phase2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    node_label = postgresql.ENUM(
        "user",
        "project",
        "goal",
        "task",
        "meeting",
        "document",
        "preference",
        "person",
        name="kg_node_label",
        create_type=False,
    )
    edge_type = postgresql.ENUM(
        "owns",
        "related_to",
        "part_of",
        "depends_on",
        "attends",
        "references",
        "prefers",
        "assigned_to",
        name="kg_edge_type",
        create_type=False,
    )
    op.execute(
        "DO $$ BEGIN CREATE TYPE kg_node_label AS ENUM "
        "('user','project','goal','task','meeting','document','preference','person'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    op.execute(
        "DO $$ BEGIN CREATE TYPE kg_edge_type AS ENUM "
        "('owns','related_to','part_of','depends_on','attends','references','prefers','assigned_to'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )

    op.create_table(
        "kg_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("label", node_label, nullable=False),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("properties", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_kg_nodes_user_label", "kg_nodes", ["user_id", "label"])

    op.create_table(
        "kg_edges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("kg_nodes.id", ondelete="CASCADE")),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("kg_nodes.id", ondelete="CASCADE")),
        sa.Column("edge_type", edge_type, nullable=False),
        sa.Column("properties", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_kg_edges_user_type", "kg_edges", ["user_id", "edge_type"])

    op.create_table(
        "reminders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("body", sa.Text(), server_default=""),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="scheduled"),
        sa.Column("workflow_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("fired_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_reminders_user_id", "reminders", ["user_id"])
    op.create_index("ix_reminders_due_at", "reminders", ["due_at"])


def downgrade() -> None:
    op.drop_table("reminders")
    op.drop_table("kg_edges")
    op.drop_table("kg_nodes")
    op.execute("DROP TYPE IF EXISTS kg_edge_type")
    op.execute("DROP TYPE IF EXISTS kg_node_label")

"""add ai_generation_sessions table

Revision ID: b1c2d3e4f5a6
Revises: a1b2c3d4e5f7
Create Date: 2026-04-26 13:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "b1c2d3e4f5a6"
down_revision = "a1b2c3d4e5f7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_generation_sessions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("messages", sa.JSON(), nullable=False),
        sa.Column("analysis", sa.JSON(), nullable=True),
        sa.Column("draft_id", sa.String(), nullable=True),
        sa.Column("model_name", sa.String(100), nullable=True),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
    )
    op.create_index(
        "ix_ai_gen_sessions_owner_updated",
        "ai_generation_sessions",
        ["owner_id", "updated_at"],
    )


def downgrade():
    op.drop_index("ix_ai_gen_sessions_owner_updated", table_name="ai_generation_sessions")
    op.drop_table("ai_generation_sessions")

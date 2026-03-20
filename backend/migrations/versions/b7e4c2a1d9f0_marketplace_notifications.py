"""marketplace notifications

Revision ID: b7e4c2a1d9f0
Revises: a5c1d2e3f4b5
Create Date: 2026-03-19 20:10:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "b7e4c2a1d9f0"
down_revision = "a5c1d2e3f4b5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notifications_user_unread",
        "notifications",
        ["user_id", "is_read"],
        unique=False,
        postgresql_where=sa.text("is_read = false"),
    )


def downgrade():
    op.drop_index("ix_notifications_user_unread", table_name="notifications")
    op.drop_table("notifications")

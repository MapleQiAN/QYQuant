"""add data source health status

Revision ID: a4c9d2e1f6b7
Revises: f7b3c2d1e9a0
Create Date: 2026-03-27 10:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "a4c9d2e1f6b7"
down_revision = "f7b3c2d1e9a0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "data_source_health_status",
        sa.Column("source_name", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_notified_status", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint("source_name"),
    )


def downgrade():
    op.drop_table("data_source_health_status")

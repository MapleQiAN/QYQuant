"""reports moderation

Revision ID: e4b1c2d3f4a5
Revises: d2a1b3c4e5fd
Create Date: 2026-03-26 11:10:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "e4b1c2d3f4a5"
down_revision = "d2a1b3c4e5fd"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "reports",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("reporter_id", sa.String(), nullable=False),
        sa.Column("strategy_id", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reports_reporter_strategy", "reports", ["reporter_id", "strategy_id"], unique=False)
    op.create_index("ix_reports_status", "reports", ["status"], unique=False)


def downgrade():
    op.drop_index("ix_reports_status", table_name="reports")
    op.drop_index("ix_reports_reporter_strategy", table_name="reports")
    op.drop_table("reports")

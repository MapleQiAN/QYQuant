"""Fix review_status default from pending to draft

Revision ID: a1b2c3d4e5f6
Revises: 20260419a1b2
Create Date: 2026-04-19
"""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "20260419a1b2"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("strategies") as batch_op:
        batch_op.alter_column(
            "review_status",
            server_default=sa.text("'draft'"),
        )

    op.execute(
        "UPDATE strategies SET review_status = 'draft' "
        "WHERE review_status = 'pending' "
        "AND (display_metrics IS NULL OR display_metrics::text = '{}')"
    )


def downgrade():
    with op.batch_alter_table("strategies") as batch_op:
        batch_op.alter_column(
            "review_status",
            server_default=sa.text("'pending'"),
        )

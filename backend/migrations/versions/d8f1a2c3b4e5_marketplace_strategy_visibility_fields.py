"""marketplace strategy visibility fields

Revision ID: d8f1a2c3b4e5
Revises: f2c7a1b9d4e6
Create Date: 2026-03-18 11:20:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "d8f1a2c3b4e5"
down_revision = "f2c7a1b9d4e6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("strategies") as batch_op:
        batch_op.add_column(sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("review_status", sa.String(length=32), nullable=False, server_default="pending"))
        batch_op.add_column(sa.Column("display_metrics", sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table("strategies") as batch_op:
        batch_op.drop_column("display_metrics")
        batch_op.drop_column("review_status")
        batch_op.drop_column("is_verified")
        batch_op.drop_column("is_public")

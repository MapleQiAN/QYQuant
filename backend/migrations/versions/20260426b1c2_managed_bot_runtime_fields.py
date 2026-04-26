"""add managed bot runtime fields

Revision ID: 20260426b1c2
Revises: 20260426a1b2
Create Date: 2026-04-26 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "20260426b1c2"
down_revision = "20260426a1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("bot_instances") as batch_op:
        batch_op.add_column(sa.Column("last_run_at", sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column("last_reconciled_at", sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column("last_signal_at", sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    with op.batch_alter_table("bot_instances") as batch_op:
        batch_op.drop_column("failure_count")
        batch_op.drop_column("last_signal_at")
        batch_op.drop_column("last_reconciled_at")
        batch_op.drop_column("last_run_at")

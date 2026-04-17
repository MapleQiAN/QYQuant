"""add strategy sharing fields

Revision ID: 20260417a1b2
Revises: b8e4d1c2f9a6
Create Date: 2026-04-17 11:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "20260417a1b2"
down_revision = "b8e4d1c2f9a6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("strategies") as batch_op:
        batch_op.add_column(sa.Column("share_mode", sa.String(length=16), nullable=False, server_default="free"))
        batch_op.add_column(sa.Column("import_mode", sa.String(length=16), nullable=False, server_default="sealed"))
        batch_op.add_column(sa.Column("trial_backtest_enabled", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.create_check_constraint("ck_strategies_share_mode_free", "share_mode = 'free'")
        batch_op.create_check_constraint("ck_strategies_import_mode_sealed", "import_mode = 'sealed'")


def downgrade():
    with op.batch_alter_table("strategies") as batch_op:
        batch_op.drop_constraint("ck_strategies_import_mode_sealed", type_="check")
        batch_op.drop_constraint("ck_strategies_share_mode_free", type_="check")
        batch_op.drop_column("trial_backtest_enabled")
        batch_op.drop_column("import_mode")
        batch_op.drop_column("share_mode")

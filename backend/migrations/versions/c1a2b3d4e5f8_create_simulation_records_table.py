"""create simulation records table

Revision ID: c1a2b3d4e5f8
Revises: c1a2b3d4e5f7
Create Date: 2026-03-23 10:42:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "c1a2b3d4e5f8"
down_revision = "c1a2b3d4e5f7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "simulation_records",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("bot_id", sa.String(), sa.ForeignKey("simulation_bots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("equity", sa.Numeric(18, 2), nullable=False),
        sa.Column("cash", sa.Numeric(18, 2), nullable=False),
        sa.Column("daily_return", sa.Numeric(10, 6), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_simulation_records_bot_id", "simulation_records", ["bot_id"])
    op.create_index("idx_simulation_records_trade_date", "simulation_records", ["bot_id", "trade_date"])


def downgrade():
    op.drop_index("idx_simulation_records_trade_date", table_name="simulation_records")
    op.drop_index("idx_simulation_records_bot_id", table_name="simulation_records")
    op.drop_table("simulation_records")

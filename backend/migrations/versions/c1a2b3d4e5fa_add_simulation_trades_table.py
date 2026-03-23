"""add simulation trades table

Revision ID: c1a2b3d4e5fa
Revises: c1a2b3d4e5f9
Create Date: 2026-03-23 11:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "c1a2b3d4e5fa"
down_revision = "c1a2b3d4e5f9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "simulation_trades",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("bot_id", sa.String(), sa.ForeignKey("simulation_bots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("side", sa.String(length=4), nullable=False),
        sa.Column("price", sa.Numeric(18, 4), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_simulation_trades_bot_id", "simulation_trades", ["bot_id"])


def downgrade():
    op.drop_index("idx_simulation_trades_bot_id", table_name="simulation_trades")
    op.drop_table("simulation_trades")

"""create simulation positions table

Revision ID: c1a2b3d4e5f9
Revises: c1a2b3d4e5f8
Create Date: 2026-03-23 10:43:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "c1a2b3d4e5f9"
down_revision = "c1a2b3d4e5f8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "simulation_positions",
        sa.Column("bot_id", sa.String(), sa.ForeignKey("simulation_bots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("avg_cost", sa.Numeric(18, 4), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("bot_id", "symbol"),
    )


def downgrade():
    op.drop_table("simulation_positions")

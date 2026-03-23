"""create simulation bots table

Revision ID: c1a2b3d4e5f7
Revises: c1a2b3d4e5f6
Create Date: 2026-03-23 10:41:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "c1a2b3d4e5f7"
down_revision = "c1a2b3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "simulation_bots",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("strategy_id", sa.String(), sa.ForeignKey("strategies.id"), nullable=False),
        sa.Column("initial_capital", sa.Numeric(18, 2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'active'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_simulation_bots_user_id", "simulation_bots", ["user_id"])
    op.create_index("idx_simulation_bots_status", "simulation_bots", ["status"])


def downgrade():
    op.drop_index("idx_simulation_bots_status", table_name="simulation_bots")
    op.drop_index("idx_simulation_bots_user_id", table_name="simulation_bots")
    op.drop_table("simulation_bots")

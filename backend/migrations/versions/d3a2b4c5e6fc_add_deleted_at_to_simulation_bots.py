"""add deleted_at to simulation_bots

Revision ID: d3a2b4c5e6fc
Revises: d2a1b3c4e5fd
Create Date: 2026-03-23 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "d3a2b4c5e6fc"
down_revision = "d2a1b3c4e5fd"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "simulation_bots",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_column("simulation_bots", "deleted_at")

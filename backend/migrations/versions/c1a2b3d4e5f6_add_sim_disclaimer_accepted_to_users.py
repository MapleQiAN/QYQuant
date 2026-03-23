"""add sim disclaimer accepted to users

Revision ID: c1a2b3d4e5f6
Revises: b8e4d1c2f9a6
Create Date: 2026-03-23 10:40:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "c1a2b3d4e5f6"
down_revision = "b8e4d1c2f9a6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column(
                "sim_disclaimer_accepted",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            )
        )


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("sim_disclaimer_accepted")

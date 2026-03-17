"""strategy library metadata

Revision ID: f2c7a1b9d4e6
Revises: 8a6d9c1f4b2e
Create Date: 2026-03-17 23:10:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "f2c7a1b9d4e6"
down_revision = "8a6d9c1f4b2e"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("strategies") as batch_op:
        batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("category", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("source", sa.String(length=32), nullable=False, server_default="upload"))
        batch_op.add_column(sa.Column("storage_key", sa.String(), nullable=True))


def downgrade():
    with op.batch_alter_table("strategies") as batch_op:
        batch_op.drop_column("storage_key")
        batch_op.drop_column("source")
        batch_op.drop_column("category")
        batch_op.drop_column("description")

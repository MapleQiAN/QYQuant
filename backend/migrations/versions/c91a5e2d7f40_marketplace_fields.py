"""marketplace fields

Revision ID: c91a5e2d7f40
Revises: f2c7a1b9d4e6
Create Date: 2026-03-17 23:55:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "c91a5e2d7f40"
down_revision = "f2c7a1b9d4e6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("strategies") as batch_op:
        batch_op.add_column(sa.Column("title", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(
            sa.Column("review_status", sa.String(length=32), nullable=False, server_default=sa.text("'pending'"))
        )
        batch_op.add_column(sa.Column("display_metrics", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))

    op.create_index("ix_strategies_category", "strategies", ["category"], unique=False)
    op.create_index(
        "ix_strategies_marketplace_public_verified",
        "strategies",
        ["is_public", "is_verified"],
        unique=False,
        postgresql_where=sa.text("is_public = true"),
        sqlite_where=sa.text("is_public = 1"),
    )
    op.create_index(
        "ix_strategies_marketplace_featured",
        "strategies",
        ["is_featured"],
        unique=False,
        postgresql_where=sa.text("is_featured = true"),
        sqlite_where=sa.text("is_featured = 1"),
    )


def downgrade():
    op.drop_index("ix_strategies_marketplace_featured", table_name="strategies")
    op.drop_index("ix_strategies_marketplace_public_verified", table_name="strategies")
    op.drop_index("ix_strategies_category", table_name="strategies")

    with op.batch_alter_table("strategies") as batch_op:
        batch_op.drop_column("display_metrics")
        batch_op.drop_column("review_status")
        batch_op.drop_column("is_verified")
        batch_op.drop_column("is_featured")
        batch_op.drop_column("is_public")
        batch_op.drop_column("title")

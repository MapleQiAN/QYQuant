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


def _column_names(bind, table_name):
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def _index_names(bind, table_name):
    inspector = sa.inspect(bind)
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade():
    bind = op.get_bind()
    columns = _column_names(bind, "strategies")

    with op.batch_alter_table("strategies") as batch_op:
        if "title" not in columns:
            batch_op.add_column(sa.Column("title", sa.String(), nullable=True))

        if "is_public" not in columns:
            batch_op.add_column(sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false()))

        if "is_featured" not in columns:
            batch_op.add_column(sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.false()))

        if "is_verified" not in columns:
            batch_op.add_column(sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()))

        if "review_status" not in columns:
            batch_op.add_column(
                sa.Column("review_status", sa.String(length=32), nullable=False, server_default=sa.text("'pending'"))
            )

        if "display_metrics" not in columns:
            batch_op.add_column(sa.Column("display_metrics", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))

    indexes = _index_names(bind, "strategies")
    if "ix_strategies_category" not in indexes:
        op.create_index("ix_strategies_category", "strategies", ["category"], unique=False)

    if "ix_strategies_marketplace_public_verified" not in indexes:
        op.create_index(
            "ix_strategies_marketplace_public_verified",
            "strategies",
            ["is_public", "is_verified"],
            unique=False,
            postgresql_where=sa.text("is_public = true"),
            sqlite_where=sa.text("is_public = 1"),
        )

    if "ix_strategies_marketplace_featured" not in indexes:
        op.create_index(
            "ix_strategies_marketplace_featured",
            "strategies",
            ["is_featured"],
            unique=False,
            postgresql_where=sa.text("is_featured = true"),
            sqlite_where=sa.text("is_featured = 1"),
        )


def downgrade():
    bind = op.get_bind()
    indexes = _index_names(bind, "strategies")
    columns = _column_names(bind, "strategies")

    if "ix_strategies_marketplace_featured" in indexes:
        op.drop_index("ix_strategies_marketplace_featured", table_name="strategies")

    if "ix_strategies_marketplace_public_verified" in indexes:
        op.drop_index("ix_strategies_marketplace_public_verified", table_name="strategies")

    if "ix_strategies_category" in indexes:
        op.drop_index("ix_strategies_category", table_name="strategies")

    with op.batch_alter_table("strategies") as batch_op:
        if "display_metrics" in columns:
            batch_op.drop_column("display_metrics")

        if "review_status" in columns:
            batch_op.drop_column("review_status")

        if "is_verified" in columns:
            batch_op.drop_column("is_verified")

        if "is_featured" in columns:
            batch_op.drop_column("is_featured")

        if "is_public" in columns:
            batch_op.drop_column("is_public")

        if "title" in columns:
            batch_op.drop_column("title")

"""add strategy import drafts

Revision ID: 6f0c1cf637c2
Revises: e9f1a2b3c4d5
Create Date: 2026-03-28 22:58:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "6f0c1cf637c2"
down_revision = "e9f1a2b3c4d5"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("strategies") as batch_op:
        batch_op.add_column(sa.Column("original_source_file_id", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("built_package_file_id", sa.String(), nullable=True))
        batch_op.create_foreign_key(
            "fk_strategies_original_source_file_id_files",
            "files",
            ["original_source_file_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_strategies_built_package_file_id_files",
            "files",
            ["built_package_file_id"],
            ["id"],
        )

    op.create_table(
        "strategy_import_drafts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("source_file_id", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="analyzed"),
        sa.Column("analysis_payload", sa.JSON(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["source_file_id"], ["files.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_strategy_import_drafts_owner_status",
        "strategy_import_drafts",
        ["owner_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_strategy_import_drafts_expires_at",
        "strategy_import_drafts",
        ["expires_at"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_strategy_import_drafts_expires_at", table_name="strategy_import_drafts")
    op.drop_index("ix_strategy_import_drafts_owner_status", table_name="strategy_import_drafts")
    op.drop_table("strategy_import_drafts")

    with op.batch_alter_table("strategies") as batch_op:
        batch_op.drop_constraint("fk_strategies_built_package_file_id_files", type_="foreignkey")
        batch_op.drop_constraint("fk_strategies_original_source_file_id_files", type_="foreignkey")
        batch_op.drop_column("built_package_file_id")
        batch_op.drop_column("original_source_file_id")

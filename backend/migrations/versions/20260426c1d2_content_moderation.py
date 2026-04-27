"""add content moderation tables and columns

Revision ID: 20260426c1d2
Revises: 20260426b1c2
Create Date: 2026-04-26 00:00:02.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "20260426c1d2"
down_revision = "20260426b1c2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sensitive_words",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("word", sa.String(), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("level", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("word"),
    )
    op.create_index("ix_sensitive_words_category", "sensitive_words", ["category"])
    op.create_index("ix_sensitive_words_is_active", "sensitive_words", ["is_active"])

    op.create_table(
        "user_moderation_records",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_id", sa.String(), nullable=False),
        sa.Column("matched_words", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("action_taken", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_moderation_records_user_id", "user_moderation_records", ["user_id"])
    op.create_index("ix_user_moderation_records_created_at", "user_moderation_records", ["created_at"])

    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("warning_count", sa.Integer(), nullable=False, server_default="0"))

    with op.batch_alter_table("posts") as batch_op:
        batch_op.add_column(sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.text("false")))

    with op.batch_alter_table("post_comments") as batch_op:
        batch_op.add_column(sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.text("false")))


def downgrade() -> None:
    with op.batch_alter_table("post_comments") as batch_op:
        batch_op.drop_column("is_hidden")

    with op.batch_alter_table("posts") as batch_op:
        batch_op.drop_column("is_hidden")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("warning_count")

    op.drop_index("ix_user_moderation_records_created_at", table_name="user_moderation_records")
    op.drop_index("ix_user_moderation_records_user_id", table_name="user_moderation_records")
    op.drop_table("user_moderation_records")

    op.drop_index("ix_sensitive_words_is_active", table_name="sensitive_words")
    op.drop_index("ix_sensitive_words_category", table_name="sensitive_words")
    op.drop_table("sensitive_words")

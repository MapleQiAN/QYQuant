"""post comments

Revision ID: c4f6a8b1d2e3
Revises: b2e4c6d8f1a3
Create Date: 2026-03-20 16:36:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "c4f6a8b1d2e3"
down_revision = "b2e4c6d8f1a3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "post_comments",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("post_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_post_comments_post_id", "post_comments", ["post_id"], unique=False)
    op.create_index("ix_post_comments_created_at", "post_comments", ["created_at"], unique=False)


def downgrade():
    op.drop_index("ix_post_comments_created_at", table_name="post_comments")
    op.drop_index("ix_post_comments_post_id", table_name="post_comments")
    op.drop_table("post_comments")

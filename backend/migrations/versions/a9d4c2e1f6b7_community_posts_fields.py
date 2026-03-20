"""community posts fields

Revision ID: a9d4c2e1f6b7
Revises: f7b3c2d1e9a0
Create Date: 2026-03-20 16:25:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "a9d4c2e1f6b7"
down_revision = "f7b3c2d1e9a0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("posts", sa.Column("content", sa.Text(), nullable=True))
    op.add_column("posts", sa.Column("strategy_id", sa.String(), nullable=True))
    op.add_column("posts", sa.Column("likes_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("posts", sa.Column("comments_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("posts", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        "fk_posts_strategy_id_strategies",
        "posts",
        "strategies",
        ["strategy_id"],
        ["id"],
    )
    op.create_index("idx_posts_created_at", "posts", ["created_at"], unique=False)
    op.create_index("idx_posts_user_id", "posts", ["user_id"], unique=False)


def downgrade():
    op.drop_index("idx_posts_user_id", table_name="posts")
    op.drop_index("idx_posts_created_at", table_name="posts")
    op.drop_constraint("fk_posts_strategy_id_strategies", "posts", type_="foreignkey")
    op.drop_column("posts", "created_at")
    op.drop_column("posts", "comments_count")
    op.drop_column("posts", "likes_count")
    op.drop_column("posts", "strategy_id")
    op.drop_column("posts", "content")

"""post interactions

Revision ID: b2e4c6d8f1a3
Revises: a9d4c2e1f6b7
Create Date: 2026-03-20 16:35:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "b2e4c6d8f1a3"
down_revision = "a9d4c2e1f6b7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "post_interactions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("post_id", sa.String(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "post_id", "type", name="uq_post_interactions_user_post_type"),
    )
    op.create_index("ix_post_interactions_user_id", "post_interactions", ["user_id"], unique=False)
    op.create_index("ix_post_interactions_post_id", "post_interactions", ["post_id"], unique=False)


def downgrade():
    op.drop_index("ix_post_interactions_post_id", table_name="post_interactions")
    op.drop_index("ix_post_interactions_user_id", table_name="post_interactions")
    op.drop_table("post_interactions")

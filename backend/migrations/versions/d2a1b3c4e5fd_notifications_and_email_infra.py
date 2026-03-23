"""notifications and email infra

Revision ID: d2a1b3c4e5fd
Revises: c1a2b3d4e5fb, c3d9e1f7a2b4, c4f6a8b1d2e3
Create Date: 2026-03-23 18:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "d2a1b3c4e5fd"
down_revision = ("c1a2b3d4e5fb", "c3d9e1f7a2b4", "c4f6a8b1d2e3")
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("email", sa.String(length=255), nullable=True))
        batch_op.create_unique_constraint("uq_users_email_v2", ["email"])

    try:
        op.drop_index("ix_notifications_user_unread", table_name="notifications")
    except Exception:
        pass
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"], unique=False)
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"], unique=False)


def downgrade():
    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.create_index(
        "ix_notifications_user_unread",
        "notifications",
        ["user_id", "is_read"],
        unique=False,
        postgresql_where=sa.text("is_read = false"),
    )

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("uq_users_email_v2", type_="unique")
        batch_op.drop_column("email")

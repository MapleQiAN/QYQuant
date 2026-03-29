"""Rename plan levels: lite→plus, expert→ultra; add go tier

Revision ID: b5c3d2e1f7a9
Revises: f4a9b8c7d6e5
Create Date: 2026-03-30

"""
from alembic import op

revision = 'b5c3d2e1f7a9'
down_revision = 'f4a9b8c7d6e5'
branch_labels = None
depends_on = None

_TABLES = ('users', 'user_quota', 'payment_orders', 'subscriptions')


def upgrade():
    for table in _TABLES:
        op.execute(f"UPDATE {table} SET plan_level = 'plus'  WHERE plan_level = 'lite'")
        op.execute(f"UPDATE {table} SET plan_level = 'ultra' WHERE plan_level = 'expert'")


def downgrade():
    for table in _TABLES:
        op.execute(f"UPDATE {table} SET plan_level = 'lite'   WHERE plan_level = 'plus'")
        op.execute(f"UPDATE {table} SET plan_level = 'expert' WHERE plan_level = 'ultra'")

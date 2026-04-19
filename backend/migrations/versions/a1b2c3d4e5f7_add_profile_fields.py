"""Add profile fields to users

Revision ID: a1b2c3d4e5f7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-19
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('location', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('website_url', sa.String(500), nullable=True))
    op.add_column('users', sa.Column('trading_experience', sa.String(32), nullable=True))
    op.add_column('users', sa.Column('preferred_markets', sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'preferred_markets')
    op.drop_column('users', 'trading_experience')
    op.drop_column('users', 'website_url')
    op.drop_column('users', 'location')

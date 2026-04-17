"""oauth_identities table

Revision ID: 20260418d4e5f
Revises: 20260418c1d2
Create Date: 2026-04-18 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260418d4e5f"
down_revision = "20260418c1d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'oauth_identities',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('provider', sa.String(32), nullable=False),
        sa.Column('provider_user_id', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('display_name', sa.String(200), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('raw_profile', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'provider_user_id', name='uq_oauth_provider_user_id'),
    )
    op.create_index('ix_oauth_identities_user_id', 'oauth_identities', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_oauth_identities_user_id', table_name='oauth_identities')
    op.drop_table('oauth_identities')

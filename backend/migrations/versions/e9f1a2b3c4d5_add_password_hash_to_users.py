"""add password hash to users

Revision ID: e9f1a2b3c4d5
Revises: 151c20bfc314, d3a2b4c5e6fc
Create Date: 2026-03-28 19:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = 'e9f1a2b3c4d5'
down_revision = ('151c20bfc314', 'd3a2b4c5e6fc')
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('password_hash', sa.String(length=255), nullable=True))
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
    )


def downgrade():
    op.drop_table('password_reset_tokens')
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('password_hash')

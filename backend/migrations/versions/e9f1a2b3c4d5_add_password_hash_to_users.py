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


def downgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('password_hash')

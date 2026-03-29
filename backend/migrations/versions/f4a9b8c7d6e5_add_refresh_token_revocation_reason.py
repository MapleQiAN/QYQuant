"""add refresh token revocation reason

Revision ID: f4a9b8c7d6e5
Revises: e9f1a2b3c4d5
Create Date: 2026-03-28 22:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = 'f4a9b8c7d6e5'
down_revision = 'e9f1a2b3c4d5'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('refresh_tokens') as batch_op:
        batch_op.add_column(sa.Column('revoked_reason', sa.String(length=32), nullable=True))


def downgrade():
    with op.batch_alter_table('refresh_tokens') as batch_op:
        batch_op.drop_column('revoked_reason')

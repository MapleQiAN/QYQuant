"""strategy encrypted source storage

Revision ID: 8a6d9c1f4b2e
Revises: 4d2f6b3a9c1e
Create Date: 2026-03-17 21:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = '8a6d9c1f4b2e'
down_revision = '4d2f6b3a9c1e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('strategies') as batch_op:
        batch_op.add_column(sa.Column('code_encrypted', sa.LargeBinary(), nullable=True))
        batch_op.add_column(sa.Column('code_hash', sa.String(length=64), nullable=True))


def downgrade():
    with op.batch_alter_table('strategies') as batch_op:
        batch_op.drop_column('code_hash')
        batch_op.drop_column('code_encrypted')

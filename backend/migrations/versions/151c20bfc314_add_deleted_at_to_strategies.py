"""add_deleted_at_to_strategies

Revision ID: 151c20bfc314
Revises: 80232243db31
Create Date: 2026-03-27 14:39:48.983494

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '151c20bfc314'
down_revision = '80232243db31'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('strategies', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    with op.batch_alter_table('strategies', schema=None) as batch_op:
        batch_op.drop_column('deleted_at')

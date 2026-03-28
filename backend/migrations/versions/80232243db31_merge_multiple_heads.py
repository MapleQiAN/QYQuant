"""merge_multiple_heads

Revision ID: 80232243db31
Revises: a4c9d2e1f6b7, d3a2b4c5e6fc, e4b1c2d3f4a5
Create Date: 2026-03-27 14:36:14.388538

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '80232243db31'
down_revision = ('a4c9d2e1f6b7', 'd3a2b4c5e6fc', 'e4b1c2d3f4a5')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

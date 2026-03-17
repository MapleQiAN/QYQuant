"""market data cache

Revision ID: 6f3c2d1b8a7e
Revises: 4d2f6b3a9c1e
Create Date: 2026-03-17 20:40:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = '6f3c2d1b8a7e'
down_revision = '4d2f6b3a9c1e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'market_data_cache',
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('trade_date', sa.Date(), nullable=False),
        sa.Column('open', sa.Numeric(18, 6), nullable=False),
        sa.Column('high', sa.Numeric(18, 6), nullable=False),
        sa.Column('low', sa.Numeric(18, 6), nullable=False),
        sa.Column('close', sa.Numeric(18, 6), nullable=False),
        sa.Column('volume', sa.BigInteger(), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=False, server_default='joinquant'),
        sa.Column('cached_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('symbol', 'trade_date'),
    )
    op.execute(
        'CREATE INDEX ix_market_data_cache_symbol_trade_date_desc '
        'ON market_data_cache (symbol, trade_date DESC)'
    )


def downgrade():
    op.drop_index('ix_market_data_cache_symbol_trade_date_desc', table_name='market_data_cache')
    op.drop_table('market_data_cache')

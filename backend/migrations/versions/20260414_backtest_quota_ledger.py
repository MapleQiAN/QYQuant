"""add backtest quota ledger

Revision ID: 20260414_backtest_quota_ledger
Revises: a1b2c3d4e5f0
Create Date: 2026-04-14 17:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = '20260414_backtest_quota_ledger'
down_revision = 'a1b2c3d4e5f0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'backtest_quota_ledger',
        sa.Column('job_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='reserved'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('finalized_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['backtest_jobs.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('job_id'),
    )
    op.create_index(
        'ix_backtest_quota_ledger_user_id_status',
        'backtest_quota_ledger',
        ['user_id', 'status'],
        unique=False,
    )


def downgrade():
    op.drop_index('ix_backtest_quota_ledger_user_id_status', table_name='backtest_quota_ledger')
    op.drop_table('backtest_quota_ledger')

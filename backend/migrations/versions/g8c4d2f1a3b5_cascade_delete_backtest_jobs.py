"""cascade delete backtest_jobs

Revision ID: g8c4d2f1a3b5
Revises: f7b3c2d1e9a0
Create Date: 2026-04-16 08:00:00.000000

"""
from alembic import op


revision = 'g8c4d2f1a3b5'
down_revision = '20260414_backtest_quota_ledger'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # backtest_trades.backtest_id -> backtest_jobs.id ON DELETE CASCADE
    op.drop_constraint('backtest_trades_backtest_id_fkey', 'backtest_trades', type_='foreignkey')
    op.create_foreign_key(
        'backtest_trades_backtest_id_fkey',
        'backtest_trades', 'backtest_jobs',
        ['backtest_id'], ['id'],
        ondelete='CASCADE',
    )

    # backtest_quota_ledger.job_id -> backtest_jobs.id ON DELETE CASCADE
    op.drop_constraint('backtest_quota_ledger_job_id_fkey', 'backtest_quota_ledger', type_='foreignkey')
    op.create_foreign_key(
        'backtest_quota_ledger_job_id_fkey',
        'backtest_quota_ledger', 'backtest_jobs',
        ['job_id'], ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint('backtest_quota_ledger_job_id_fkey', 'backtest_quota_ledger', type_='foreignkey')
    op.create_foreign_key(
        'backtest_quota_ledger_job_id_fkey',
        'backtest_quota_ledger', 'backtest_jobs',
        ['job_id'], ['id'],
    )

    op.drop_constraint('backtest_trades_backtest_id_fkey', 'backtest_trades', type_='foreignkey')
    op.create_foreign_key(
        'backtest_trades_backtest_id_fkey',
        'backtest_trades', 'backtest_jobs',
        ['backtest_id'], ['id'],
    )

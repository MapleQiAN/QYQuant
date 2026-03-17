"""backtest jobs infrastructure

Revision ID: 4d2f6b3a9c1e
Revises: 3b1d8f6c2a4e
Create Date: 2026-03-17 18:20:00.000000

"""

from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


revision = '4d2f6b3a9c1e'
down_revision = '3b1d8f6c2a4e'
branch_labels = None
depends_on = None


status_enum = sa.Enum(
    'pending',
    'running',
    'completed',
    'failed',
    'timeout',
    name='backtest_job_status',
    native_enum=False,
)


def _ms_to_utc(value):
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)


def _normalize_status(value):
    if value in {'pending', 'running', 'completed', 'failed', 'timeout'}:
        return value
    return 'completed' if value == 'success' else 'failed'


def upgrade():
    op.rename_table('backtests', 'backtest_jobs')

    with op.batch_alter_table('backtest_jobs') as batch_op:
        batch_op.add_column(sa.Column('strategy_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('params', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('result_summary', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('result_storage_key', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('error_message', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('started_at_v2', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('created_at_v2', sa.DateTime(timezone=True), nullable=True))

    connection = op.get_bind()
    backtest_jobs = sa.table(
        'backtest_jobs',
        sa.column('id', sa.String()),
        sa.column('name', sa.String()),
        sa.column('symbol', sa.String()),
        sa.column('status', sa.String()),
        sa.column('started_at', sa.BigInteger()),
        sa.column('finished_at', sa.BigInteger()),
        sa.column('summary', sa.JSON()),
        sa.column('job_id', sa.String()),
        sa.column('created_at', sa.BigInteger()),
        sa.column('params', sa.JSON()),
        sa.column('result_summary', sa.JSON()),
        sa.column('result_storage_key', sa.Text()),
        sa.column('started_at_v2', sa.DateTime(timezone=True)),
        sa.column('completed_at', sa.DateTime(timezone=True)),
        sa.column('created_at_v2', sa.DateTime(timezone=True)),
    )

    rows = connection.execute(
        sa.select(
            backtest_jobs.c.id,
            backtest_jobs.c.name,
            backtest_jobs.c.symbol,
            backtest_jobs.c.status,
            backtest_jobs.c.started_at,
            backtest_jobs.c.finished_at,
            backtest_jobs.c.summary,
            backtest_jobs.c.job_id,
            backtest_jobs.c.created_at,
        )
    ).mappings().all()

    for row in rows:
        created_at = _ms_to_utc(row['created_at']) or _ms_to_utc(row['started_at']) or datetime.now(timezone.utc)
        connection.execute(
            backtest_jobs.update()
            .where(backtest_jobs.c.id == row['id'])
            .values(
                status=_normalize_status(row['status']),
                params={
                    'name': row['name'],
                    'symbol': row['symbol'],
                },
                result_summary=row['summary'],
                result_storage_key=row['job_id'],
                started_at_v2=_ms_to_utc(row['started_at']),
                completed_at=_ms_to_utc(row['finished_at']),
                created_at_v2=created_at,
            )
        )

    with op.batch_alter_table('backtest_jobs') as batch_op:
        batch_op.alter_column('status', existing_type=sa.String(), type_=status_enum, nullable=False)
        batch_op.create_foreign_key(
            'fk_backtest_jobs_strategy_id_strategies',
            'strategies',
            ['strategy_id'],
            ['id'],
        )
        batch_op.drop_column('name')
        batch_op.drop_column('symbol')
        batch_op.drop_column('finished_at')
        batch_op.drop_column('summary')
        batch_op.drop_column('job_id')
        batch_op.drop_column('started_at')
        batch_op.drop_column('created_at')
        batch_op.drop_column('updated_at')
        batch_op.alter_column('started_at_v2', new_column_name='started_at')
        batch_op.alter_column('created_at_v2', new_column_name='created_at')

    op.create_index('ix_backtest_jobs_user_id_created_at', 'backtest_jobs', ['user_id', 'created_at'])
    op.create_index('ix_backtest_jobs_status', 'backtest_jobs', ['status'])
    op.create_index('ix_backtest_jobs_strategy_id', 'backtest_jobs', ['strategy_id'])

    op.create_table(
        'user_quota',
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('plan_level', sa.String(length=32), nullable=False, server_default='free'),
        sa.Column('used_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reset_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('user_id'),
    )


def downgrade():
    op.drop_table('user_quota')
    op.drop_index('ix_backtest_jobs_strategy_id', table_name='backtest_jobs')
    op.drop_index('ix_backtest_jobs_status', table_name='backtest_jobs')
    op.drop_index('ix_backtest_jobs_user_id_created_at', table_name='backtest_jobs')

    with op.batch_alter_table('backtest_jobs') as batch_op:
        batch_op.add_column(sa.Column('name', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('symbol', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('finished_at', sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column('summary', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('job_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('started_at_v1', sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column('created_at_v1', sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.BigInteger(), nullable=True))

    connection = op.get_bind()
    backtest_jobs = sa.table(
        'backtest_jobs',
        sa.column('id', sa.String()),
        sa.column('params', sa.JSON()),
        sa.column('result_summary', sa.JSON()),
        sa.column('result_storage_key', sa.Text()),
        sa.column('started_at', sa.DateTime(timezone=True)),
        sa.column('completed_at', sa.DateTime(timezone=True)),
        sa.column('created_at', sa.DateTime(timezone=True)),
        sa.column('name', sa.String()),
        sa.column('symbol', sa.String()),
        sa.column('finished_at', sa.BigInteger()),
        sa.column('summary', sa.JSON()),
        sa.column('job_id', sa.String()),
        sa.column('started_at_v1', sa.BigInteger()),
        sa.column('created_at_v1', sa.BigInteger()),
        sa.column('updated_at', sa.BigInteger()),
    )

    rows = connection.execute(
        sa.select(
            backtest_jobs.c.id,
            backtest_jobs.c.params,
            backtest_jobs.c.result_summary,
            backtest_jobs.c.result_storage_key,
            backtest_jobs.c.started_at,
            backtest_jobs.c.completed_at,
            backtest_jobs.c.created_at,
        )
    ).mappings().all()

    for row in rows:
        params = row['params'] or {}
        connection.execute(
            backtest_jobs.update()
            .where(backtest_jobs.c.id == row['id'])
            .values(
                name=params.get('name') or 'legacy-backtest',
                symbol=params.get('symbol') or 'N/A',
                finished_at=int(row['completed_at'].timestamp() * 1000) if row['completed_at'] else None,
                summary=row['result_summary'],
                job_id=row['result_storage_key'],
                started_at_v1=int(row['started_at'].timestamp() * 1000) if row['started_at'] else 0,
                created_at_v1=int(row['created_at'].timestamp() * 1000) if row['created_at'] else 0,
                updated_at=int(row['completed_at'].timestamp() * 1000) if row['completed_at'] else None,
            )
        )

    with op.batch_alter_table('backtest_jobs') as batch_op:
        batch_op.drop_constraint('fk_backtest_jobs_strategy_id_strategies', type_='foreignkey')
        batch_op.alter_column('status', existing_type=status_enum, type_=sa.String(), nullable=False)
        batch_op.drop_column('strategy_id')
        batch_op.drop_column('params')
        batch_op.drop_column('result_summary')
        batch_op.drop_column('result_storage_key')
        batch_op.drop_column('error_message')
        batch_op.drop_column('completed_at')
        batch_op.drop_column('started_at')
        batch_op.drop_column('created_at')
        batch_op.alter_column('started_at_v1', new_column_name='started_at')
        batch_op.alter_column('created_at_v1', new_column_name='created_at')

    op.rename_table('backtest_jobs', 'backtests')

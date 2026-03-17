"""phone auth

Revision ID: 3b1d8f6c2a4e
Revises: bab2ec6fb654
Create Date: 2026-03-17 11:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = '3b1d8f6c2a4e'
down_revision = 'bab2ec6fb654'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('jti', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('jti'),
        sa.UniqueConstraint('token_hash'),
    )

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('operator_id', sa.String(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=False),
        sa.Column('target_id', sa.String(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['operator_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('phone', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('nickname', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('avatar_url', sa.String(), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('bio', sa.String(length=200), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('role', sa.String(length=32), nullable=False, server_default='user'))
        batch_op.add_column(sa.Column('plan_level', sa.String(length=32), nullable=False, server_default='free'))
        batch_op.add_column(sa.Column('is_banned', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('onboarding_completed', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('created_at_v2', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
        batch_op.add_column(sa.Column('updated_at_v2', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))

    op.execute("UPDATE users SET nickname = COALESCE(name, '用户')")
    op.execute("UPDATE users SET avatar_url = COALESCE(avatar, '')")
    op.execute("UPDATE users SET plan_level = COALESCE(level, 'free')")

    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('nickname', existing_type=sa.String(length=200), nullable=False)
        batch_op.create_unique_constraint('uq_users_phone', ['phone'])
        batch_op.drop_column('email')
        batch_op.drop_column('name')
        batch_op.drop_column('avatar')
        batch_op.drop_column('level')
        batch_op.drop_column('notifications')
        batch_op.drop_column('password_hash')
        batch_op.drop_column('api_key_encrypted')
        batch_op.drop_column('broker_key_encrypted')
        batch_op.drop_column('created_at')
        batch_op.drop_column('updated_at')
        batch_op.alter_column('created_at_v2', new_column_name='created_at')
        batch_op.alter_column('updated_at_v2', new_column_name='updated_at')


def downgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('updated_at', sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column('created_at', sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column('broker_key_encrypted', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('api_key_encrypted', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('password_hash', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('notifications', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('level', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('avatar', sa.String(), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('name', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('email', sa.String(), nullable=True))
        batch_op.drop_constraint('uq_users_phone', type_='unique')
        batch_op.drop_column('phone')
        batch_op.drop_column('nickname')
        batch_op.drop_column('avatar_url')
        batch_op.drop_column('bio')
        batch_op.drop_column('role')
        batch_op.drop_column('plan_level')
        batch_op.drop_column('is_banned')
        batch_op.drop_column('onboarding_completed')
        batch_op.drop_column('deleted_at')
        batch_op.drop_column('created_at')
        batch_op.drop_column('updated_at')

    op.execute("UPDATE users SET name = 'Admin' WHERE name IS NULL")
    op.execute("UPDATE users SET email = id || '@legacy.local' WHERE email IS NULL")
    op.execute("UPDATE users SET password_hash = '' WHERE password_hash IS NULL")

    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('name', existing_type=sa.String(), nullable=False)
        batch_op.alter_column('email', existing_type=sa.String(), nullable=False)
        batch_op.alter_column('password_hash', existing_type=sa.String(), nullable=False)
        batch_op.create_unique_constraint('uq_users_email', ['email'])

    op.drop_table('audit_logs')
    op.drop_table('refresh_tokens')

"""managed bot snapshots and ownership fields

Revision ID: 20260418c1d2
Revises: z9a1b2c3d4e5
Create Date: 2026-04-18 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260418c1d2"
down_revision = "z9a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("bot_instances") as batch_op:
        batch_op.add_column(sa.Column("strategy_id", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("integration_id", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("last_error_message", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_foreign_key("fk_bot_instances_strategy_id", "strategies", ["strategy_id"], ["id"])
        batch_op.create_foreign_key("fk_bot_instances_integration_id", "user_integrations", ["integration_id"], ["id"])

    op.create_index("ix_bot_instances_user_status", "bot_instances", ["user_id", "status"], unique=False)
    op.create_index("ix_bot_instances_strategy_id", "bot_instances", ["strategy_id"], unique=False)
    op.create_index("ix_bot_instances_integration_id", "bot_instances", ["integration_id"], unique=False)

    op.create_table(
        "bot_equity_snapshots",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("bot_id", sa.String(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("equity", sa.Numeric(18, 2), nullable=False),
        sa.Column("available_cash", sa.Numeric(18, 2), nullable=False),
        sa.Column("position_value", sa.Numeric(18, 2), nullable=False),
        sa.Column("total_profit", sa.Numeric(18, 2), nullable=False),
        sa.Column("total_return_rate", sa.Numeric(12, 6), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["bot_id"], ["bot_instances.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bot_id", "snapshot_date", name="uq_bot_equity_snapshot_date"),
    )
    op.create_index("ix_bot_equity_snapshots_bot_date", "bot_equity_snapshots", ["bot_id", "snapshot_date"], unique=False)


def downgrade():
    op.drop_index("ix_bot_equity_snapshots_bot_date", table_name="bot_equity_snapshots")
    op.drop_table("bot_equity_snapshots")

    op.drop_index("ix_bot_instances_integration_id", table_name="bot_instances")
    op.drop_index("ix_bot_instances_strategy_id", table_name="bot_instances")
    op.drop_index("ix_bot_instances_user_status", table_name="bot_instances")

    with op.batch_alter_table("bot_instances") as batch_op:
        batch_op.drop_constraint("fk_bot_instances_integration_id", type_="foreignkey")
        batch_op.drop_constraint("fk_bot_instances_strategy_id", type_="foreignkey")
        batch_op.drop_column("deleted_at")
        batch_op.drop_column("last_error_message")
        batch_op.drop_column("integration_id")
        batch_op.drop_column("strategy_id")

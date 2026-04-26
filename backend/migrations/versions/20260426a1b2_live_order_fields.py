"""add live order fields

Revision ID: 20260426a1b2
Revises: z9a1b2c3d4e5, b1c2d3e4f5a6
Create Date: 2026-04-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "20260426a1b2"
down_revision = ("z9a1b2c3d4e5", "b1c2d3e4f5a6")
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("orders") as batch_op:
        batch_op.add_column(sa.Column("integration_id", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("strategy_id", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("broker_order_id", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("order_type", sa.String(length=16), nullable=True))
        batch_op.add_column(sa.Column("limit_price", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("filled_quantity", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("filled_avg_price", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("submitted_at", sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column("filled_at", sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column("rejected_reason", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("raw_broker_payload", sa.JSON(), nullable=True))
        batch_op.create_foreign_key("fk_orders_integration_id", "user_integrations", ["integration_id"], ["id"])
        batch_op.create_foreign_key("fk_orders_strategy_id", "strategies", ["strategy_id"], ["id"])
        batch_op.create_index("ix_orders_integration_id", ["integration_id"], unique=False)
        batch_op.create_index("ix_orders_strategy_id", ["strategy_id"], unique=False)
        batch_op.create_index("ix_orders_broker_order_id", ["broker_order_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("orders") as batch_op:
        batch_op.drop_index("ix_orders_broker_order_id")
        batch_op.drop_index("ix_orders_strategy_id")
        batch_op.drop_index("ix_orders_integration_id")
        batch_op.drop_constraint("fk_orders_strategy_id", type_="foreignkey")
        batch_op.drop_constraint("fk_orders_integration_id", type_="foreignkey")
        batch_op.drop_column("raw_broker_payload")
        batch_op.drop_column("rejected_reason")
        batch_op.drop_column("filled_at")
        batch_op.drop_column("submitted_at")
        batch_op.drop_column("filled_avg_price")
        batch_op.drop_column("filled_quantity")
        batch_op.drop_column("limit_price")
        batch_op.drop_column("order_type")
        batch_op.drop_column("broker_order_id")
        batch_op.drop_column("strategy_id")
        batch_op.drop_column("integration_id")

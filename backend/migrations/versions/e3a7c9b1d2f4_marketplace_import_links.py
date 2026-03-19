"""marketplace import links

Revision ID: e3a7c9b1d2f4
Revises: d8f1a2c3b4e5
Create Date: 2026-03-18 17:15:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "e3a7c9b1d2f4"
down_revision = "d8f1a2c3b4e5"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("strategies") as batch_op:
        batch_op.add_column(sa.Column("source_strategy_id", sa.String(), nullable=True))
        batch_op.create_foreign_key(
            "fk_strategies_source_strategy_id",
            "strategies",
            ["source_strategy_id"],
            ["id"],
        )
        batch_op.create_unique_constraint(
            "uq_user_imported_strategy",
            ["owner_id", "source_strategy_id"],
        )


def downgrade():
    with op.batch_alter_table("strategies") as batch_op:
        batch_op.drop_constraint("uq_user_imported_strategy", type_="unique")
        batch_op.drop_constraint("fk_strategies_source_strategy_id", type_="foreignkey")
        batch_op.drop_column("source_strategy_id")

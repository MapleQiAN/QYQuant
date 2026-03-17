"""strategy parameter presets

Revision ID: a5c1d2e3f4b5
Revises: f2c7a1b9d4e6
Create Date: 2026-03-17 23:50:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "a5c1d2e3f4b5"
down_revision = "f2c7a1b9d4e6"
branch_labels = None
depends_on = None


json_type = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade():
    op.create_table(
        "strategy_parameter_presets",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("strategy_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("parameters", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_strategy_parameter_presets_strategy_user",
        "strategy_parameter_presets",
        ["strategy_id", "user_id"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_strategy_parameter_presets_strategy_user", table_name="strategy_parameter_presets")
    op.drop_table("strategy_parameter_presets")

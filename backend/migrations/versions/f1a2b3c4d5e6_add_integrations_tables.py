"""add integrations tables

Revision ID: f1a2b3c4d5e6
Revises: d3a2b4c5e6fc
Create Date: 2026-03-30 11:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "f1a2b3c4d5e6"
down_revision = "d3a2b4c5e6fc"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "integration_providers",
        sa.Column("key", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column("config_schema", sa.JSON(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "user_integrations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider_key", sa.String(length=64), sa.ForeignKey("integration_providers.key"), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("config_public", sa.JSON(), nullable=False),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_user_integrations_user_status", "user_integrations", ["user_id", "status"])
    op.create_index("ix_user_integrations_provider_key", "user_integrations", ["provider_key"])
    op.create_table(
        "user_integration_secrets",
        sa.Column("integration_id", sa.String(), sa.ForeignKey("user_integrations.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("encrypted_payload", sa.Text(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table("user_integration_secrets")
    op.drop_index("ix_user_integrations_provider_key", table_name="user_integrations")
    op.drop_index("ix_user_integrations_user_status", table_name="user_integrations")
    op.drop_table("user_integrations")
    op.drop_table("integration_providers")

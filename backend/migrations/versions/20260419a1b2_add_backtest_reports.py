"""add backtest reports

Revision ID: 20260419a1b2
Revises: 20260418d4e5f
Create Date: 2026-04-19 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260419a1b2"
down_revision = "20260418d4e5f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "backtest_reports",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("backtest_job_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("equity_curve", sa.JSON(), nullable=True),
        sa.Column("drawdown_series", sa.JSON(), nullable=True),
        sa.Column("monthly_returns", sa.JSON(), nullable=True),
        sa.Column("trade_details", sa.JSON(), nullable=True),
        sa.Column("anomalies", sa.JSON(), nullable=True),
        sa.Column("parameter_sensitivity", sa.JSON(), nullable=True),
        sa.Column("monte_carlo", sa.JSON(), nullable=True),
        sa.Column("regime_analysis", sa.JSON(), nullable=True),
        sa.Column("metric_narrations", sa.JSON(), nullable=True),
        sa.Column("executive_summary", sa.Text(), nullable=True),
        sa.Column("diagnosis_narration", sa.Text(), nullable=True),
        sa.Column("advisor_narration", sa.Text(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["backtest_job_id"], ["backtest_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("backtest_job_id", name="uq_report_job"),
    )
    op.create_index(
        "ix_backtest_reports_user_id_created_at",
        "backtest_reports",
        ["user_id", "created_at"],
    )
    op.create_index("ix_backtest_reports_status", "backtest_reports", ["status"])

    op.create_table(
        "report_chat_messages",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("report_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["report_id"], ["backtest_reports.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_report_chat_messages_report_id_created_at",
        "report_chat_messages",
        ["report_id", "created_at"],
    )

    op.create_table(
        "report_alerts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("report_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["report_id"], ["backtest_reports.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_report_alerts_report_id_status", "report_alerts", ["report_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_report_alerts_report_id_status", table_name="report_alerts")
    op.drop_table("report_alerts")

    op.drop_index("ix_report_chat_messages_report_id_created_at", table_name="report_chat_messages")
    op.drop_table("report_chat_messages")

    op.drop_index("ix_backtest_reports_status", table_name="backtest_reports")
    op.drop_index("ix_backtest_reports_user_id_created_at", table_name="backtest_reports")
    op.drop_table("backtest_reports")

import math

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from sqlalchemy import func

from ..extensions import db
from ..models import (
    BacktestJob,
    BacktestJobStatus,
    BotInstance,
    SimulationBot,
    Strategy,
)
from ..quota import ensure_user_quota, get_plan_limit, serialize_plan_limit
from ..utils.response import ok
from ..utils.time import format_beijing_iso

bp = Blueprint("dashboard", __name__, url_prefix="/api")


@bp.get("/v1/dashboard/stats")
@jwt_required()
def get_dashboard_stats():
    user_id = get_jwt_identity()

    # Backtest counts
    completed_backtests = BacktestJob.query.filter_by(
        user_id=user_id, status=BacktestJobStatus.COMPLETED.value
    ).count()
    total_backtests = BacktestJob.query.filter_by(user_id=user_id).count()

    # Strategy count
    strategy_count = Strategy.query.filter_by(
        owner_id=user_id, deleted_at=None
    ).count()

    # Active bots (BotInstance + SimulationBot)
    active_bot_instances = BotInstance.query.filter(
        BotInstance.user_id == user_id,
        BotInstance.status.in_(("running", "active")),
        BotInstance.deleted_at.is_(None),
    ).count()
    active_sim_bots = SimulationBot.query.filter_by(
        user_id=user_id, status="active", deleted_at=None
    ).count()
    active_bots = active_bot_instances + active_sim_bots

    # Total bot count
    total_bot_instances = BotInstance.query.filter(
        BotInstance.user_id == user_id,
        BotInstance.deleted_at.is_(None),
    ).count()
    total_sim_bots = SimulationBot.query.filter_by(
        user_id=user_id, deleted_at=None
    ).count()
    total_bots = total_bot_instances + total_sim_bots

    # Quota
    quota = ensure_user_quota(user_id)
    db.session.commit()
    plan_limit = get_plan_limit(quota.plan_level)
    plan_limit_display = serialize_plan_limit(quota.plan_level)

    # Latest completed backtest summary for KPIs
    latest_job = (
        BacktestJob.query.filter_by(
            user_id=user_id, status=BacktestJobStatus.COMPLETED.value
        )
        .order_by(BacktestJob.completed_at.desc())
        .first()
    )

    latest_summary = latest_job.result_summary if latest_job else None
    total_return = latest_summary.get("totalReturn", 0) if latest_summary else 0

    # Previous completed backtest for profit change calculation
    previous_job = (
        BacktestJob.query.filter_by(
            user_id=user_id, status=BacktestJobStatus.COMPLETED.value
        )
        .order_by(BacktestJob.completed_at.desc())
        .offset(1)
        .first()
    )
    previous_return = (
        (previous_job.result_summary or {}).get("totalReturn", 0)
        if previous_job
        else 0
    )
    if previous_return != 0:
        profit_change = ((total_return - previous_return) / abs(previous_return)) * 100
    else:
        profit_change = 0.0

    # Recent backtest returns for sparkline chart (last 10 completed)
    recent_jobs = (
        BacktestJob.query.filter_by(
            user_id=user_id, status=BacktestJobStatus.COMPLETED.value
        )
        .order_by(BacktestJob.completed_at.desc())
        .limit(10)
        .all()
    )
    profit_history = [
        (job.result_summary or {}).get("totalReturn", 0)
        for job in reversed(recent_jobs)
    ]

    return ok(
        {
            "total_backtests": total_backtests,
            "completed_backtests": completed_backtests,
            "strategy_count": strategy_count,
            "active_bots": active_bots,
            "total_bots": total_bots,
            "backtest_quota": {
                "used": quota.used_count,
                "limit": plan_limit_display,
            },
            "latest_summary": {
                "total_return": total_return,
                "win_rate": latest_summary.get("winRate") if latest_summary else None,
                "avg_holding_days": (
                    latest_summary.get("avgHoldingDays") if latest_summary else None
                ),
                "sharpe_ratio": (
                    latest_summary.get("sharpeRatio") if latest_summary else None
                ),
                "annualized_return": (
                    latest_summary.get("annualizedReturn") if latest_summary else None
                ),
                "max_drawdown": (
                    latest_summary.get("maxDrawdown") if latest_summary else None
                ),
                "total_trades": (
                    latest_summary.get("totalTrades") if latest_summary else None
                ),
                "profit_factor": (
                    latest_summary.get("profitFactor") if latest_summary else None
                ),
            },
            "profit_change": round(profit_change, 2),
            "profit_history": profit_history,
        }
    )

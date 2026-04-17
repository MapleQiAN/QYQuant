from __future__ import annotations

from typing import Any

from ..celery_app import celery_app
from ..extensions import db
from ..models import BacktestJob, Strategy
from ..strategy_runtime import preflight_strategy
from ..tasks.backtests import run_backtest_task


DEFAULT_LIMIT = 120


def launch_marketplace_trial_backtest(strategy: Strategy, *, user_id: str, payload: dict[str, Any] | None = None) -> BacktestJob:
    params = normalize_marketplace_trial_backtest_payload(strategy, payload)
    _, validated_params = preflight_strategy(
        strategy.id,
        params.get("strategy_version"),
        params.get("strategy_params"),
        user_id=user_id,
    )
    params["strategy_params"] = validated_params

    job = BacktestJob(
        user_id=user_id,
        strategy_id=strategy.id,
        params=params,
    )
    db.session.add(job)
    db.session.commit()

    if celery_app.conf.task_always_eager:
        run_backtest_task.run(job.id)
    else:
        run_backtest_task.apply_async(args=[job.id], task_id=job.id, queue="backtest")
    return job


def normalize_marketplace_trial_backtest_payload(
    strategy: Strategy,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_payload = payload if isinstance(payload, dict) else {}
    trial_params = _normalize_strategy_params(
        normalized_payload.get("params")
        or normalized_payload.get("strategy_params")
        or normalized_payload.get("strategyParams")
    )
    time_range = _normalize_mapping(
        normalized_payload.get("time_range")
        or normalized_payload.get("timeRange")
    )

    return {
        "mode": "trial",
        "symbol": _normalize_string(normalized_payload.get("symbol")) or strategy.symbol or "BTCUSDT",
        "interval": _normalize_string(normalized_payload.get("interval")),
        "limit": _normalize_limit(normalized_payload.get("limit")),
        "start_time": _normalize_string(
            time_range.get("start")
            or normalized_payload.get("start_time")
            or normalized_payload.get("startTime")
        ),
        "end_time": _normalize_string(
            time_range.get("end")
            or normalized_payload.get("end_time")
            or normalized_payload.get("endTime")
        ),
        "strategy_id": strategy.id,
        "strategy_version": _normalize_string(
            normalized_payload.get("strategy_version")
            or normalized_payload.get("strategyVersion")
        ),
        "strategy_params": trial_params,
        "data_source": _normalize_string(
            normalized_payload.get("data_source")
            or normalized_payload.get("dataSource")
            or normalized_payload.get("provider")
        ),
    }


def _normalize_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _normalize_strategy_params(value: Any) -> Any:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    return value


def _normalize_limit(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return DEFAULT_LIMIT
    return parsed if parsed > 0 else DEFAULT_LIMIT


def _normalize_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None

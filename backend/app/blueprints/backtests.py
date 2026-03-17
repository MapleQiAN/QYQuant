from celery.result import AsyncResult
from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from ..backtest.engine import run_backtest
from ..celery_app import celery_app
from ..extensions import db
from ..models import BacktestJob, BacktestJobStatus, Strategy
from ..quota import ensure_user_quota, has_remaining_quota, serialize_plan_limit
from ..services.error_parser import load_execution_error
from ..services.supported_packages import get_supported_packages
from ..strategy_runtime import StrategyRuntimeError, as_response, preflight_strategy
from ..tasks.backtests import run_backtest_task
from ..utils.response import error_response, ok
from ..utils.storage import build_backtest_storage_key, read_json
from ..utils.time import format_beijing_iso


AVERAGE_BACKTEST_SECONDS = 30
REPORT_DISCLAIMER = "回测结果仅供研究参考，不构成任何投资建议。"

bp = Blueprint("backtests", __name__, url_prefix="/api")


def _build_legacy_job_data(job_id):
    job_record = db.session.get(BacktestJob, job_id)
    if job_record is None:
        return None

    result = AsyncResult(job_id, app=celery_app)
    data = {
        "job_id": job_record.id,
        "status": job_record.status,
        "params": job_record.params,
        "result_summary": job_record.result_summary,
        "error_message": job_record.error_message,
        "started_at": format_beijing_iso(job_record.started_at),
        "completed_at": format_beijing_iso(job_record.completed_at),
        "created_at": format_beijing_iso(job_record.created_at),
        "celery_status": result.status,
    }
    if result.status == "SUCCESS":
        data["result"] = result.result
    return data


def _estimate_wait_time():
    pending_count = BacktestJob.query.filter_by(status=BacktestJobStatus.PENDING.value).count()
    return pending_count * AVERAGE_BACKTEST_SECONDS


def _serialize_job_status(job_record):
    return {
        "job_id": job_record.id,
        "status": job_record.status,
        "created_at": format_beijing_iso(job_record.created_at),
        "started_at": format_beijing_iso(job_record.started_at),
        "completed_at": format_beijing_iso(job_record.completed_at),
        "estimated_wait_time": _estimate_wait_time() if job_record.status == BacktestJobStatus.PENDING.value else 0,
    }


def _get_strategy_for_submit(strategy_id, user_id):
    strategy = db.session.get(Strategy, strategy_id)
    if strategy is None:
        return None
    if strategy.owner_id not in {None, user_id}:
        return None
    return strategy


def _build_v1_job_params(payload):
    symbols = payload.get("symbols") or []
    parameters = payload.get("parameters") or {}
    return {
        "symbol": symbols[0] if symbols else None,
        "symbols": symbols,
        "start_date": payload.get("start_date"),
        "end_date": payload.get("end_date"),
        "start_time": payload.get("start_date"),
        "end_time": payload.get("end_date"),
        "strategy_id": payload.get("strategy_id"),
        "strategy_params": parameters,
        "parameters": parameters,
    }


@bp.post("/backtests/run")
def run():
    payload = request.get_json() or {}
    symbol = payload.get("symbol", "BTCUSDT")
    interval = payload.get("interval")
    data_source = payload.get("dataSource", payload.get("data_source", payload.get("provider")))
    limit = payload.get("limit", 120)
    start_time = payload.get("startTime", payload.get("start_time"))
    end_time = payload.get("endTime", payload.get("end_time"))
    strategy_id = payload.get("strategyId", payload.get("strategy_id"))
    strategy_version = payload.get("strategyVersion", payload.get("strategy_version"))
    strategy_params = payload.get("strategyParams", payload.get("strategy_params"))

    try:
        limit = int(limit) if limit is not None else 120
    except (TypeError, ValueError):
        limit = 120

    if strategy_id:
        try:
            preflight_strategy(strategy_id, strategy_version, strategy_params)
        except StrategyRuntimeError as exc:
            return as_response(exc), 400

    job_record = BacktestJob(
        user_id=payload.get("userId", payload.get("user_id")),
        strategy_id=strategy_id,
        params={
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
            "start_time": start_time,
            "end_time": end_time,
            "strategy_id": strategy_id,
            "strategy_version": strategy_version,
            "strategy_params": strategy_params,
            "data_source": data_source,
        },
    )
    db.session.add(job_record)
    db.session.commit()

    run_backtest_task.apply_async(args=[job_record.id], task_id=job_record.id, queue="backtest")
    return ok({"job_id": job_record.id})


@bp.get("/backtests/job/<job_id>")
def job(job_id):
    data = _build_legacy_job_data(job_id)
    if data is None:
        return {"code": 40400, "message": "job_not_found", "details": None}, 404
    return ok(data)


@bp.get("/backtests/latest")
def latest():
    import json

    symbol = request.args.get("symbol", "BTCUSDT")
    interval = request.args.get("interval")
    data_source = request.args.get("dataSource", request.args.get("data_source", request.args.get("provider")))
    limit = request.args.get("limit", 120)
    start_time = request.args.get("startTime", request.args.get("start_time"))
    end_time = request.args.get("endTime", request.args.get("end_time"))
    strategy_id = request.args.get("strategyId", request.args.get("strategy_id"))
    strategy_version = request.args.get("strategyVersion", request.args.get("strategy_version"))
    strategy_params = request.args.get("strategyParams", request.args.get("strategy_params"))

    try:
        limit = int(limit) if limit is not None else 120
    except (TypeError, ValueError):
        limit = 120

    if strategy_params:
        try:
            strategy_params = json.loads(strategy_params)
        except (TypeError, ValueError, json.JSONDecodeError):
            return {"code": 40000, "message": "invalid_strategy_params", "details": None}, 400

    try:
        result = run_backtest(
            symbol,
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            strategy_params=strategy_params,
            data_source=data_source,
        )
    except StrategyRuntimeError as exc:
        return as_response(exc), 400
    return ok(result)


@bp.get("/v1/backtest/quota")
@jwt_required()
def get_quota():
    user_id = get_jwt_identity()
    quota = ensure_user_quota(user_id)
    db.session.commit()
    return ok(
        {
            "used_count": quota.used_count,
            "plan_limit": serialize_plan_limit(quota.plan_level),
            "plan_level": quota.plan_level,
            "reset_at": format_beijing_iso(quota.reset_at),
        }
    )


@bp.get("/v1/backtest/<job_id>")
@jwt_required()
def get_job_status(job_id):
    user_id = get_jwt_identity()
    job_record = db.session.get(BacktestJob, job_id)
    if job_record is None or job_record.user_id != user_id:
        return error_response("JOB_NOT_FOUND", "回测任务不存在", 404)
    return ok(_serialize_job_status(job_record))


@bp.get("/v1/backtest/<job_id>/report")
@jwt_required()
def get_backtest_report(job_id):
    user_id = get_jwt_identity()
    job_record = db.session.get(BacktestJob, job_id)
    if job_record is None or job_record.user_id != user_id:
        return error_response("JOB_NOT_FOUND", "回测任务不存在", 404)
    if job_record.status == BacktestJobStatus.FAILED.value:
        return ok(
            {
                "job_id": job_record.id,
                "status": job_record.status,
                "params": job_record.params,
                "error": load_execution_error(job_record.error_message),
                "completed_at": format_beijing_iso(job_record.completed_at),
            }
        )
    if job_record.status != BacktestJobStatus.COMPLETED.value:
        return error_response("REPORT_NOT_READY", "回测报告尚未生成", 409)

    storage_key = job_record.result_storage_key or build_backtest_storage_key(job_record.id)
    try:
        equity_curve = read_json(f"{storage_key}/equity_curve.json")
        trades = read_json(f"{storage_key}/trades.json")
    except FileNotFoundError:
        return error_response("REPORT_NOT_FOUND", "回测报告不存在", 404)

    return ok(
        {
            "job_id": job_record.id,
            "status": job_record.status,
            "params": job_record.params,
            "result_summary": job_record.result_summary or {},
            "equity_curve": equity_curve,
            "trades": trades,
            "completed_at": format_beijing_iso(job_record.completed_at),
            "disclaimer": REPORT_DISCLAIMER,
        }
    )


@bp.get("/v1/backtest/supported-packages")
@jwt_required()
def get_backtest_supported_packages():
    return ok({"packages": get_supported_packages()})


@bp.post("/v1/backtest/")
@jwt_required()
def submit_backtest():
    user_id = get_jwt_identity()
    payload = request.get_json() or {}
    strategy_id = payload.get("strategy_id")
    symbols = payload.get("symbols")
    start_date = payload.get("start_date")
    end_date = payload.get("end_date")

    if not strategy_id:
        return error_response("VALIDATION_ERROR", "strategy_id is required", 422)
    if not isinstance(symbols, list) or not symbols:
        return error_response("VALIDATION_ERROR", "symbols is required", 422)
    if not start_date or not end_date:
        return error_response("VALIDATION_ERROR", "start_date and end_date are required", 422)

    strategy = _get_strategy_for_submit(strategy_id, user_id)
    if strategy is None:
        return error_response("STRATEGY_NOT_FOUND", "策略不存在或无权访问", 404)

    quota = ensure_user_quota(user_id)
    if not has_remaining_quota(quota):
        db.session.rollback()
        return error_response("QUOTA_EXCEEDED", "额度已用完，请升级套餐", 429)

    job_record = BacktestJob(
        user_id=user_id,
        strategy_id=strategy.id,
        status=BacktestJobStatus.PENDING.value,
        params=_build_v1_job_params(payload),
    )
    db.session.add(job_record)
    db.session.commit()

    run_backtest_task.apply_async(args=[job_record.id], task_id=job_record.id, queue="backtest")
    return ok({"job_id": job_record.id})

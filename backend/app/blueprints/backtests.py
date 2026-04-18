import shutil

from celery.result import AsyncResult
from flask import after_this_request, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from ..backtest.engine import run_backtest
from ..celery_app import celery_app
from ..extensions import db
from ..models import BacktestJob, BacktestJobStatus, BacktestReport, Strategy
from ..quota import ensure_user_quota, has_remaining_quota, reserve_backtest_quota, serialize_plan_limit
from ..services.backtest_report_export import render_backtest_report_pdf
from ..services.error_parser import load_execution_error
from ..services.supported_packages import get_supported_packages
from ..strategy_runtime import StrategyRuntimeError, as_response, preflight_strategy
from ..tasks.backtests import run_backtest_task
from ..utils.response import error_response, ok
from ..utils.storage import build_backtest_storage_key, delete_json, read_json
from ..utils.time import format_beijing_iso


AVERAGE_BACKTEST_SECONDS = 30
REPORT_DISCLAIMER = "回测结果仅供研究参考，不构成任何投资建议。"

_EAGER_BACKTEST_RESULTS = {}
bp = Blueprint("backtests", __name__, url_prefix="/api")


def _build_legacy_job_data(job_id, user_id):
    job_record = db.session.get(BacktestJob, job_id)
    if job_record is None:
        return None
    if job_record.user_id != user_id:
        return None

    data = {
        "job_id": job_record.id,
        "status": job_record.status,
        "params": job_record.params,
        "result_summary": job_record.result_summary,
        "error_message": job_record.error_message,
        "started_at": format_beijing_iso(job_record.started_at),
        "completed_at": format_beijing_iso(job_record.completed_at),
        "created_at": format_beijing_iso(job_record.created_at),
    }

    if celery_app.conf.task_always_eager and job_id in _EAGER_BACKTEST_RESULTS:
        data["celery_status"] = "SUCCESS"
        data["result"] = _EAGER_BACKTEST_RESULTS[job_id]
        return data

    result = AsyncResult(job_id, app=celery_app)
    data["celery_status"] = result.status
    if result.status == "SUCCESS":
        data["result"] = result.result
    return data


def _estimate_wait_time():
    pending_count = BacktestJob.query.filter_by(status=BacktestJobStatus.PENDING.value).count()
    return pending_count * AVERAGE_BACKTEST_SECONDS


def _serialize_job_status(job_record):
    data = {
        "job_id": job_record.id,
        "status": job_record.status,
        "created_at": format_beijing_iso(job_record.created_at),
        "started_at": format_beijing_iso(job_record.started_at),
        "completed_at": format_beijing_iso(job_record.completed_at),
        "estimated_wait_time": _estimate_wait_time() if job_record.status == BacktestJobStatus.PENDING.value else 0,
    }
    if job_record.status in {BacktestJobStatus.FAILED.value, BacktestJobStatus.TIMEOUT.value} and job_record.error_message:
        data["error_message"] = job_record.error_message
        data["error"] = load_execution_error(job_record.error_message)
    return data


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
        "name": payload.get("name"),
        "symbol": symbols[0] if symbols else None,
        "symbols": symbols,
        "start_date": payload.get("start_date"),
        "end_date": payload.get("end_date"),
        "start_time": payload.get("start_date"),
        "end_time": payload.get("end_date"),
        "data_source": payload.get("data_source", payload.get("dataSource", payload.get("provider"))),
        "strategy_id": payload.get("strategy_id"),
        "strategy_params": parameters,
        "parameters": parameters,
    }


def _derive_backtest_name(job_record, strategy_name=None):
    params = job_record.params or {}
    if params.get("name"):
        return params["name"]

    symbol = params.get("symbol")
    start_date = params.get("start_date")
    end_date = params.get("end_date")

    segments = [segment for segment in [strategy_name, symbol] if segment]
    if start_date and end_date:
        segments.append(f"{start_date} ~ {end_date}")

    if segments:
        return " / ".join(str(segment) for segment in segments)
    return job_record.id


def _serialize_history_item(job_record, strategy_name=None):
    params = job_record.params or {}
    return {
        "job_id": job_record.id,
        "name": _derive_backtest_name(job_record, strategy_name),
        "strategy_id": job_record.strategy_id,
        "strategy_name": strategy_name,
        "symbol": params.get("symbol") or (params.get("symbols") or [None])[0],
        "status": job_record.status,
        "created_at": format_beijing_iso(job_record.created_at),
        "started_at": format_beijing_iso(job_record.started_at),
        "completed_at": format_beijing_iso(job_record.completed_at),
        "result_summary": job_record.result_summary,
        "has_report": job_record.status in {
            BacktestJobStatus.COMPLETED.value,
            BacktestJobStatus.FAILED.value,
        },
    }


@bp.post("/backtests/run")
@jwt_required()
def run():
    user_id = get_jwt_identity()
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
            preflight_strategy(strategy_id, strategy_version, strategy_params, user_id=user_id)
        except StrategyRuntimeError as exc:
            if exc.message == "strategy_not_found":
                return error_response("STRATEGY_NOT_FOUND", "策略不存在或无权访问", 404)
            return as_response(exc), 400

    job_record = BacktestJob(
        user_id=user_id,
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

    if celery_app.conf.task_always_eager:
        _EAGER_BACKTEST_RESULTS[job_record.id] = run_backtest_task.run(job_record.id)
    else:
        run_backtest_task.apply_async(args=[job_record.id], task_id=job_record.id, queue="backtest")
    return ok({"job_id": job_record.id})


@bp.get("/backtests/job/<job_id>")
@jwt_required()
def job(job_id):
    user_id = get_jwt_identity()
    data = _build_legacy_job_data(job_id, user_id)
    if data is None:
        return {"code": 40400, "message": "job_not_found", "details": None}, 404
    return ok(data)


@bp.get("/backtests/latest")
@jwt_required()
def latest():
    import json

    user_id = get_jwt_identity()
    symbol = request.args.get("symbol", "BTCUSDT")
    interval = request.args.get("interval")
    data_source = request.args.get("dataSource", request.args.get("data_source", request.args.get("provider")))
    limit = request.args.get("limit", 500)
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
            user_id=user_id,
        )
    except StrategyRuntimeError as exc:
        if exc.message == "strategy_not_found":
            return error_response("STRATEGY_NOT_FOUND", "策略不存在或无权访问", 404)
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


@bp.get("/v1/backtest/latest-report")
@jwt_required()
def get_latest_completed_report():
    user_id = get_jwt_identity()
    job_record = (
        BacktestJob.query.filter_by(user_id=user_id, status=BacktestJobStatus.COMPLETED.value)
        .order_by(BacktestJob.completed_at.desc())
        .first()
    )
    if job_record is None:
        return ok(None)

    params = job_record.params or {}
    storage_key = job_record.result_storage_key or build_backtest_storage_key(job_record.id)
    try:
        kline = read_json(f"{storage_key}/kline.json")
        trades = read_json(f"{storage_key}/trades.json")
    except FileNotFoundError:
        return ok(None)

    strategy_name = None
    if job_record.strategy_id:
        strategy = db.session.get(Strategy, job_record.strategy_id)
        strategy_name = strategy.name if strategy else None

    return ok({
        "summary": job_record.result_summary or {},
        "kline": kline,
        "trades": trades,
        "dataSource": params.get("data_source"),
        "job_id": job_record.id,
        "strategy_name": strategy_name,
        "symbol": params.get("symbol"),
        "interval": params.get("interval"),
        "completed_at": format_beijing_iso(job_record.completed_at),
    })


@bp.get("/v1/backtest/history")
@jwt_required()
def get_backtest_history():
    user_id = get_jwt_identity()
    limit = request.args.get("limit", default=50, type=int) or 50
    limit = max(1, min(limit, 200))

    jobs = (
        BacktestJob.query.filter_by(user_id=user_id)
        .order_by(BacktestJob.created_at.desc())
        .limit(limit)
        .all()
    )

    strategy_ids = {job.strategy_id for job in jobs if job.strategy_id}
    strategy_names = {}
    if strategy_ids:
        strategy_names = {
            strategy.id: strategy.name
            for strategy in Strategy.query.filter(Strategy.id.in_(strategy_ids)).all()
        }

    items = [
        _serialize_history_item(job, strategy_names.get(job.strategy_id))
        for job in jobs
    ]
    return ok({"items": items})


@bp.get("/v1/backtest/<job_id>/report")
@jwt_required()
def get_backtest_report(job_id):
    user_id = get_jwt_identity()
    job_record = db.session.get(BacktestJob, job_id)
    if job_record is None or job_record.user_id != user_id:
        return error_response("JOB_NOT_FOUND", "回测任务不存在", 404)
    report_record = BacktestReport.query.filter_by(backtest_job_id=job_record.id).one_or_none()
    if job_record.status == BacktestJobStatus.FAILED.value:
        return ok(
            {
                "job_id": job_record.id,
                "status": job_record.status,
                "params": job_record.params,
                "error": load_execution_error(job_record.error_message),
                "completed_at": format_beijing_iso(job_record.completed_at),
                "report_id": report_record.id if report_record else None,
                "report_status": report_record.status if report_record else None,
            }
        )
    if job_record.status != BacktestJobStatus.COMPLETED.value:
        return error_response("REPORT_NOT_READY", "回测报告尚未生成", 409)

    storage_key = job_record.result_storage_key or build_backtest_storage_key(job_record.id)
    try:
        equity_curve = read_json(f"{storage_key}/equity_curve.json")
        trades = read_json(f"{storage_key}/trades.json")
        kline = read_json(f"{storage_key}/kline.json")
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
            "kline": kline,
            "completed_at": format_beijing_iso(job_record.completed_at),
            "disclaimer": REPORT_DISCLAIMER,
            "report_id": report_record.id if report_record else None,
            "report_status": report_record.status if report_record else None,
        }
    )


@bp.post("/v1/backtest/<job_id>/export/pdf")
@jwt_required()
def export_backtest_report_pdf(job_id):
    user_id = get_jwt_identity()
    job_record = db.session.get(BacktestJob, job_id)
    if job_record is None or job_record.user_id != user_id:
        return error_response("JOB_NOT_FOUND", "回测任务不存在", 404)
    if job_record.status != BacktestJobStatus.COMPLETED.value:
        return error_response("REPORT_NOT_READY", "回测报告尚未生成", 409)

    payload = request.get_json() or {}
    html = payload.get("html")
    filename = payload.get("filename") or f"backtest-report-{job_id}.pdf"
    filename = str(filename).replace("\\", "/").split("/")[-1] or f"backtest-report-{job_id}.pdf"

    if not isinstance(html, str) or not html.strip():
        return error_response("VALIDATION_ERROR", "html is required", 422)

    try:
        pdf_path = render_backtest_report_pdf(job_id, html, filename=filename)
    except RuntimeError:
        return error_response("EXPORT_FAILED", "PDF 导出失败", 500)

    @after_this_request
    def _cleanup(response):
        shutil.rmtree(str(pdf_path.parent), ignore_errors=True)
        return response

    return send_file(
        pdf_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
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
    db.session.flush()

    if not reserve_backtest_quota(user_id, job_record.id):
        db.session.rollback()
        return error_response("QUOTA_EXCEEDED", "Quota exhausted, upgrade required", 429)

    db.session.commit()

    run_backtest_task.apply_async(args=[job_record.id], task_id=job_record.id, queue="backtest")
    return ok({"job_id": job_record.id})


@bp.delete("/v1/backtest/<job_id>")
@jwt_required()
def delete_backtest(job_id):
    user_id = get_jwt_identity()
    job_record = db.session.get(BacktestJob, job_id)
    if job_record is None or job_record.user_id != user_id:
        return error_response("JOB_NOT_FOUND", "回测任务不存在", 404)
    storage_key = job_record.result_storage_key or build_backtest_storage_key(job_record.id)
    db.session.delete(job_record)
    db.session.commit()
    delete_json(storage_key)
    return ok({"deleted": job_id})


@bp.post("/v1/backtest/batch-delete")
@jwt_required()
def batch_delete_backtests():
    user_id = get_jwt_identity()
    payload = request.get_json() or {}
    status = payload.get("status")
    if not status:
        return error_response("VALIDATION_ERROR", "status is required", 422)
    jobs = BacktestJob.query.filter_by(user_id=user_id, status=status).all()
    deleted_count = 0
    for job_record in jobs:
        storage_key = job_record.result_storage_key or build_backtest_storage_key(job_record.id)
        db.session.delete(job_record)
        delete_json(storage_key)
        deleted_count += 1
    db.session.commit()
    return ok({"deleted_count": deleted_count})

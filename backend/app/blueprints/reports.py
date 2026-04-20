import json
import time
from datetime import datetime, timezone

from flask import Response, request, stream_with_context
from flask_jwt_extended import decode_token, get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from ..extensions import db
from ..models import BacktestJob, BacktestJobStatus, BacktestReport, ReportAlert, ReportChatMessage, User
from ..report_agent import chat_router
from ..report_agent.tier_filter import filter_report_for_tier
from ..tasks.report_generation import generate_backtest_report
from ..utils.response import error_response, ok


bp = Blueprint("reports", __name__, url_prefix="/api")
TERMINAL_REPORT_STATUSES = {"ready", "failed"}


def _get_report_for_user(report_id, user_id):
    report = db.session.get(BacktestReport, report_id)
    if report is None or report.user_id != user_id:
        return None
    return report


def _get_job_for_user(job_id, user_id):
    job = db.session.get(BacktestJob, job_id)
    if job is None or job.user_id != user_id:
        return None
    return job


def _serialize_report_payload(report):
    return {
        "metrics": report.metrics or {},
        "equity_curve": report.equity_curve or [],
        "drawdown_series": report.drawdown_series or [],
        "monthly_returns": report.monthly_returns or [],
        "trade_details": report.trade_details or [],
        "executive_summary": report.executive_summary,
        "metric_narrations": report.metric_narrations or {},
        "anomalies": report.anomalies or [],
        "parameter_sensitivity": report.parameter_sensitivity or [],
        "monte_carlo": report.monte_carlo or {},
        "regime_analysis": report.regime_analysis or [],
        "diagnosis_narration": report.diagnosis_narration,
        "advisor_narration": report.advisor_narration,
    }


def _serialize_report_status(report):
    return {
        "id": report.id,
        "job_id": report.backtest_job_id,
        "status": report.status,
    }


def _serialize_chat_message(message):
    return {
        "id": message.id,
        "role": message.role,
        "message": message.message,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }


def _serialize_alert(alert):
    return {
        "id": alert.id,
        "level": alert.level,
        "title": alert.title,
        "message": alert.message,
        "status": alert.status,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
    }


def _resolve_stream_user_id():
    token = request.args.get("token", "")
    if not token:
        return None, error_response("UNAUTHORIZED", "Missing token", 401)

    try:
        decoded = decode_token(token)
    except Exception:
        return None, error_response("UNAUTHORIZED", "Invalid token", 401)

    user_id = decoded.get("sub")
    if not user_id:
        return None, error_response("UNAUTHORIZED", "Invalid token", 401)

    user = db.session.get(User, user_id)
    if user is None or user.deleted_at is not None:
        return None, error_response("UNAUTHORIZED", "Invalid token", 401)

    return user_id, None


@bp.post("/backtests/<job_id>/report")
@jwt_required()
def create_or_regenerate_report(job_id):
    user_id = get_jwt_identity()
    job = _get_job_for_user(job_id, user_id)
    if job is None:
        return error_response("JOB_NOT_FOUND", "回测任务不存在", 404)
    if job.status != BacktestJobStatus.COMPLETED.value:
        return error_response("REPORT_NOT_READY", "回测尚未完成，无法生成报告", 409)

    report = BacktestReport.query.filter_by(backtest_job_id=job_id).one_or_none()
    if report is None:
        report = BacktestReport(
            backtest_job_id=job_id,
            user_id=user_id,
            status="pending",
        )
        db.session.add(report)
        db.session.commit()
    else:
        report.user_id = user_id
        report.status = "pending"
        report.failure_reason = None
        db.session.commit()

    locale = (request.get_json(silent=True) or {}).get("locale", "en")
    generate_backtest_report.delay(job_id, user_id, force=True, locale=locale)
    return ok(
        {
            "job_id": job_id,
            "report_id": report.id,
            "status": report.status,
        }
    )


@bp.get("/reports/<report_id>")
@jwt_required()
def get_report(report_id):
    user_id = get_jwt_identity()
    report = _get_report_for_user(report_id, user_id)
    if report is None:
        return error_response("REPORT_NOT_FOUND", "报告不存在", 404)

    user = db.session.get(User, user_id)
    payload = filter_report_for_tier(_serialize_report_payload(report), getattr(user, "plan_level", "free"))
    return ok(
        {
            "id": report.id,
            "job_id": report.backtest_job_id,
            "status": report.status,
            "payload": payload,
        }
    )


@bp.get("/reports/<report_id>/status")
@jwt_required()
def get_report_status(report_id):
    user_id = get_jwt_identity()
    report = _get_report_for_user(report_id, user_id)
    if report is None:
        return error_response("REPORT_NOT_FOUND", "报告不存在", 404)
    return ok(_serialize_report_status(report))


@bp.post("/reports/<report_id>/chat")
@jwt_required()
def post_report_chat(report_id):
    user_id = get_jwt_identity()
    report = _get_report_for_user(report_id, user_id)
    if report is None:
        return error_response("REPORT_NOT_FOUND", "报告不存在", 404)

    user = db.session.get(User, user_id)
    if not chat_router.is_chat_available(getattr(user, "plan_level", "free")):
        return error_response("REPORT_CHAT_UNAVAILABLE", "当前套餐暂未开放报告对话", 403)

    message = (request.get_json(silent=True) or {}).get("message", "")
    message = str(message).strip()
    if not message:
        return error_response("INVALID_MESSAGE", "请输入问题", 400)

    user_message = ReportChatMessage(
        report_id=report.id,
        user_id=user_id,
        role="user",
        message=message,
    )
    db.session.add(user_message)
    db.session.flush()

    locale = (request.get_json(silent=True) or {}).get("locale", "en")
    answer = chat_router.route_chat_question(message, report, locale=locale)
    assistant_message = ReportChatMessage(
        report_id=report.id,
        user_id=None,
        role="assistant",
        message=answer,
    )
    db.session.add(assistant_message)
    db.session.commit()

    return ok(_serialize_chat_message(assistant_message))


@bp.get("/reports/<report_id>/chat/history")
@jwt_required()
def get_report_chat_history(report_id):
    user_id = get_jwt_identity()
    report = _get_report_for_user(report_id, user_id)
    if report is None:
        return error_response("REPORT_NOT_FOUND", "报告不存在", 404)

    messages = (
        ReportChatMessage.query.filter_by(report_id=report.id)
        .order_by(ReportChatMessage.created_at.asc())
        .all()
    )
    return ok({"messages": [_serialize_chat_message(message) for message in messages]})


@bp.get("/reports/<report_id>/alerts")
@jwt_required()
def get_report_alerts(report_id):
    user_id = get_jwt_identity()
    report = _get_report_for_user(report_id, user_id)
    if report is None:
        return error_response("REPORT_NOT_FOUND", "报告不存在", 404)

    alerts = (
        ReportAlert.query.filter_by(report_id=report.id, user_id=user_id)
        .order_by(ReportAlert.created_at.asc())
        .all()
    )
    return ok({"alerts": [_serialize_alert(alert) for alert in alerts]})


@bp.post("/reports/<report_id>/alerts/<alert_id>/dismiss")
@jwt_required()
def dismiss_report_alert(report_id, alert_id):
    user_id = get_jwt_identity()
    report = _get_report_for_user(report_id, user_id)
    if report is None:
        return error_response("REPORT_NOT_FOUND", "报告不存在", 404)

    alert = ReportAlert.query.filter_by(id=alert_id, report_id=report.id, user_id=user_id).one_or_none()
    if alert is None:
        return error_response("ALERT_NOT_FOUND", "提醒不存在", 404)

    alert.status = "dismissed"
    db.session.commit()
    return ok(_serialize_alert(alert))


@bp.get("/reports/<report_id>/status/stream")
def stream_report_status(report_id):
    user_id, error = _resolve_stream_user_id()
    if error:
        return error

    report = _get_report_for_user(report_id, user_id)
    if report is None:
        return error_response("REPORT_NOT_FOUND", "报告不存在", 404)

    def generate():
        last_status = None
        last_heartbeat_at = time.monotonic()

        while True:
            current = db.session.get(BacktestReport, report_id)
            if current is None or current.user_id != user_id:
                break

            payload = _serialize_report_status(current)
            if payload["status"] != last_status:
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                last_status = payload["status"]
                last_heartbeat_at = time.monotonic()

            if payload["status"] in TERMINAL_REPORT_STATUSES:
                break

            if time.monotonic() - last_heartbeat_at >= 30:
                yield f": heartbeat {datetime.now(timezone.utc).isoformat()}\n\n"
                last_heartbeat_at = time.monotonic()

            time.sleep(1)

    return Response(
        stream_with_context(generate()),
        content_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

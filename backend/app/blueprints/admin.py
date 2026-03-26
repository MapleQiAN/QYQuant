from datetime import timedelta

from flask import request
from flask_smorest import Blueprint
from sqlalchemy.orm import aliased

from ..celery_app import celery_app
from ..extensions import db
from ..models import BacktestJob, BacktestJobStatus, Report, Strategy, User
from ..services.notifications import create_notification
from ..tasks.notification_tasks import send_email_notification
from ..utils.auth_helpers import require_admin
from ..utils.audit import log_audit
from ..utils.response import error_response, ok
from ..utils.time import ensure_aware_utc, format_beijing_iso, format_beijing_iso_ms, now_ms, now_utc

bp = Blueprint("admin", __name__, url_prefix="/api/v1/admin")
REVIEWABLE_STATUSES = {"approved", "rejected"}
REPORT_RESOLUTION_ACTIONS = {"takedown", "dismiss"}


@bp.get("/health")
@require_admin
def admin_health():
    return ok({"status": "ok", "scope": "admin"})


@bp.get("/strategies")
@require_admin
def list_admin_strategies():
    review_status = (request.args.get("review_status") or "pending").strip() or "pending"
    page = _int_arg("page", default=1, minimum=1)
    per_page = _int_arg("per_page", default=20, minimum=1, maximum=100)

    query = (
        db.session.query(Strategy, User)
        .outerjoin(User, Strategy.owner_id == User.id)
        .filter(Strategy.review_status == review_status)
        .order_by(Strategy.created_at.desc(), Strategy.id.desc())
    )

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return ok(
        [_serialize_admin_strategy(strategy, author) for strategy, author in items],
        meta={"total": total, "page": page, "per_page": per_page},
    )


@bp.patch("/strategies/<strategy_id>/review")
@require_admin
def review_strategy(strategy_id):
    payload = request.get_json() or {}
    status = str(payload.get("status") or "").strip().lower()
    if status not in REVIEWABLE_STATUSES:
        return error_response("REVIEW_STATUS_INVALID", "Review status is invalid", 422)

    reason = payload.get("reason")
    reason = str(reason).strip() if reason is not None else None
    if status == "rejected" and not reason:
        return error_response("REVIEW_REASON_REQUIRED", "Review reason is required", 422)
    if status == "approved":
        reason = None

    strategy = db.session.get(Strategy, strategy_id)
    if strategy is None:
        return error_response("STRATEGY_NOT_FOUND", "Strategy not found", 404)
    if strategy.review_status != "pending":
        return error_response("STRATEGY_REVIEW_CONFLICT", "Strategy review has already been processed", 409)

    admin_id = _current_admin_id()
    reviewed_at = now_ms()
    previous_status = strategy.review_status
    strategy.review_status = status
    strategy.is_public = status == "approved"
    strategy.updated_at = reviewed_at
    strategy.last_update = reviewed_at

    strategy_name = strategy.title or strategy.name
    create_notification(
        user_id=strategy.owner_id,
        type="strategy_review_result",
        title=_notification_title_for_status(status),
        content=_notification_content_for_status(strategy_name, status, reason),
    )
    log_audit(
        operator_id=admin_id,
        action="strategy_approve" if status == "approved" else "strategy_reject",
        target_type="strategy",
        target_id=strategy.id,
        details={
            "review_status_before": previous_status,
            "review_status_after": status,
            "reason": reason,
            "strategy_owner_id": strategy.owner_id,
            "admin_id": admin_id,
        },
    )
    db.session.commit()

    send_email_notification.delay(
        user_id=strategy.owner_id,
        event_type="strategy_review_result",
        context_data={
            "strategy_name": strategy_name,
            "status": status,
            "reason": reason,
            "target_id": strategy.id,
        },
    )
    return ok({"strategy_id": strategy.id, "review_status": strategy.review_status})


@bp.get("/reports")
@require_admin
def list_admin_reports():
    status = (request.args.get("status") or "pending").strip() or "pending"
    page = _int_arg("page", default=1, minimum=1)
    per_page = _int_arg("per_page", default=20, minimum=1, maximum=100)

    reporter = aliased(User)
    author = aliased(User)
    query = (
        db.session.query(Report, reporter, Strategy, author)
        .join(Strategy, Report.strategy_id == Strategy.id)
        .outerjoin(reporter, Report.reporter_id == reporter.id)
        .outerjoin(author, Strategy.owner_id == author.id)
        .filter(Report.status == status)
        .order_by(Report.created_at.desc(), Report.id.desc())
    )

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return ok(
        [
            _serialize_admin_report(report, reporter_user, strategy, author_user)
            for report, reporter_user, strategy, author_user in items
        ],
        meta={"total": total, "page": page, "per_page": per_page},
    )


@bp.patch("/reports/<report_id>/resolve")
@require_admin
def resolve_report(report_id):
    payload = request.get_json() or {}
    action = str(payload.get("action") or "").strip().lower()
    admin_note = payload.get("admin_note")
    admin_note = str(admin_note).strip() if admin_note is not None else None
    if not admin_note:
        admin_note = None

    if admin_note and len(admin_note) > 500:
        return error_response("ADMIN_NOTE_TOO_LONG", "Admin note must be 500 characters or fewer", 422)

    if action not in REPORT_RESOLUTION_ACTIONS:
        return error_response("REPORT_ACTION_INVALID", "Report action is invalid", 422)

    report = db.session.get(Report, report_id)
    if report is None:
        return error_response("REPORT_NOT_FOUND", "Report not found", 404)
    if report.status != "pending":
        return error_response("REPORT_RESOLUTION_CONFLICT", "Report has already been processed", 409)

    strategy = db.session.get(Strategy, report.strategy_id)
    if strategy is None:
        return error_response("STRATEGY_NOT_FOUND", "Strategy not found", 404)

    admin_id = _current_admin_id()
    reviewed_at = now_utc()

    if action == "takedown":
        strategy.is_public = False
        strategy.updated_at = now_ms()
        strategy.last_update = strategy.updated_at

        pending_reports = (
            Report.query
            .filter(
                Report.strategy_id == strategy.id,
                Report.status == "pending",
            )
            .all()
        )
        for pending_report in pending_reports:
            pending_report.status = "reviewed"
            pending_report.reviewed_at = reviewed_at
            pending_report.reviewed_by = admin_id
            pending_report.admin_note = admin_note

        strategy_name = strategy.title or strategy.name
        takedown_reason = report.reason
        if strategy.owner_id:
            create_notification(
                user_id=strategy.owner_id,
                type="strategy_takedown",
                title="策略已下架",
                content=f"策略《{strategy_name}》已因举报被下架。原因：{takedown_reason}",
            )
        log_audit(
            operator_id=admin_id,
            action="strategy_takedown",
            target_type="strategy",
            target_id=strategy.id,
            details={
                "report_id": report.id,
                "strategy_id": strategy.id,
                "strategy_owner_id": strategy.owner_id,
                "reason": takedown_reason,
                "admin_note": admin_note,
            },
        )
        db.session.commit()

        if strategy.owner_id:
            send_email_notification.delay(
                user_id=strategy.owner_id,
                event_type="strategy_takedown",
                context_data={
                    "strategy_name": strategy_name,
                    "reason": takedown_reason,
                    "target_id": strategy.id,
                },
            )
        return ok({"report_id": report.id, "status": "reviewed", "action": action})

    report.status = "dismissed"
    report.reviewed_at = reviewed_at
    report.reviewed_by = admin_id
    report.admin_note = admin_note
    log_audit(
        operator_id=admin_id,
        action="report_dismiss",
        target_type="report",
        target_id=report.id,
        details={
            "report_id": report.id,
            "strategy_id": report.strategy_id,
            "admin_note": admin_note,
        },
    )
    db.session.commit()
    return ok({"report_id": report.id, "status": "dismissed", "action": action})


@bp.get("/backtest/queue-stats")
@require_admin
def get_backtest_queue_stats():
    return ok(
        {
            "stats": {
                "pending": BacktestJob.query.filter_by(status=BacktestJobStatus.PENDING.value).count(),
                "running": BacktestJob.query.filter_by(status=BacktestJobStatus.RUNNING.value).count(),
                "avg_duration": _average_completed_duration_seconds(),
                "failure_rate_1h": _failure_rate_last_hour(),
            },
            "stuck_jobs": _list_stuck_backtest_jobs(),
        }
    )


@bp.delete("/backtest/<job_id>")
@require_admin
def terminate_backtest_job(job_id):
    payload = request.get_json(silent=True) or {}
    admin_note = payload.get("admin_note")
    admin_note = str(admin_note).strip() if admin_note is not None else None
    if not admin_note:
        admin_note = None
    if admin_note and len(admin_note) > 500:
        return error_response("ADMIN_NOTE_TOO_LONG", "Admin note must be 500 characters or fewer", 422)

    job = db.session.get(BacktestJob, job_id)
    if job is None:
        return error_response("JOB_NOT_FOUND", "Backtest job not found", 404)
    if job.status not in {BacktestJobStatus.PENDING.value, BacktestJobStatus.RUNNING.value}:
        return error_response("JOB_TERMINATION_CONFLICT", "Backtest job cannot be terminated", 409)

    strategy = db.session.get(Strategy, job.strategy_id) if job.strategy_id else None
    admin_id = _current_admin_id()
    completed_at = now_utc()
    running_duration_seconds = _duration_seconds(job.started_at, completed_at)
    strategy_name = _strategy_display_name(strategy)
    reason = admin_note or "管理员手动终止"

    celery_app.control.revoke(job_id, terminate=True)

    job.status = BacktestJobStatus.FAILED.value
    job.error_message = "管理员手动终止"
    job.completed_at = completed_at

    if job.user_id:
        create_notification(
            user_id=job.user_id,
            type="job_terminated",
            title="回测任务已终止",
            content=f"策略“{strategy_name}”的回测任务已被管理员终止。原因：{reason}",
        )

    log_audit(
        operator_id=admin_id,
        action="job_terminate",
        target_type="backtest_job",
        target_id=job.id,
        details={
            "job_id": job.id,
            "user_id": job.user_id,
            "strategy_id": job.strategy_id,
            "strategy_name": strategy_name,
            "running_duration_seconds": running_duration_seconds,
            "admin_note": admin_note,
        },
    )
    db.session.commit()
    return ok({"job_id": job.id, "status": "terminated"})


def _serialize_admin_strategy(strategy, author):
    return {
        "id": strategy.id,
        "title": strategy.title or strategy.name,
        "name": strategy.name,
        "description": strategy.description,
        "category": strategy.category,
        "tags": list(strategy.tags or []),
        "display_metrics": dict(strategy.display_metrics or {}),
        "owner_id": strategy.owner_id,
        "author_nickname": getattr(author, "nickname", None),
        "created_at": format_beijing_iso_ms(strategy.created_at),
        "review_status": strategy.review_status,
    }


def _serialize_admin_report(report, reporter, strategy, author):
    return {
        "id": report.id,
        "reporter_id": report.reporter_id,
        "reporter_nickname": getattr(reporter, "nickname", None),
        "strategy_id": strategy.id,
        "strategy_title": strategy.title or strategy.name,
        "strategy_author_id": strategy.owner_id,
        "strategy_author_nickname": getattr(author, "nickname", None),
        "reason": report.reason,
        "status": report.status,
        "created_at": format_beijing_iso(report.created_at),
    }


def _notification_title_for_status(status):
    if status == "approved":
        return "策略审核通过"
    return "策略审核被拒绝"


def _notification_content_for_status(strategy_name, status, reason):
    if status == "approved":
        return f"您的策略《{strategy_name}》已通过审核，现已在策略广场上架。"
    return f"您的策略《{strategy_name}》未通过审核。原因：{reason}"


def _average_completed_duration_seconds():
    completed_jobs = (
        BacktestJob.query
        .filter(BacktestJob.status == BacktestJobStatus.COMPLETED.value)
        .filter(BacktestJob.started_at.isnot(None), BacktestJob.completed_at.isnot(None))
        .order_by(BacktestJob.completed_at.desc(), BacktestJob.id.desc())
        .limit(100)
        .all()
    )
    durations = [
        _duration_seconds(job.started_at, job.completed_at)
        for job in completed_jobs
        if job.started_at is not None and job.completed_at is not None
    ]
    if not durations:
        return 0
    return int(round(sum(durations) / len(durations)))


def _failure_rate_last_hour():
    cutoff = now_utc() - timedelta(hours=1)
    terminal_jobs = (
        BacktestJob.query
        .filter(
            BacktestJob.status.in_(
                [
                    BacktestJobStatus.COMPLETED.value,
                    BacktestJobStatus.FAILED.value,
                    BacktestJobStatus.TIMEOUT.value,
                ]
            )
        )
        .filter(BacktestJob.completed_at.isnot(None), BacktestJob.completed_at >= cutoff)
        .all()
    )
    if not terminal_jobs:
        return 0
    failed_jobs = sum(
        1
        for job in terminal_jobs
        if job.status in {BacktestJobStatus.FAILED.value, BacktestJobStatus.TIMEOUT.value}
    )
    return round(failed_jobs / len(terminal_jobs), 4)


def _list_stuck_backtest_jobs():
    cutoff = now_utc() - timedelta(minutes=10)
    current_time = now_utc()
    items = (
        db.session.query(BacktestJob, Strategy)
        .outerjoin(Strategy, BacktestJob.strategy_id == Strategy.id)
        .filter(BacktestJob.status == BacktestJobStatus.RUNNING.value)
        .filter(BacktestJob.started_at.isnot(None), BacktestJob.started_at < cutoff)
        .order_by(BacktestJob.started_at.asc(), BacktestJob.id.asc())
        .all()
    )
    return [_serialize_stuck_job(job, strategy, current_time) for job, strategy in items]


def _serialize_stuck_job(job, strategy, current_time):
    return {
        "job_id": job.id,
        "user_id": job.user_id,
        "strategy_id": job.strategy_id,
        "strategy_name": _strategy_display_name(strategy),
        "started_at": format_beijing_iso(job.started_at),
        "running_duration_seconds": _duration_seconds(job.started_at, current_time),
    }


def _strategy_display_name(strategy):
    if strategy is None:
        return "未命名策略"
    return strategy.title or strategy.name or "未命名策略"


def _duration_seconds(started_at, ended_at):
    if started_at is None or ended_at is None:
        return 0
    started_at = ensure_aware_utc(started_at)
    ended_at = ensure_aware_utc(ended_at)
    return max(int((ended_at - started_at).total_seconds()), 0)


def _int_arg(name, *, default, minimum=None, maximum=None):
    raw = request.args.get(name)
    try:
        value = int(raw) if raw is not None else default
    except (TypeError, ValueError):
        value = default
    if minimum is not None:
        value = max(value, minimum)
    if maximum is not None:
        value = min(value, maximum)
    return value


def _current_admin_id():
    from flask_jwt_extended import get_jwt_identity

    return get_jwt_identity()

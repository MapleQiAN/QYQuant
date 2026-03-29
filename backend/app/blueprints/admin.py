from datetime import datetime, timedelta

from flask import request
from flask_smorest import Blueprint
from sqlalchemy import or_
from sqlalchemy.orm import aliased

from ..celery_app import celery_app
from ..extensions import db
from ..models import AuditLog, BacktestJob, BacktestJobStatus, Report, Strategy, User
from ..services.data_source_health import DataSourceHealthService
from ..services.notifications import create_notification
from ..tasks.notification_tasks import send_email_notification
from ..utils.auth import blacklist_refresh_tokens, revoke_all_user_tokens
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


@bp.get("/data-source-health")
@require_admin
def get_data_source_health():
    return ok(DataSourceHealthService(session=db.session).get_status_payload())


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


@bp.get("/users")
@require_admin
def list_admin_users():
    search = (request.args.get("search") or "").strip()
    page = _int_arg("page", default=1, minimum=1)
    per_page = _int_arg("per_page", default=20, minimum=1, maximum=100)

    query = User.query.filter(User.deleted_at.is_(None), User.role != "admin")
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(User.phone.ilike(pattern), User.nickname.ilike(pattern)))

    total = query.count()
    items = query.order_by(User.created_at.desc(), User.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return ok(
        [_serialize_admin_user(user) for user in items],
        meta={"total": total, "page": page, "per_page": per_page},
    )


@bp.patch("/users/<user_id>")
@require_admin
def update_admin_user(user_id):
    payload = request.get_json() or {}
    is_banned = payload.get("is_banned")
    ban_reason = payload.get("ban_reason")

    if not isinstance(is_banned, bool):
        return error_response("INVALID_BAN_STATUS", "Ban status must be a boolean", 422)

    ban_reason = str(ban_reason).strip() if ban_reason is not None else None
    if not ban_reason:
        ban_reason = None
    if ban_reason and len(ban_reason) > 500:
        return error_response("BAN_REASON_TOO_LONG", "Ban reason must be 500 characters or fewer", 422)

    user = db.session.get(User, user_id)
    if user is None or user.deleted_at is not None:
        return error_response("USER_NOT_FOUND", "User not found", 404)

    if user.is_banned == is_banned:
        return ok({"user_id": user.id, "is_banned": user.is_banned})

    admin_id = _current_admin_id()
    token_revoked_count = 0
    if is_banned:
        active_tokens = revoke_all_user_tokens(user.id, reason='admin_ban')
        blacklist_refresh_tokens(active_tokens)
        token_revoked_count = len(active_tokens)

    user.is_banned = is_banned
    create_notification(
        user_id=user.id,
        type="user_ban_status",
        title=_user_ban_notification_title(is_banned),
        content=_user_ban_notification_content(user.nickname, is_banned, ban_reason),
    )
    log_audit(
        operator_id=admin_id,
        action="user_ban" if is_banned else "user_unban",
        target_type="user",
        target_id=user.id,
        details={
            "is_banned_before": not is_banned,
            "is_banned_after": is_banned,
            "ban_reason": ban_reason,
            "token_revoked_count": token_revoked_count,
        },
    )
    db.session.commit()

    send_email_notification.delay(
        user_id=user.id,
        event_type="user_ban_status",
        context_data={
            "is_banned": is_banned,
            "ban_reason": ban_reason,
            "target_id": user.id,
        },
    )
    return ok({"user_id": user.id, "is_banned": user.is_banned})


@bp.get("/audit-logs")
@require_admin
def list_admin_audit_logs():
    operator = aliased(User)
    page = _int_arg("page", default=1, minimum=1)
    per_page = _int_arg("per_page", default=20, minimum=1, maximum=100)

    query = db.session.query(AuditLog, operator).outerjoin(operator, AuditLog.operator_id == operator.id)

    operator_id = (request.args.get("operator_id") or "").strip()
    action = (request.args.get("action") or "").strip()
    target_type = (request.args.get("target_type") or "").strip()
    target_id = (request.args.get("target_id") or "").strip()
    date_from = _datetime_arg("date_from")
    date_to = _datetime_arg("date_to")

    if operator_id:
        query = query.filter(AuditLog.operator_id == operator_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)
    if target_id:
        query = query.filter(AuditLog.target_id == target_id)
    if date_from is not None:
        query = query.filter(AuditLog.created_at >= date_from)
    if date_to is not None:
        query = query.filter(AuditLog.created_at <= date_to)

    total = query.count()
    items = (
        query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return ok(
        [_serialize_admin_audit_log(audit_log, operator_user) for audit_log, operator_user in items],
        meta={"total": total, "page": page, "per_page": per_page},
    )


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
    running_duration_seconds = _duration_seconds(job.started_at, completed_at) if job.started_at else None
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


def _serialize_admin_user(user):
    return {
        "user_id": user.id,
        "nickname": user.nickname,
        "phone": _mask_phone(user.phone),
        "created_at": format_beijing_iso(user.created_at),
        "plan_level": user.plan_level,
        "is_banned": bool(user.is_banned),
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


def _serialize_admin_audit_log(audit_log, operator_user):
    return {
        "id": audit_log.id,
        "operator_id": audit_log.operator_id,
        "operator_nickname": getattr(operator_user, "nickname", None),
        "action": audit_log.action,
        "target_type": audit_log.target_type,
        "target_id": audit_log.target_id,
        "details": audit_log.details or {},
        "created_at": format_beijing_iso(audit_log.created_at),
    }


def _mask_phone(phone):
    if not phone:
        return ""
    if len(phone) < 7:
        return phone
    return f"{phone[:3]}****{phone[-4:]}"


def _notification_title_for_status(status):
    if status == "approved":
        return "策略审核通过"
    return "策略审核被拒绝"


def _notification_content_for_status(strategy_name, status, reason):
    if status == "approved":
        return f"您的策略《{strategy_name}》已通过审核，现已在策略广场上架。"
    return f"您的策略《{strategy_name}》未通过审核。原因：{reason}"


def _user_ban_notification_title(is_banned):
    return "账号已被封禁" if is_banned else "账号已解封"


def _user_ban_notification_content(nickname, is_banned, ban_reason):
    display_name = nickname or "您的账号"
    if is_banned:
        if ban_reason:
            return f"{display_name}因违规已被封禁。原因：{ban_reason}"
        return f"{display_name}因违规已被封禁。"
    return f"{display_name}已解除封禁，可以重新登录。"


def _average_completed_duration_seconds():
    rows = (
        db.session.query(BacktestJob.started_at, BacktestJob.completed_at)
        .filter(BacktestJob.status == BacktestJobStatus.COMPLETED.value)
        .filter(BacktestJob.started_at.isnot(None), BacktestJob.completed_at.isnot(None))
        .order_by(BacktestJob.completed_at.desc(), BacktestJob.id.desc())
        .limit(100)
        .all()
    )
    if not rows:
        return 0
    total = sum(_duration_seconds(s, c) for s, c in rows)
    return int(round(total / len(rows)))


def _failure_rate_last_hour():
    from sqlalchemy import case, func

    cutoff = now_utc() - timedelta(hours=1)
    failed_statuses = [BacktestJobStatus.FAILED.value, BacktestJobStatus.TIMEOUT.value]
    terminal_statuses = [BacktestJobStatus.COMPLETED.value] + failed_statuses

    row = (
        db.session.query(
            func.count().label("total"),
            func.sum(case((BacktestJob.status.in_(failed_statuses), 1), else_=0)).label("failed"),
        )
        .filter(BacktestJob.status.in_(terminal_statuses))
        .filter(BacktestJob.completed_at.isnot(None), BacktestJob.completed_at >= cutoff)
        .one()
    )
    if not row.total:
        return 0
    return round(int(row.failed) / int(row.total), 4)


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


def _datetime_arg(name):
    raw = (request.args.get(name) or "").strip()
    if not raw:
        return None
    try:
        return ensure_aware_utc(datetime.fromisoformat(raw.replace("Z", "+00:00")))
    except ValueError:
        return None


def _current_admin_id():
    from flask_jwt_extended import get_jwt_identity

    return get_jwt_identity()

from flask import request
from flask_smorest import Blueprint

from ..extensions import db
from ..models import Strategy, User
from ..services.notifications import create_notification
from ..tasks.notification_tasks import send_email_notification
from ..utils.auth_helpers import require_admin
from ..utils.audit import log_audit
from ..utils.response import error_response, ok
from ..utils.time import format_beijing_iso_ms, now_ms

bp = Blueprint("admin", __name__, url_prefix="/api/v1/admin")
REVIEWABLE_STATUSES = {"approved", "rejected"}


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
    previous_status = strategy.review_status
    reviewed_at = now_ms()
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


def _notification_title_for_status(status):
    if status == "approved":
        return "策略审核通过"
    return "策略审核被拒绝"


def _notification_content_for_status(strategy_name, status, reason):
    if status == "approved":
        return f"您的策略「{strategy_name}」已通过审核，现已在策略广场上架。"
    return f"您的策略「{strategy_name}」未通过审核。原因：{reason}"


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

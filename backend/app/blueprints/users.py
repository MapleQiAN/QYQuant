import math

from flask import current_app, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from ..extensions import db
from ..models import Post, Strategy, User
from ..quota import ensure_user_quota, get_plan_limit, serialize_plan_limit
from ..schemas import UserPrivateSchema, UserPublicSchema, UserUpdateSchema
from ..utils.audit import log_audit
from ..utils.auth import blacklist_refresh_tokens, clear_refresh_cookie, consume_verification_code, revoke_all_user_tokens
from ..utils.phone import mask_phone
from ..utils.response import error_response, ok
from ..utils.time import format_beijing_iso, now_utc

bp = Blueprint('users', __name__, url_prefix='/api/v1/users')

_private_schema = UserPrivateSchema()
_public_schema = UserPublicSchema()
_update_schema = UserUpdateSchema()


def _get_user_or_404(user_id):
    user = db.session.get(User, user_id)
    if user is None or user.deleted_at is not None:
        return None, error_response("USER_NOT_FOUND", "user not found", 404)
    return user, None


def _validation_error(exc):
    messages = []
    for field, errors in exc.messages.items():
        if errors:
            messages.append(f"{field}: {errors[0]}")
    message = "; ".join(messages) if messages else "invalid payload"
    return error_response("VALIDATION_ERROR", message, 422, details=exc.messages)


@bp.get('/me')
@jwt_required()
def me():
    user, error = _get_user_or_404(get_jwt_identity())
    if error:
        return error
    return ok(_private_schema.dump(user))


@bp.patch('/me')
@jwt_required()
def update_me():
    user, error = _get_user_or_404(get_jwt_identity())
    if error:
        return error

    payload = request.get_json() or {}
    try:
        updates = _update_schema.load(payload, partial=True)
    except ValidationError as exc:
        return _validation_error(exc)

    for field, value in updates.items():
        setattr(user, field, value)

    db.session.commit()
    return ok(_private_schema.dump(user))


@bp.put('/<user_id>/onboarding-completed')
@jwt_required()
def update_onboarding_completed(user_id):
    user, error = _get_user_or_404(get_jwt_identity())
    if error:
        return error

    payload = request.get_json() or {}
    completed = payload.get("completed")
    if not isinstance(completed, bool):
        return error_response("VALIDATION_ERROR", "completed must be a boolean", 422)

    user.onboarding_completed = completed
    db.session.commit()
    return ok(_private_schema.dump(user))


@bp.delete('/me')
@jwt_required()
def delete_me():
    user, error = _get_user_or_404(get_jwt_identity())
    if error:
        return error

    payload = request.get_json() or {}
    code = (payload.get("code") or "").strip()
    code_error = consume_verification_code(user.phone or user.email or "", code)
    if code_error:
        return code_error

    masked_phone = mask_phone(user.phone or "")
    revoked_tokens = revoke_all_user_tokens(user.id)
    user.phone = None
    user.email = None
    user.nickname = "已注销用户"
    user.avatar_url = ""
    user.bio = ""
    user.deleted_at = now_utc()
    Strategy.query.filter(
        Strategy.owner_id == user.id,
        Strategy.is_public.is_(False),
        Strategy.deleted_at.is_(None),
    ).update({"deleted_at": now_utc()}, synchronize_session=False)
    log_audit(
        operator_id=user.id,
        action="user_delete",
        target_type="user",
        target_id=user.id,
        details={"phone": masked_phone, "status": "deleted"},
    )
    db.session.commit()
    blacklist_refresh_tokens(revoked_tokens)

    response = current_app.response_class(
        response=current_app.json.dumps(ok({"message": "账号已注销，所有个人数据已清除"})),
        status=200,
        mimetype='application/json',
    )
    clear_refresh_cookie(response)
    return response


@bp.get('/<user_id>/strategies')
def get_user_strategies(user_id):
    user, error = _get_user_or_404(user_id)
    if error:
        return error

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    pagination = (
        Strategy.query
        .filter_by(owner_id=user.id, is_public=True)
        .order_by(Strategy.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    items = [
        {
            "id": strategy.id,
            "name": strategy.name,
            "category": strategy.category,
            "returns": strategy.returns,
            "max_drawdown": strategy.max_drawdown,
            "win_rate": strategy.win_rate,
            "tags": strategy.tags or [],
        }
        for strategy in pagination.items
    ]

    return ok({
        "items": items,
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
    })


@bp.get('/<user_id>/posts')
def get_user_posts(user_id):
    user, error = _get_user_or_404(user_id)
    if error:
        return error

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    pagination = (
        Post.query
        .filter(Post.user_id == user.id, Post.content.isnot(None))
        .order_by(Post.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    items = []
    for post in pagination.items:
        content = post.content or ""
        items.append({
            "id": post.id,
            "content": content[:200],
            "likes_count": post.likes_count or 0,
            "comments_count": post.comments_count or 0,
            "created_at": format_beijing_iso(post.created_at) if post.created_at else None,
        })

    return ok({
        "items": items,
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
    })


@bp.get('/me/quota')
@jwt_required()
def get_my_quota():
    user, error = _get_user_or_404(get_jwt_identity())
    if error:
        return error

    quota = ensure_user_quota(user.id, plan_level=user.plan_level)
    db.session.commit()

    plan_limit_raw = get_plan_limit(quota.plan_level)
    if math.isinf(plan_limit_raw):
        remaining = "unlimited"
    else:
        remaining = max(0, int(plan_limit_raw) - quota.used_count)

    return ok({
        "plan_level": quota.plan_level,
        "used_count": quota.used_count,
        "plan_limit": serialize_plan_limit(quota.plan_level),
        "remaining": remaining,
        "reset_at": format_beijing_iso(quota.reset_at),
    })


@bp.get('/<user_id>')
def get_user_profile(user_id):
    user, error = _get_user_or_404(user_id)
    if error:
        return error
    return ok(_public_schema.dump(user))

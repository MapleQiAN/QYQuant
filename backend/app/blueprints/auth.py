import hashlib
import re
import secrets
from datetime import datetime, timezone

from flask import current_app, request
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
from flask_smorest import Blueprint

from ..extensions import db
from ..models import AuditLog, RefreshToken, User
from ..quota import ensure_user_quota
from ..utils.auth import (
    REFRESH_COOKIE_NAME,
    as_utc,
    blacklist_refresh_tokens,
    clear_refresh_cookie,
    revoke_all_user_tokens,
    revoke_token_record,
    seconds_until,
    validate_code_shape,
)
from ..utils.redis_client import get_auth_store
from ..utils.response import error_response, ok
from ..utils.sms import get_sms_sender
from ..utils.time import now_utc


bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

PHONE_RE = re.compile(r'^1[3-9]\d{9}$')


def _hash_token(token):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def _mask_phone(phone):
    return f"{phone[:3]}****{phone[-4:]}"


def _build_login_payload(user, access_token):
    payload = ok(
        {
            "user_id": user.id,
            "phone": _mask_phone(user.phone or ""),
            "nickname": user.nickname,
            "plan_level": user.plan_level,
        }
    )
    payload["access_token"] = access_token
    return payload


def _set_refresh_cookie(response, token, max_age):
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        token,
        max_age=max_age,
        httponly=True,
        secure=current_app.config["JWT_COOKIE_SECURE"],
        samesite=current_app.config["JWT_COOKIE_SAMESITE"],
        path='/api/v1/auth',
    )


def _create_refresh_token_record(user):
    refresh_token = create_refresh_token(identity=user.id)
    decoded = decode_token(refresh_token)
    expires_at = datetime.fromtimestamp(decoded["exp"], timezone.utc)
    record = RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(refresh_token),
        jti=decoded["jti"],
        expires_at=expires_at,
    )
    db.session.add(record)
    return refresh_token, record, decoded


def _decode_refresh_cookie():
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not token:
        return None, None, error_response("UNAUTHORIZED", "未登录", 401)

    try:
        decoded = decode_token(token)
        if decoded.get("type") != "refresh":
            return None, None, error_response("INVALID_TOKEN", "无效的登录状态", 401)
    except Exception:
        return None, None, error_response("TOKEN_EXPIRED", "登录已过期，请重新登录", 401)
    return token, decoded, None


def _validate_phone(phone):
    if not PHONE_RE.match(phone or ""):
        return error_response("INVALID_PHONE", "手机号格式不正确", 422)
    return None


def _issue_code():
    fixed_code = current_app.config.get("AUTH_FIXED_SMS_CODE")
    if fixed_code:
        return fixed_code
    return ''.join(str(secrets.randbelow(10)) for _ in range(6))


def _find_refresh_record(token):
    token_hash = _hash_token(token)
    return RefreshToken.query.filter_by(token_hash=token_hash).one_or_none()


@bp.post('/send-code')
def send_code():
    payload = request.get_json() or {}
    phone = (payload.get('phone') or '').strip()

    phone_error = _validate_phone(phone)
    if phone_error:
        return phone_error

    store = get_auth_store()
    retry_after = store.get_throttle_remaining(phone)
    if retry_after > 0:
        return error_response(
            "RATE_LIMITED",
            f"请 {retry_after} 秒后重试",
            429,
            details={"retry_after": retry_after},
        )

    code = _issue_code()
    store.set_verification_code(phone, code, ttl=current_app.config["AUTH_SMS_CODE_TTL"])
    store.mark_code_sent(phone, ttl=current_app.config["AUTH_SMS_THROTTLE_SECONDS"])
    get_sms_sender().send_code(phone, code)
    return ok({"message": "验证码已发送"})


@bp.post('/login')
def login():
    payload = request.get_json() or {}
    phone = (payload.get('phone') or '').strip()
    code = (payload.get('code') or '').strip()
    nickname = (payload.get('nickname') or '').strip()

    phone_error = _validate_phone(phone)
    if phone_error:
        return phone_error

    code_error = validate_code_shape(code)
    if code_error:
        return code_error

    store = get_auth_store()
    if store.get_failed_attempts(phone) >= current_app.config["AUTH_SMS_MAX_FAILURES"]:
        return error_response("TOO_MANY_ATTEMPTS", "验证码尝试次数过多，请稍后重试", 429)

    saved_code = store.get_verification_code(phone)
    if saved_code != code:
        attempts = store.increment_failed_attempts(phone, ttl=current_app.config["AUTH_SMS_LOCK_SECONDS"])
        if attempts >= current_app.config["AUTH_SMS_MAX_FAILURES"]:
            return error_response("TOO_MANY_ATTEMPTS", "验证码尝试次数过多，请稍后重试", 429)
        return error_response("INVALID_CODE", "验证码错误或已过期", 422)

    user = User.query.filter_by(phone=phone).one_or_none()
    if user is not None and user.deleted_at is not None:
        user = None
    if user is None:
        if not nickname:
            return error_response("NICKNAME_REQUIRED", "首次登录需要填写昵称", 422)
        user = User(phone=phone, nickname=nickname)
        db.session.add(user)
        db.session.flush()
        db.session.add(
            AuditLog(
                operator_id=user.id,
                action='register',
                target_type='user',
                target_id=user.id,
                details={"phone": _mask_phone(phone)},
            )
        )

    ensure_user_quota(user.id, plan_level=user.plan_level)

    store.delete_verification_code(phone)
    store.reset_failed_attempts(phone)

    access_token = create_access_token(identity=user.id)
    refresh_token, token_record, decoded = _create_refresh_token_record(user)
    db.session.commit()

    response = current_app.response_class(
        response=current_app.json.dumps(_build_login_payload(user, access_token)),
        status=200,
        mimetype='application/json',
    )
    _set_refresh_cookie(response, refresh_token, seconds_until(token_record.expires_at))
    return response


@bp.post('/refresh')
def refresh():
    token, decoded, error = _decode_refresh_cookie()
    if error:
        return error

    store = get_auth_store()
    if store.is_token_blacklisted(decoded["jti"]):
        return error_response("TOKEN_REVOKED", "登录已失效，请重新登录", 401)

    record = _find_refresh_record(token)
    if record is None or as_utc(record.expires_at) <= datetime.now(timezone.utc):
        return error_response("TOKEN_EXPIRED", "登录已过期，请重新登录", 401)

    if record.revoked_at is not None:
        revoked_tokens = revoke_all_user_tokens(record.user_id)
        db.session.commit()
        blacklist_refresh_tokens(revoked_tokens)
        return error_response("TOKEN_REVOKED", "登录已失效，请重新登录", 401)

    revoke_token_record(record)
    store.blacklist_token(record.jti, seconds_until(record.expires_at))

    user = db.session.get(User, record.user_id)
    access_token = create_access_token(identity=user.id)
    refresh_token, new_record, _ = _create_refresh_token_record(user)
    db.session.commit()

    payload = ok({"access_token": access_token})
    response = current_app.response_class(
        response=current_app.json.dumps(payload),
        status=200,
        mimetype='application/json',
    )
    _set_refresh_cookie(response, refresh_token, seconds_until(new_record.expires_at))
    return response


@bp.post('/logout')
def logout():
    token, decoded, error = _decode_refresh_cookie()
    if error:
        return error

    record = _find_refresh_record(token)
    if record is not None:
        revoke_token_record(record)
        get_auth_store().blacklist_token(decoded["jti"], seconds_until(record.expires_at))
        db.session.commit()

    payload = ok({"message": "已成功登出"})
    response = current_app.response_class(
        response=current_app.json.dumps(payload),
        status=200,
        mimetype='application/json',
    )
    clear_refresh_cookie(response)
    return response

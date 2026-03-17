import re
from datetime import datetime, timezone

from flask import current_app

from ..models import RefreshToken
from .redis_client import get_auth_store
from .response import error_response
from .time import now_utc


CODE_RE = re.compile(r"^\d{6}$")
REFRESH_COOKIE_NAME = "refresh_token"


def as_utc(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def seconds_until(expires_at):
    now = datetime.now(timezone.utc)
    return max(int((as_utc(expires_at) - now).total_seconds()), 0)


def clear_refresh_cookie(response):
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        "",
        max_age=0,
        expires=0,
        httponly=True,
        secure=current_app.config["JWT_COOKIE_SECURE"],
        samesite=current_app.config["JWT_COOKIE_SAMESITE"],
        path="/api/v1/auth",
    )


def validate_code_shape(code):
    if not CODE_RE.match(code or ""):
        return error_response("INVALID_CODE", "验证码错误或已过期", 422)
    return None


def consume_verification_code(phone, code):
    code_error = validate_code_shape(code)
    if code_error:
        return code_error

    store = get_auth_store()
    saved_code = store.get_verification_code(phone)
    if saved_code != code:
        return error_response("INVALID_CODE", "验证码错误或已过期", 422)

    store.delete_verification_code(phone)
    store.reset_failed_attempts(phone)
    return None


def revoke_token_record(record):
    if record and record.revoked_at is None:
        record.revoked_at = now_utc()


def revoke_all_user_tokens(user_id):
    active_tokens = (
        RefreshToken.query.filter_by(user_id=user_id)
        .filter(RefreshToken.revoked_at.is_(None))
        .all()
    )
    for token in active_tokens:
        revoke_token_record(token)
    return active_tokens


def blacklist_refresh_tokens(tokens):
    store = get_auth_store()
    for token in tokens:
        store.blacklist_token(token.jti, seconds_until(token.expires_at))

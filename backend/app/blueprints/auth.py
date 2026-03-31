import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app, request
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token, get_jwt_identity, jwt_required
from flask_mail import Message
from flask_smorest import Blueprint
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db, mail
from ..models import AuditLog, PasswordResetToken, RefreshToken, User
from ..quota import ensure_user_quota
from ..schemas import UserPrivateSchema
from ..utils.auth import (
    REFRESH_COOKIE_NAME,
    as_utc,
    blacklist_refresh_tokens,
    clear_refresh_cookie,
    consume_verification_code,
    revoke_all_user_tokens,
    revoke_token_record,
    seconds_until,
)
from ..utils.response import error_response, ok
from ..utils.time import now_utc


bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
PHONE_RE = re.compile(r'^1\d{10}$')
_private_schema = UserPrivateSchema()
PASSWORD_RESET_TTL_MINUTES = 30


def _hash_token(token):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def _mask_email(email):
    if not email or '@' not in email:
        return ''
    local_part, domain = email.split('@', 1)
    visible = local_part[:2] if len(local_part) > 2 else local_part[:1]
    return f"{visible}***@{domain}"


def _build_login_payload(user, access_token):
    payload = ok(
        {
            "user_id": user.id,
            "email": _mask_email(user.email or ""),
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
    return refresh_token, record


def _decode_refresh_cookie():
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not token:
        return None, None, error_response("UNAUTHORIZED", "Unauthorized", 401)

    try:
        decoded = decode_token(token)
        if decoded.get("type") != "refresh":
            return None, None, error_response("INVALID_TOKEN", "Invalid login state", 401)
    except Exception:
        return None, None, error_response("TOKEN_EXPIRED", "Login expired", 401)
    return token, decoded, None


def _validate_email(email):
    if not EMAIL_RE.match(email or ""):
        return error_response("INVALID_EMAIL", "Invalid email address", 422)
    return None


def _validate_phone(phone):
    if not PHONE_RE.match(phone or ""):
        return error_response("INVALID_PHONE", "Invalid phone number", 422)
    return None


def _validate_password(password):
    if len(password or "") < 8:
        return error_response("INVALID_PASSWORD", "Password must be at least 8 characters", 422)
    return None


def _issue_auth_response(user):
    access_token = create_access_token(identity=user.id)
    refresh_token, token_record = _create_refresh_token_record(user)
    db.session.commit()

    response = current_app.response_class(
        response=current_app.json.dumps(_build_login_payload(user, access_token)),
        status=200,
        mimetype='application/json',
    )
    _set_refresh_cookie(response, refresh_token, seconds_until(token_record.expires_at))
    return response


def _find_active_user_by_email(email):
    user = User.query.filter_by(email=email).one_or_none()
    if user is not None and user.deleted_at is not None:
        return None
    return user


def _find_active_user_by_phone(phone):
    user = User.query.filter_by(phone=phone).one_or_none()
    if user is not None and user.deleted_at is not None:
        return None
    return user


def _get_current_user():
    user = db.session.get(User, get_jwt_identity())
    if user is None or user.deleted_at is not None:
        return None
    return user


def _issue_password_reset_token():
    return secrets.token_urlsafe(32)


def _find_password_reset_token(token):
    return PasswordResetToken.query.filter_by(token_hash=_hash_token(token)).one_or_none()


def _send_password_reset_email(email, token):
    reset_link = f"/reset-password?token={token}"
    mail.send(
        Message(
            subject="QY Quant password reset",
            recipients=[email],
            body=f"Use this link to reset your password: {reset_link}",
            html=f"<p>Use this link to reset your password:</p><p>{reset_link}</p>",
        )
    )


@bp.post('/register')
def register():
    payload = request.get_json() or {}
    email = (payload.get('email') or '').strip().lower()
    password = payload.get('password') or ''
    nickname = (payload.get('nickname') or '').strip()

    email_error = _validate_email(email)
    if email_error:
        return email_error
    password_error = _validate_password(password)
    if password_error:
        return password_error
    if not nickname:
        return error_response("NICKNAME_REQUIRED", "Nickname is required for registration", 422)

    user = _find_active_user_by_email(email)
    if user is None:
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            nickname=nickname,
        )
        db.session.add(user)
        db.session.flush()
        db.session.add(
            AuditLog(
                operator_id=user.id,
                action='register',
                target_type='user',
                target_id=user.id,
                details={"email": _mask_email(email), "method": "password"},
            )
        )
    elif user.password_hash:
        return error_response("EMAIL_EXISTS", "Email already registered", 409)
    else:
        user.password_hash = generate_password_hash(password)
        user.nickname = nickname or user.nickname

    ensure_user_quota(user.id, plan_level=user.plan_level)
    return _issue_auth_response(user)


@bp.post('/login')
def login():
    payload = request.get_json() or {}
    phone = (payload.get('phone') or '').strip()
    if phone:
        phone_error = _validate_phone(phone)
        if phone_error:
            return phone_error

        code = (payload.get('code') or '').strip()
        code_error = consume_verification_code(phone, code)
        if code_error:
            return code_error

        user = _find_active_user_by_phone(phone)
        if user is None:
            nickname = (payload.get('nickname') or '').strip()
            if not nickname:
                return error_response("NICKNAME_REQUIRED", "Nickname is required for first login", 422)
            user = User(phone=phone, nickname=nickname)
            db.session.add(user)
            db.session.flush()

        if user.is_banned:
            return error_response("USER_BANNED", "璐﹀彿宸茶灏佺", 403)

        ensure_user_quota(user.id, plan_level=user.plan_level)
        return _issue_auth_response(user)

    email = (payload.get('email') or '').strip().lower()
    password = payload.get('password') or ''

    email_error = _validate_email(email)
    if email_error:
        return email_error
    password_error = _validate_password(password)
    if password_error:
        return password_error

    user = _find_active_user_by_email(email)
    if user is None or not user.password_hash or not check_password_hash(user.password_hash, password):
        return error_response("INVALID_CREDENTIALS", "Invalid email or password", 401)
    if user.is_banned:
        return error_response("USER_BANNED", "账号已被封禁", 403)

    ensure_user_quota(user.id, plan_level=user.plan_level)
    return _issue_auth_response(user)


@bp.post('/forgot-password')
def forgot_password():
    payload = request.get_json() or {}
    email = (payload.get('email') or '').strip().lower()

    email_error = _validate_email(email)
    if email_error:
        return email_error

    user = _find_active_user_by_email(email)
    if user is not None:
        token = _issue_password_reset_token()
        reset_record = PasswordResetToken(
            user_id=user.id,
            token_hash=_hash_token(token),
            expires_at=now_utc() + timedelta(minutes=PASSWORD_RESET_TTL_MINUTES),
        )
        db.session.add(reset_record)
        db.session.add(
            AuditLog(
                operator_id=user.id,
                action='forgot_password',
                target_type='user',
                target_id=user.id,
                details={"email": _mask_email(email)},
            )
        )
        db.session.commit()
        _send_password_reset_email(email, token)
    return ok({"message": "If the account exists, a reset email has been sent."})


@bp.post('/reset-password')
def reset_password():
    payload = request.get_json() or {}
    token = (payload.get('token') or '').strip()
    password = payload.get('password') or ''

    password_error = _validate_password(password)
    if password_error:
        return password_error
    if not token:
        return error_response("INVALID_TOKEN", "Invalid reset token", 422)

    reset_record = _find_password_reset_token(token)
    if reset_record is None or reset_record.used_at is not None or as_utc(reset_record.expires_at) <= now_utc():
        return error_response("INVALID_TOKEN", "Invalid or expired reset token", 422)

    user = db.session.get(User, reset_record.user_id)
    if user is None or user.deleted_at is not None:
        return error_response("INVALID_TOKEN", "Invalid or expired reset token", 422)

    user.password_hash = generate_password_hash(password)
    reset_record.used_at = now_utc()
    revoked_tokens = revoke_all_user_tokens(user.id, reason='password_reset')
    db.session.add(
        AuditLog(
            operator_id=user.id,
            action='reset_password',
            target_type='user',
            target_id=user.id,
            details={"email": _mask_email(user.email or "")},
        )
    )
    db.session.commit()
    blacklist_refresh_tokens(revoked_tokens)

    return ok({"message": "Password reset successful"})


@bp.post('/refresh')
def refresh():
    token, decoded, error = _decode_refresh_cookie()
    if error:
        return error

    record = RefreshToken.query.filter_by(token_hash=_hash_token(token)).one_or_none()
    if record is None or as_utc(record.expires_at) <= datetime.now(timezone.utc):
        return error_response("TOKEN_EXPIRED", "Login expired", 401)

    if record.revoked_at is not None:
        if record.revoked_reason == 'rotated':
            revoked_tokens = revoke_all_user_tokens(record.user_id, reason='reuse_detected')
            db.session.commit()
            blacklist_refresh_tokens(revoked_tokens)
        return error_response("TOKEN_REVOKED", "Login has been revoked", 401)

    revoke_token_record(record, reason='rotated')
    user = db.session.get(User, record.user_id)
    if user is None or user.deleted_at is not None:
        db.session.commit()
        return error_response("UNAUTHORIZED", "Unauthorized", 401)

    store_seconds = seconds_until(record.expires_at)
    if store_seconds > 0:
        from ..utils.redis_client import get_auth_store
        get_auth_store().blacklist_token(record.jti, store_seconds)

    access_token = create_access_token(identity=user.id)
    refresh_token, new_record = _create_refresh_token_record(user)
    db.session.commit()

    payload = ok({"access_token": access_token})
    response = current_app.response_class(
        response=current_app.json.dumps(payload),
        status=200,
        mimetype='application/json',
    )
    _set_refresh_cookie(response, refresh_token, seconds_until(new_record.expires_at))
    return response


@bp.get('/profile')
@jwt_required()
def profile():
    user = _get_current_user()
    if user is None:
        return error_response("UNAUTHORIZED", "Unauthorized", 401)
    return ok(_private_schema.dump(user))


@bp.post('/logout')
def logout():
    token, decoded, error = _decode_refresh_cookie()
    if error:
        return error

    record = RefreshToken.query.filter_by(token_hash=_hash_token(token)).one_or_none()
    if record is not None:
        revoke_token_record(record, reason='logout')
        from ..utils.redis_client import get_auth_store
        get_auth_store().blacklist_token(decoded["jti"], seconds_until(record.expires_at))
        db.session.commit()

    payload = ok({"message": "Logged out"})
    response = current_app.response_class(
        response=current_app.json.dumps(payload),
        status=200,
        mimetype='application/json',
    )
    clear_refresh_cookie(response)
    return response

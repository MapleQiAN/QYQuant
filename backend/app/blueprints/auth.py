import hashlib
import re
import secrets
from datetime import datetime, timezone

from flask import current_app, request
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token, get_jwt_identity, jwt_required
from flask_mail import Message
from flask_smorest import Blueprint
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db, mail
from ..models import AuditLog, RefreshToken, User
from ..quota import ensure_user_quota
from ..schemas import UserPrivateSchema
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
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
_private_schema = UserPrivateSchema()


def _hash_token(token):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def _mask_phone(phone):
    return f"{phone[:3]}****{phone[-4:]}"


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
            "phone": _mask_phone(user.phone or ""),
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
    return refresh_token, record, decoded


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


def _validate_phone(phone):
    if not PHONE_RE.match(phone or ""):
        return error_response("INVALID_PHONE", "鎵嬫満鍙锋牸寮忎笉姝ｇ‘", 422)
    return None


def _validate_email(email):
    if not EMAIL_RE.match(email or ""):
        return error_response("INVALID_EMAIL", "Invalid email address", 422)
    return None


def _validate_password(password):
    if len(password or "") < 8:
        return error_response("INVALID_PASSWORD", "Password must be at least 8 characters", 422)
    return None


def _resolve_identifier(payload):
    phone = (payload.get('phone') or '').strip()
    email = (payload.get('email') or '').strip().lower()

    if bool(phone) == bool(email):
        return None, None, error_response(
            "INVALID_IDENTIFIER",
            "Provide exactly one of phone or email",
            422,
        )

    if phone:
        return 'phone', phone, _validate_phone(phone)
    return 'email', email, _validate_email(email)


def _issue_code():
    fixed_code = current_app.config.get("AUTH_FIXED_SMS_CODE")
    if fixed_code:
        return fixed_code
    return ''.join(str(secrets.randbelow(10)) for _ in range(6))


def _find_refresh_record(token):
    token_hash = _hash_token(token)
    return RefreshToken.query.filter_by(token_hash=token_hash).one_or_none()


def _get_current_user():
    user = db.session.get(User, get_jwt_identity())
    if user is None or user.deleted_at is not None:
        return None
    return user


def _find_active_user_by_email(email):
    user = User.query.filter_by(email=email).one_or_none()
    if user is not None and user.deleted_at is not None:
        return None
    return user


def _issue_auth_response(user):
    access_token = create_access_token(identity=user.id)
    refresh_token, token_record, _ = _create_refresh_token_record(user)
    db.session.commit()

    response = current_app.response_class(
        response=current_app.json.dumps(_build_login_payload(user, access_token)),
        status=200,
        mimetype='application/json',
    )
    _set_refresh_cookie(response, refresh_token, seconds_until(token_record.expires_at))
    return response


def _send_email_code(email, code):
    mail.send(
        Message(
            subject="QY Quant verification code",
            recipients=[email],
            body=f"Your verification code is {code}. It expires in 5 minutes.",
            html=(
                "<p>Your verification code is "
                f"<strong>{code}</strong>."
                "</p><p>It expires in 5 minutes.</p>"
            ),
        )
    )


@bp.post('/send-code')
def send_code():
    payload = request.get_json() or {}
    identifier_type, identifier, identifier_error = _resolve_identifier(payload)
    if identifier_error:
        return identifier_error

    store = get_auth_store()
    retry_after = store.get_throttle_remaining(identifier)
    if retry_after > 0:
        return error_response(
            "RATE_LIMITED",
            f"Retry after {retry_after} seconds",
            429,
            details={"retry_after": retry_after},
        )

    code = _issue_code()
    store.set_verification_code(identifier, code, ttl=current_app.config["AUTH_SMS_CODE_TTL"])
    store.mark_code_sent(identifier, ttl=current_app.config["AUTH_SMS_THROTTLE_SECONDS"])
    if identifier_type == 'phone':
        get_sms_sender().send_code(identifier, code)
    else:
        _send_email_code(identifier, code)
    return ok({"message": "验证码已发送"})


@bp.post('/login')
def login():
    payload = request.get_json() or {}
    identifier_type, identifier, identifier_error = _resolve_identifier(payload)
    code = (payload.get('code') or '').strip()
    nickname = (payload.get('nickname') or '').strip()

    if identifier_error:
        return identifier_error

    code_error = validate_code_shape(code)
    if code_error:
        return code_error

    store = get_auth_store()
    if store.get_failed_attempts(identifier) >= current_app.config["AUTH_SMS_MAX_FAILURES"]:
        return error_response("TOO_MANY_ATTEMPTS", "Too many verification attempts, please retry later", 429)

    saved_code = store.get_verification_code(identifier)
    if saved_code != code:
        attempts = store.increment_failed_attempts(identifier, ttl=current_app.config["AUTH_SMS_LOCK_SECONDS"])
        if attempts >= current_app.config["AUTH_SMS_MAX_FAILURES"]:
            return error_response("TOO_MANY_ATTEMPTS", "Too many verification attempts, please retry later", 429)
        return error_response("INVALID_CODE", "Invalid or expired verification code", 422)

    if identifier_type == 'phone':
        user = User.query.filter_by(phone=identifier).one_or_none()
        if user is not None and user.deleted_at is not None:
            user = None
    else:
        user = _find_active_user_by_email(identifier)
    if user is None:
        if not nickname:
            return error_response("NICKNAME_REQUIRED", "Nickname is required for first login", 422)
        user_kwargs = {"nickname": nickname}
        if identifier_type == 'phone':
            user_kwargs["phone"] = identifier
            audit_details = {"phone": _mask_phone(identifier)}
        else:
            user_kwargs["email"] = identifier
            audit_details = {"email": _mask_email(identifier)}
        user = User(**user_kwargs)
        db.session.add(user)
        db.session.flush()
        db.session.add(
            AuditLog(
                operator_id=user.id,
                action='register',
                target_type='user',
                target_id=user.id,
                details=audit_details,
            )
        )
    elif user.is_banned:
        return error_response("USER_BANNED", "账号已被封禁", 403)

    ensure_user_quota(user.id, plan_level=user.plan_level)

    store.delete_verification_code(identifier)
    store.reset_failed_attempts(identifier)

    return _issue_auth_response(user)


@bp.post('/register/password')
def register_with_password():
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
        if nickname:
            user.nickname = nickname

    ensure_user_quota(user.id, plan_level=user.plan_level)
    return _issue_auth_response(user)


@bp.post('/login/password')
def login_with_password():
    payload = request.get_json() or {}
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


@bp.post('/refresh')
def refresh():
    token, decoded, error = _decode_refresh_cookie()
    if error:
        return error

    store = get_auth_store()
    if store.is_token_blacklisted(decoded["jti"]):
        return error_response("TOKEN_REVOKED", "Login has been revoked", 401)

    record = _find_refresh_record(token)
    if record is None or as_utc(record.expires_at) <= datetime.now(timezone.utc):
        return error_response("TOKEN_EXPIRED", "Login expired", 401)

    if record.revoked_at is not None:
        revoked_tokens = revoke_all_user_tokens(record.user_id)
        db.session.commit()
        blacklist_refresh_tokens(revoked_tokens)
        return error_response("TOKEN_REVOKED", "Login has been revoked", 401)

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

    record = _find_refresh_record(token)
    if record is not None:
        revoke_token_record(record)
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

import hashlib
import json
import re
import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app, redirect, request, url_for
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token, get_jwt_identity, jwt_required
from flask_mail import Message
from flask_smorest import Blueprint
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db, mail
from ..models import AuditLog, OAuthIdentity, PasswordResetToken, RefreshToken, User
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
from ..utils.oauth import (
    SUPPORTED_PROVIDERS,
    build_authorization_url,
    exchange_code_for_token,
    fetch_user_profile,
    get_oauth_config,
)
from ..utils.response import error_response, ok
from ..utils.redis_client import get_auth_store
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


# ---------------------------------------------------------------------------
# OAuth endpoints
# ---------------------------------------------------------------------------

OAUTH_STATE_TTL = 600  # 10 minutes
OAUTH_TOKEN_TTL = 60   # 1 minute — one-time use


@bp.get('/oauth/<provider>')
def oauth_initiate(provider):
    if provider not in SUPPORTED_PROVIDERS:
        return error_response("UNSUPPORTED_PROVIDER", f"Unsupported OAuth provider: {provider}", 400)

    client_id, _, _ = get_oauth_config(current_app, provider)
    if not client_id:
        return error_response("OAUTH_NOT_CONFIGURED", f"OAuth for {provider} is not configured", 503)

    state = secrets.token_urlsafe(32)
    store = get_auth_store()
    store._backend.set(f"oauth:state:{state}", provider, ttl=OAUTH_STATE_TTL)

    callback_url = current_app.config.get("FRONTEND_BASE_URL", "http://localhost:5173").rstrip("/")
    redirect_uri = f"{current_app.config.get('SERVER_NAME', 'localhost')}/api/v1/auth/oauth/{provider}/callback"
    if not redirect_uri.startswith("http"):
        redirect_uri = f"http://{redirect_uri}"

    authorization_url = build_authorization_url(current_app, provider, state, redirect_uri)
    return ok({"authorization_url": authorization_url})


@bp.get('/oauth/<provider>/callback')
def oauth_callback(provider):
    if provider not in SUPPORTED_PROVIDERS:
        return error_response("UNSUPPORTED_PROVIDER", "Unsupported OAuth provider", 400)

    code = request.args.get("code", "").strip()
    state = request.args.get("state", "").strip()

    if not code or not state:
        return error_response("INVALID_OAUTH_RESPONSE", "Missing code or state", 400)

    store = get_auth_store()
    state_key = f"oauth:state:{state}"
    stored_provider = store._backend.get(state_key)
    if not stored_provider or stored_provider != provider:
        return error_response("INVALID_STATE", "Invalid or expired OAuth state", 400)
    store._backend.delete(state_key)

    callback_url = current_app.config.get("FRONTEND_BASE_URL", "http://localhost:5173").rstrip("/")
    redirect_uri = f"{current_app.config.get('SERVER_NAME', 'localhost')}/api/v1/auth/oauth/{provider}/callback"
    if not redirect_uri.startswith("http"):
        redirect_uri = f"http://{redirect_uri}"

    try:
        token_data = exchange_code_for_token(current_app, provider, code, redirect_uri)
    except Exception:
        return error_response("TOKEN_EXCHANGE_FAILED", "Failed to exchange OAuth code", 502)

    access_token = token_data.get("access_token", "")
    openid = token_data.get("openid") or token_data.get("sub")

    try:
        profile = fetch_user_profile(current_app, provider, access_token, openid=openid)
    except Exception:
        return error_response("PROFILE_FETCH_FAILED", "Failed to fetch user profile", 502)

    provider_user_id = profile["provider_user_id"]
    if not provider_user_id:
        return error_response("INVALID_PROFILE", "Could not determine user identity", 502)

    identity = OAuthIdentity.query.filter_by(provider=provider, provider_user_id=provider_user_id).one_or_none()

    if identity is not None:
        user = db.session.get(User, identity.user_id)
        if user is None or user.deleted_at is not None:
            return error_response("USER_NOT_FOUND", "User no longer exists", 404)
        if user.is_banned:
            return error_response("USER_BANNED", "账号已被封禁", 403)
    else:
        user_email = profile.get("email")
        user = None
        if user_email:
            user = _find_active_user_by_email(user_email)

        if user is None:
            display_name = profile.get("display_name") or "OAuth User"
            user = User(
                email=user_email,
                nickname=display_name,
                avatar_url=profile.get("avatar_url", ""),
            )
            db.session.add(user)
            db.session.flush()

        identity = OAuthIdentity(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            email=profile.get("email"),
            display_name=profile.get("display_name"),
            avatar_url=profile.get("avatar_url"),
            access_token=access_token,
            raw_profile=profile.get("raw_profile"),
        )
        db.session.add(identity)
        db.session.add(
            AuditLog(
                operator_id=user.id,
                action='oauth_register',
                target_type='user',
                target_id=user.id,
                details={"provider": provider, "email": _mask_email(profile.get("email") or "")},
            )
        )

    identity.access_token = access_token
    identity.updated_at = now_utc()
    ensure_user_quota(user.id, plan_level=user.plan_level)
    db.session.commit()

    oauth_token = secrets.token_urlsafe(32)
    payload = json.dumps({"user_id": user.id, "provider": provider})
    store._backend.set(f"oauth:token:{oauth_token}", payload, ttl=OAUTH_TOKEN_TTL)

    frontend_base = current_app.config.get("FRONTEND_BASE_URL", "http://localhost:5173").rstrip("/")
    return redirect(f"{frontend_base}/auth/oauth/callback?oauth_token={oauth_token}")


@bp.post('/oauth/complete')
def oauth_complete():
    payload_data = request.get_json() or {}
    oauth_token = (payload_data.get("oauth_token") or "").strip()
    if not oauth_token:
        return error_response("MISSING_TOKEN", "Missing oauth_token", 400)

    store = get_auth_store()
    token_key = f"oauth:token:{oauth_token}"
    stored = store._backend.get(token_key)
    if not stored:
        return error_response("INVALID_TOKEN", "Invalid or expired OAuth token", 401)

    store._backend.delete(token_key)

    data = json.loads(stored)
    user_id = data.get("user_id")
    user = db.session.get(User, user_id)
    if user is None or user.deleted_at is not None:
        return error_response("USER_NOT_FOUND", "User no longer exists", 401)

    return _issue_auth_response(user)

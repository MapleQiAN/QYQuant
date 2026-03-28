from datetime import timedelta


def _extract_refresh_cookie(response):
    cookies = response.headers.getlist("Set-Cookie")
    for cookie in cookies:
        if cookie.startswith("refresh_token="):
            return cookie
    return ""


def _extract_refresh_cookie_value(cookie_header):
    if not cookie_header:
        return ""
    return cookie_header.split(";", 1)[0].split("=", 1)[1]


def test_register_creates_email_user_and_returns_tokens(client, app):
    from app.models import User

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "password@example.com",
            "password": "Secret123!",
            "nickname": "PasswordUser",
        },
    )

    assert response.status_code == 200
    assert response.json["data"]["nickname"] == "PasswordUser"
    assert response.json["data"]["email"] == "pa***@example.com"
    assert isinstance(response.json["access_token"], str)
    assert "HttpOnly" in _extract_refresh_cookie(response)

    with app.app_context():
        user = User.query.filter_by(email="password@example.com").one_or_none()
        assert user is not None
        assert user.password_hash


def test_register_rejects_duplicate_email(client):
    first = client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "Secret123!",
            "nickname": "FirstUser",
        },
    )
    assert first.status_code == 200

    second = client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "Secret123!",
            "nickname": "SecondUser",
        },
    )

    assert second.status_code == 409
    assert second.json["error"]["code"] == "EMAIL_EXISTS"


def test_login_returns_tokens_with_email_and_password(client):
    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "Secret123!",
            "nickname": "LoginUser",
        },
    )
    user_id = register.json["data"]["user_id"]

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "Secret123!",
        },
    )

    assert response.status_code == 200
    assert response.json["data"]["user_id"] == user_id
    assert isinstance(response.json["access_token"], str)


def test_login_rejects_invalid_password(client):
    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": "bad-password@example.com",
            "password": "Secret123!",
            "nickname": "PasswordUser",
        },
    )
    assert register.status_code == 200

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "bad-password@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json["error"]["code"] == "INVALID_CREDENTIALS"


def test_forgot_password_returns_success_for_existing_email(client, monkeypatch):
    from app.extensions import mail

    client.post(
        "/api/v1/auth/register",
        json={
            "email": "forgot@example.com",
            "password": "Secret123!",
            "nickname": "ForgotUser",
        },
    )

    sent_messages = []
    monkeypatch.setattr(mail, "send", lambda message: sent_messages.append(message))

    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "forgot@example.com"},
    )

    assert response.status_code == 200
    assert response.json["data"]["message"] == "If the account exists, a reset email has been sent."
    assert len(sent_messages) == 1


def test_forgot_password_returns_same_success_for_missing_email(client, monkeypatch):
    from app.extensions import mail

    sent_messages = []
    monkeypatch.setattr(mail, "send", lambda message: sent_messages.append(message))

    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "missing@example.com"},
    )

    assert response.status_code == 200
    assert response.json["data"]["message"] == "If the account exists, a reset email has been sent."
    assert sent_messages == []


def test_reset_password_updates_hash_and_revokes_existing_refresh_tokens(client, app, monkeypatch):
    from app.extensions import db, mail
    from app.models import PasswordResetToken, User

    login = client.post(
        "/api/v1/auth/register",
        json={
            "email": "reset@example.com",
            "password": "Secret123!",
            "nickname": "ResetUser",
        },
    )
    original_cookie = _extract_refresh_cookie(login)
    assert original_cookie

    monkeypatch.setattr(mail, "send", lambda message: None)
    monkeypatch.setattr("app.blueprints.auth._issue_password_reset_token", lambda: "reset-token-123")

    forgot = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "reset@example.com"},
    )
    assert forgot.status_code == 200

    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": "reset-token-123",
            "password": "NewSecret123!",
        },
    )

    assert response.status_code == 200
    assert response.json["data"]["message"] == "Password reset successful"

    with app.app_context():
        user = User.query.filter_by(email="reset@example.com").one()
        assert user.password_hash
        token_record = PasswordResetToken.query.filter_by(user_id=user.id).one()
        assert token_record.used_at is not None

    old_client = client.application.test_client()
    old_client.set_cookie("refresh_token", _extract_refresh_cookie_value(original_cookie), path="/api/v1/auth")
    refresh = old_client.post("/api/v1/auth/refresh")
    assert refresh.status_code == 401
    assert refresh.json["error"]["code"] == "TOKEN_REVOKED"

    relogin = client.post(
        "/api/v1/auth/login",
        json={
            "email": "reset@example.com",
            "password": "NewSecret123!",
        },
    )
    assert relogin.status_code == 200


def test_reset_password_rejects_reused_token(client, monkeypatch):
    from app.extensions import mail

    client.post(
        "/api/v1/auth/register",
        json={
            "email": "reuse@example.com",
            "password": "Secret123!",
            "nickname": "ReuseUser",
        },
    )

    monkeypatch.setattr(mail, "send", lambda message: None)
    monkeypatch.setattr("app.blueprints.auth._issue_password_reset_token", lambda: "reused-token-123")

    client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "reuse@example.com"},
    )

    first = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "reused-token-123", "password": "NewSecret123!"},
    )
    assert first.status_code == 200

    second = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "reused-token-123", "password": "AnotherSecret123!"},
    )

    assert second.status_code == 422
    assert second.json["error"]["code"] == "INVALID_TOKEN"


def test_reset_password_rejects_expired_token(client, app):
    from app.extensions import db
    from app.models import PasswordResetToken, User
    from app.blueprints.auth import _hash_token
    from app.utils.time import now_utc

    client.post(
        "/api/v1/auth/register",
        json={
            "email": "expired@example.com",
            "password": "Secret123!",
            "nickname": "ExpiredUser",
        },
    )

    with app.app_context():
        user = User.query.filter_by(email="expired@example.com").one()
        db.session.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=_hash_token("expired-token-123"),
                expires_at=now_utc() - timedelta(minutes=1),
            )
        )
        db.session.commit()

    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "expired-token-123", "password": "NewSecret123!"},
    )

    assert response.status_code == 422
    assert response.json["error"]["code"] == "INVALID_TOKEN"


def test_refresh_rotates_refresh_token_and_returns_new_access_token(client):
    login = client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh@example.com",
            "password": "Secret123!",
            "nickname": "RefreshUser",
        },
    )
    first_cookie = _extract_refresh_cookie(login)
    assert first_cookie

    refresh = client.post("/api/v1/auth/refresh")

    assert refresh.status_code == 200
    assert isinstance(refresh.json["data"]["access_token"], str)
    second_cookie = _extract_refresh_cookie(refresh)
    assert second_cookie
    assert second_cookie != first_cookie


def test_refresh_token_reuse_revokes_all_active_sessions(client):
    device_a_login = client.post(
        "/api/v1/auth/register",
        json={"email": "reuse-refresh@example.com", "password": "Secret123!", "nickname": "ReuseRefreshUser"},
    )
    original_cookie = _extract_refresh_cookie(device_a_login)
    assert original_cookie

    rotated = client.post("/api/v1/auth/refresh")
    assert rotated.status_code == 200

    device_b = client.application.test_client()
    device_b_login = device_b.post(
        "/api/v1/auth/login",
        json={"email": "reuse-refresh@example.com", "password": "Secret123!"},
    )
    device_b_cookie = _extract_refresh_cookie(device_b_login)
    assert device_b_cookie

    attacker = client.application.test_client()
    attacker.set_cookie("refresh_token", _extract_refresh_cookie_value(original_cookie), path="/api/v1/auth")
    replay = attacker.post("/api/v1/auth/refresh")
    assert replay.status_code == 401
    assert replay.json["error"]["code"] == "TOKEN_REVOKED"

    device_b.set_cookie("refresh_token", _extract_refresh_cookie_value(device_b_cookie), path="/api/v1/auth")
    compromised_refresh = device_b.post("/api/v1/auth/refresh")
    assert compromised_refresh.status_code == 401
    assert compromised_refresh.json["error"]["code"] == "TOKEN_REVOKED"


def test_profile_returns_private_user_payload(client, app):
    from app.extensions import db
    from app.models import User

    login = client.post(
        "/api/v1/auth/register",
        json={
            "email": "profile@example.com",
            "password": "Secret123!",
            "nickname": "ProfileUser",
        },
    )
    access_token = login.json["access_token"]
    user_id = login.json["data"]["user_id"]

    with app.app_context():
        user = db.session.get(User, user_id)
        user.avatar_url = "https://example.com/profile.png"
        user.bio = "Profile bio"
        user.onboarding_completed = False
        db.session.commit()

    response = client.get(
        "/api/v1/auth/profile",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    data = response.json["data"]
    assert data["id"] == user_id
    assert data["nickname"] == "ProfileUser"
    assert data["email"] == "pr***@example.com"
    assert data["onboarding_completed"] is False


def test_logout_revokes_current_device_refresh_token_only(client):
    device_a_login = client.post(
        "/api/v1/auth/register",
        json={"email": "logout@example.com", "password": "Secret123!", "nickname": "LogoutUser"},
    )
    device_a_cookie = _extract_refresh_cookie(device_a_login)
    assert device_a_cookie

    device_b = client.application.test_client()
    device_b_login = device_b.post(
        "/api/v1/auth/login",
        json={"email": "logout@example.com", "password": "Secret123!"},
    )
    device_b_cookie = _extract_refresh_cookie(device_b_login)
    assert device_b_cookie

    logout = client.post("/api/v1/auth/logout")

    assert logout.status_code == 200
    assert "Max-Age=0" in _extract_refresh_cookie(logout)

    client.set_cookie("refresh_token", _extract_refresh_cookie_value(device_a_cookie), path="/api/v1/auth")
    revoked_refresh = client.post("/api/v1/auth/refresh")
    assert revoked_refresh.status_code == 401
    assert revoked_refresh.json["error"]["code"] == "TOKEN_REVOKED"

    device_b.set_cookie("refresh_token", _extract_refresh_cookie_value(device_b_cookie), path="/api/v1/auth")
    surviving_refresh = device_b.post("/api/v1/auth/refresh")
    assert surviving_refresh.status_code == 200
    assert isinstance(surviving_refresh.json["data"]["access_token"], str)

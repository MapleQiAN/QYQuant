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


def _seed_code(app, phone, code="123456", ttl=300):
    from app.utils.redis_client import get_auth_store

    with app.app_context():
        get_auth_store().set_verification_code(phone, code, ttl=ttl)


def test_send_code_success(client):
    resp = client.post("/api/v1/auth/send-code", json={"phone": "13800138000"})

    assert resp.status_code == 200
    assert resp.json["data"]["message"] == "验证码已发送"


def test_send_code_rate_limited(client):
    first = client.post("/api/v1/auth/send-code", json={"phone": "13800138000"})
    assert first.status_code == 200

    second = client.post("/api/v1/auth/send-code", json={"phone": "13800138000"})

    assert second.status_code == 429
    assert second.json["error"]["code"] == "RATE_LIMITED"
    assert second.json["error"]["details"]["retry_after"] > 0


def test_first_login_registers_user_and_returns_tokens(client):
    _seed_code(client.application, "13800138000")

    resp = client.post(
        "/api/v1/auth/login",
        json={
            "phone": "13800138000",
            "code": "123456",
            "nickname": "量化小白",
        },
    )

    assert resp.status_code == 200
    assert resp.json["data"]["phone"] == "138****8000"
    assert resp.json["data"]["nickname"] == "量化小白"
    assert resp.json["data"]["plan_level"] == "free"
    assert isinstance(resp.json["access_token"], str)
    assert "HttpOnly" in _extract_refresh_cookie(resp)


def test_first_login_creates_default_user_quota(client, app):
    from app.extensions import db
    from app.models import UserQuota

    _seed_code(client.application, "13800138111")

    resp = client.post(
        "/api/v1/auth/login",
        json={
            "phone": "13800138111",
            "code": "123456",
            "nickname": "QuotaInit",
        },
    )

    assert resp.status_code == 200
    user_id = resp.json["data"]["user_id"]

    with app.app_context():
        quota = db.session.get(UserQuota, user_id)
        assert quota is not None
        assert quota.plan_level == "free"
        assert quota.used_count == 0


def test_registered_user_login_reuses_same_user(client):
    _seed_code(client.application, "13800138000")
    first_login = client.post(
        "/api/v1/auth/login",
        json={
            "phone": "13800138000",
            "code": "123456",
            "nickname": "量化小白",
        },
    )
    first_user_id = first_login.json["data"]["user_id"]

    _seed_code(client.application, "13800138000")
    second_login = client.post(
        "/api/v1/auth/login",
        json={
            "phone": "13800138000",
            "code": "123456",
        },
    )

    assert second_login.status_code == 200
    assert second_login.json["data"]["user_id"] == first_user_id


def test_login_rejects_banned_user(client, app):
    from app.extensions import db
    from app.models import User

    _seed_code(client.application, "13800138123")
    first_login = client.post(
        "/api/v1/auth/login",
        json={
            "phone": "13800138123",
            "code": "123456",
            "nickname": "BannedUser",
        },
    )
    assert first_login.status_code == 200
    user_id = first_login.json["data"]["user_id"]

    with app.app_context():
        user = db.session.get(User, user_id)
        user.is_banned = True
        db.session.commit()

    _seed_code(client.application, "13800138123")
    response = client.post(
        "/api/v1/auth/login",
        json={
            "phone": "13800138123",
            "code": "123456",
        },
    )

    assert response.status_code == 403
    assert response.json["error"] == {
        "code": "USER_BANNED",
        "message": "账号已被封禁",
    }


def test_refresh_rotates_refresh_token_and_returns_new_access_token(client):
    _seed_code(client.application, "13800138000")
    login = client.post(
        "/api/v1/auth/login",
        json={
            "phone": "13800138000",
            "code": "123456",
            "nickname": "量化小白",
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


def test_profile_returns_private_user_payload_with_onboarding_state(client, app):
    from app.extensions import db
    from app.models import User

    _seed_code(client.application, "13800138999")
    login = client.post(
        "/api/v1/auth/login",
        json={
            "phone": "13800138999",
            "code": "123456",
            "nickname": "OnboardingUser",
        },
    )
    access_token = login.json["access_token"]
    user_id = login.json["data"]["user_id"]

    with app.app_context():
        user = db.session.get(User, user_id)
        user.avatar_url = "https://example.com/onboarding.png"
        user.bio = "First-time quant user"
        user.onboarding_completed = False
        db.session.commit()

    response = client.get(
        "/api/v1/auth/profile",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    data = response.json["data"]
    assert data["id"] == user_id
    assert data["nickname"] == "OnboardingUser"
    assert data["onboarding_completed"] is False
    assert data["avatar_url"] == "https://example.com/onboarding.png"


def test_logout_revokes_current_device_refresh_token_only(client):
    phone = "13800138000"

    _seed_code(client.application, phone)
    device_a_login = client.post(
        "/api/v1/auth/login",
        json={"phone": phone, "code": "123456", "nickname": "量化小白"},
    )
    device_a_cookie = _extract_refresh_cookie(device_a_login)
    assert device_a_cookie

    device_b = client.application.test_client()
    _seed_code(device_b.application, phone)
    device_b_login = device_b.post(
        "/api/v1/auth/login",
        json={"phone": phone, "code": "123456"},
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

    surviving_refresh = device_b.post("/api/v1/auth/refresh")
    assert surviving_refresh.status_code == 200
    assert isinstance(surviving_refresh.json["data"]["access_token"], str)

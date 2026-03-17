from datetime import datetime, timezone

from app.extensions import db
from app.models import AuditLog, User


def _seed_code(app, phone, code="123456", ttl=300):
    from app.utils.redis_client import get_auth_store

    with app.app_context():
        get_auth_store().set_verification_code(phone, code, ttl=ttl)


def _login_user(client, phone="13800138000", nickname="Trader"):
    response = _login_user_response(client, phone=phone, nickname=nickname)
    assert response.status_code == 200
    return response.json["access_token"], response.json["data"]["user_id"]


def _login_user_response(client, phone="13800138000", nickname="Trader"):
    _seed_code(client.application, phone)
    return client.post(
        "/api/v1/auth/login",
        json={
            "phone": phone,
            "code": "123456",
            "nickname": nickname,
        },
    )


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


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


def test_get_me_requires_auth(client):
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


def test_get_me_returns_private_profile_with_masked_phone_and_beijing_times(client, app):
    token, user_id = _login_user(client, nickname="Alpha")

    with app.app_context():
        user = db.session.get(User, user_id)
        user.avatar_url = "https://example.com/avatar.png"
        user.bio = "Systematic trader"
        user.onboarding_completed = True
        user.created_at = datetime(2026, 3, 14, 10, 0, 0, tzinfo=timezone.utc)
        user.updated_at = datetime(2026, 3, 14, 11, 30, 0, tzinfo=timezone.utc)
        db.session.commit()

    response = client.get("/api/v1/users/me", headers=_auth_headers(token))

    assert response.status_code == 200
    data = response.json["data"]
    assert data["id"] == user_id
    assert data["phone"] == "138****8000"
    assert data["nickname"] == "Alpha"
    assert data["avatar_url"] == "https://example.com/avatar.png"
    assert data["bio"] == "Systematic trader"
    assert data["role"] == "user"
    assert data["plan_level"] == "free"
    assert data["onboarding_completed"] is True
    assert data["created_at"] == "2026-03-14T18:00:00+08:00"
    assert data["updated_at"] == "2026-03-14T19:30:00+08:00"


def test_patch_me_updates_profile_fields_and_keeps_omitted_fields(client, app):
    token, user_id = _login_user(client, nickname="Alpha")

    with app.app_context():
        user = db.session.get(User, user_id)
        user.avatar_url = "https://example.com/original.png"
        user.created_at = datetime(2026, 3, 14, 10, 0, 0, tzinfo=timezone.utc)
        user.updated_at = datetime(2026, 3, 14, 10, 0, 0, tzinfo=timezone.utc)
        db.session.commit()

    response = client.patch(
        "/api/v1/users/me",
        headers=_auth_headers(token),
        json={
            "nickname": "Beta",
            "bio": "Momentum focused",
        },
    )

    assert response.status_code == 200
    data = response.json["data"]
    assert data["nickname"] == "Beta"
    assert data["bio"] == "Momentum focused"
    assert data["avatar_url"] == "https://example.com/original.png"
    assert data["updated_at"].endswith("+08:00")

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.nickname == "Beta"
        assert user.bio == "Momentum focused"
        assert user.avatar_url == "https://example.com/original.png"


def test_patch_me_rejects_invalid_nickname_length(client):
    token, _ = _login_user(client)

    response = client.patch(
        "/api/v1/users/me",
        headers=_auth_headers(token),
        json={"nickname": "A"},
    )

    assert response.status_code == 422
    assert response.json["error"]["code"] == "VALIDATION_ERROR"


def test_patch_me_rejects_bio_longer_than_200_characters(client):
    token, _ = _login_user(client)

    response = client.patch(
        "/api/v1/users/me",
        headers=_auth_headers(token),
        json={"bio": "x" * 201},
    )

    assert response.status_code == 422
    assert response.json["error"]["code"] == "VALIDATION_ERROR"


def test_put_onboarding_completed_updates_only_current_user(client, app):
    token, user_id = _login_user(client, phone="13800138123", nickname="GuideOwner")
    _, other_user_id = _login_user(client, phone="13800138124", nickname="OtherUser")

    response = client.put(
        f"/api/v1/users/{other_user_id}/onboarding-completed",
        headers=_auth_headers(token),
        json={"completed": True},
    )

    assert response.status_code == 200
    assert response.json["data"]["onboarding_completed"] is True

    with app.app_context():
        owner = db.session.get(User, user_id)
        other = db.session.get(User, other_user_id)
        assert owner.onboarding_completed is True
        assert other.onboarding_completed is False


def test_get_public_profile_hides_phone_and_returns_banned_flag(client, app):
    _, user_id = _login_user(client, phone="13900139000", nickname="PublicUser")

    with app.app_context():
        user = db.session.get(User, user_id)
        user.avatar_url = "https://example.com/public.png"
        user.bio = "Public bio"
        user.is_banned = True
        user.created_at = datetime(2026, 3, 14, 10, 0, 0, tzinfo=timezone.utc)
        db.session.commit()

    response = client.get(f"/api/v1/users/{user_id}")

    assert response.status_code == 200
    data = response.json["data"]
    assert data["id"] == user_id
    assert data["nickname"] == "PublicUser"
    assert data["avatar_url"] == "https://example.com/public.png"
    assert data["bio"] == "Public bio"
    assert data["is_banned"] is True
    assert data["created_at"] == "2026-03-14T18:00:00+08:00"
    assert "phone" not in data
    assert "plan_level" not in data


def test_get_public_profile_returns_404_for_deleted_user(client, app):
    _, user_id = _login_user(client, phone="13700137000", nickname="DeletedUser")

    with app.app_context():
        user = db.session.get(User, user_id)
        user.deleted_at = datetime(2026, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        db.session.commit()

    response = client.get(f"/api/v1/users/{user_id}")

    assert response.status_code == 404
    assert response.json["error"]["code"] == "USER_NOT_FOUND"


def test_delete_me_requires_auth(client):
    response = client.delete("/api/v1/users/me", json={"code": "123456"})

    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


def test_delete_me_rejects_invalid_code(client):
    token, _ = _login_user(client, phone="13600136000", nickname="DeleteMe")

    response = client.delete(
        "/api/v1/users/me",
        headers=_auth_headers(token),
        json={"code": "000000"},
    )

    assert response.status_code == 422
    assert response.json["error"]["code"] == "INVALID_CODE"


def test_delete_me_soft_deletes_user_revokes_all_refresh_tokens_and_writes_audit_log(client, app):
    phone = "13500135000"

    device_a = client
    device_a_login = _login_user_response(device_a, phone=phone, nickname="DeleteFlow")
    assert device_a_login.status_code == 200
    access_token = device_a_login.json["access_token"]
    user_id = device_a_login.json["data"]["user_id"]
    device_a_cookie = _extract_refresh_cookie(device_a_login)

    device_b = app.test_client()
    _seed_code(device_b.application, phone)
    device_b_login = device_b.post(
        "/api/v1/auth/login",
        json={"phone": phone, "code": "123456"},
    )
    device_b_cookie = _extract_refresh_cookie(device_b_login)

    _seed_code(app, phone)
    response = device_a.delete(
        "/api/v1/users/me",
        headers=_auth_headers(access_token),
        json={"code": "123456"},
    )

    assert response.status_code == 200
    assert response.json["data"]["message"] == "账号已注销，所有个人数据已清除"
    assert "Max-Age=0" in _extract_refresh_cookie(response)

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        assert user.deleted_at is not None
        assert user.phone is None
        assert user.nickname == "已注销用户"
        assert user.avatar_url == ""
        assert user.bio == ""

        audit_log = (
            AuditLog.query.filter_by(
                operator_id=user_id,
                action="user_delete",
                target_type="user",
                target_id=user_id,
            )
            .order_by(AuditLog.created_at.desc())
            .first()
        )
        assert audit_log is not None

    device_a.set_cookie("refresh_token", _extract_refresh_cookie_value(device_a_cookie), path="/api/v1/auth")
    revoked_a = device_a.post("/api/v1/auth/refresh")
    assert revoked_a.status_code == 401
    assert revoked_a.json["error"]["code"] == "TOKEN_REVOKED"

    device_b.set_cookie("refresh_token", _extract_refresh_cookie_value(device_b_cookie), path="/api/v1/auth")
    revoked_b = device_b.post("/api/v1/auth/refresh")
    assert revoked_b.status_code == 401
    assert revoked_b.json["error"]["code"] == "TOKEN_REVOKED"


def test_deleted_user_access_token_returns_401(client, app):
    access_token, _ = _login_user(client, phone="13400134000", nickname="DeletedToken")
    _seed_code(app, "13400134000")
    delete_response = client.delete(
        "/api/v1/users/me",
        headers=_auth_headers(access_token),
        json={"code": "123456"},
    )
    assert delete_response.status_code == 200

    response = client.get("/api/v1/users/me", headers=_auth_headers(access_token))

    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


def test_deleted_user_phone_can_register_a_new_account(client, app):
    first_access_token, first_user_id = _login_user(client, phone="13300133000", nickname="FirstOwner")
    _seed_code(app, "13300133000")
    delete_response = client.delete(
        "/api/v1/users/me",
        headers=_auth_headers(first_access_token),
        json={"code": "123456"},
    )
    assert delete_response.status_code == 200

    _seed_code(app, "13300133000")
    relogin = client.post(
        "/api/v1/auth/login",
        json={
            "phone": "13300133000",
            "code": "123456",
            "nickname": "SecondOwner",
        },
    )

    assert relogin.status_code == 200
    assert relogin.json["data"]["user_id"] != first_user_id
    assert relogin.json["data"]["nickname"] == "SecondOwner"

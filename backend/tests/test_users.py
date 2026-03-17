from datetime import datetime, timezone

from app.extensions import db
from app.models import User


def _seed_code(app, phone, code="123456", ttl=300):
    from app.utils.redis_client import get_auth_store

    with app.app_context():
        get_auth_store().set_verification_code(phone, code, ttl=ttl)


def _login_user(client, phone="13800138000", nickname="Trader"):
    _seed_code(client.application, phone)
    response = client.post(
        "/api/v1/auth/login",
        json={
            "phone": phone,
            "code": "123456",
            "nickname": nickname,
        },
    )
    assert response.status_code == 200
    return response.json["access_token"], response.json["data"]["user_id"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


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

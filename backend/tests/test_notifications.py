from datetime import datetime, timezone

from sqlalchemy import text

from app.extensions import db
from app.models import Notification, User
from app.utils.notification import create_notification


def _seed_code(app, phone, code="123456", ttl=300):
    from app.utils.redis_client import get_auth_store

    with app.app_context():
        get_auth_store().set_verification_code(phone, code, ttl=ttl)


def _login_user(client, phone="13800138900", nickname="Notifier"):
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


def test_create_notification_adds_unread_record_without_committing(app):
    with app.app_context():
        user = User(phone="13800138901", nickname="UtilityUser")
        db.session.add(user)
        db.session.commit()

        notification = create_notification(
            db.session,
            user_id=user.id,
            type="quota_alert",
            title="Quota alert",
            content="Your quota is nearly exhausted.",
        )

        assert notification.user_id == user.id
        assert notification.is_read is False
        assert notification in db.session.new

        db.session.rollback()
        assert Notification.query.count() == 0


def test_notification_model_exposes_required_indexes(app):
    with app.app_context():
        rows = db.session.execute(
            text("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='notifications'")
        ).fetchall()

    index_names = {row[0] for row in rows}
    assert "ix_notifications_user_id" in index_names
    assert "ix_notifications_created_at" in index_names


def test_notifications_endpoints_require_auth(client):
    unread_response = client.get("/api/v1/notifications/unread-count")
    list_response = client.get("/api/v1/notifications")
    mark_response = client.patch("/api/v1/notifications/notification-1/read")

    assert unread_response.status_code == 401
    assert list_response.status_code == 401
    assert mark_response.status_code == 401
    assert unread_response.json["error"]["code"] == "UNAUTHORIZED"
    assert list_response.json["error"]["code"] == "UNAUTHORIZED"
    assert mark_response.json["error"]["code"] == "UNAUTHORIZED"


def test_get_unread_count_returns_only_current_user_unread_total(client, app):
    token, user_id = _login_user(client, phone="13800138902", nickname="UnreadOwner")
    _, other_user_id = _login_user(client, phone="13800138903", nickname="UnreadOther")

    with app.app_context():
        db.session.add_all(
            [
                Notification(user_id=user_id, type="review", title="Unread 1", is_read=False),
                Notification(user_id=user_id, type="review", title="Unread 2", is_read=False),
                Notification(user_id=user_id, type="review", title="Read 1", is_read=True),
                Notification(user_id=other_user_id, type="review", title="Other unread", is_read=False),
            ]
        )
        db.session.commit()

    response = client.get(
        "/api/v1/notifications/unread-count",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json["data"] == {"count": 2}


def test_get_notifications_returns_paginated_desc_list_with_beijing_times(client, app):
    token, user_id = _login_user(client, phone="13800138904", nickname="ListOwner")

    with app.app_context():
        db.session.add_all(
            [
                Notification(
                    id="notification-1",
                    user_id=user_id,
                    type="review",
                    title="Oldest",
                    content="first item",
                    is_read=True,
                    created_at=datetime(2026, 3, 23, 1, 0, tzinfo=timezone.utc),
                ),
                Notification(
                    id="notification-2",
                    user_id=user_id,
                    type="quota",
                    title="Middle",
                    content="second item",
                    is_read=False,
                    created_at=datetime(2026, 3, 23, 2, 0, tzinfo=timezone.utc),
                ),
                Notification(
                    id="notification-3",
                    user_id=user_id,
                    type="payment",
                    title="Newest",
                    content="third item",
                    is_read=False,
                    created_at=datetime(2026, 3, 23, 3, 0, tzinfo=timezone.utc),
                ),
            ]
        )
        db.session.commit()

    response = client.get(
        "/api/v1/notifications?page=1&per_page=2",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json["data"]] == ["notification-3", "notification-2"]
    assert response.json["meta"] == {"page": 1, "per_page": 2, "total": 3}
    assert response.json["data"][0] == {
        "id": "notification-3",
        "type": "payment",
        "title": "Newest",
        "content": "third item",
        "is_read": False,
        "created_at": "2026-03-23T11:00:00+08:00",
    }


def test_mark_notification_read_updates_only_current_users_notification(client, app):
    owner_token, owner_id = _login_user(client, phone="13800138905", nickname="ReadOwner")
    other_token, other_id = _login_user(client, phone="13800138906", nickname="ReadOther")

    with app.app_context():
        db.session.add_all(
            [
                Notification(id="owner-notification", user_id=owner_id, type="review", title="Owner unread"),
                Notification(id="other-notification", user_id=other_id, type="review", title="Other unread"),
            ]
        )
        db.session.commit()

    success_response = client.patch(
        "/api/v1/notifications/owner-notification/read",
        headers=_auth_headers(owner_token),
    )

    assert success_response.status_code == 200
    assert success_response.json["data"] == {"ok": True}

    with app.app_context():
        owner_notification = db.session.get(Notification, "owner-notification")
        other_notification = db.session.get(Notification, "other-notification")
        assert owner_notification.is_read is True
        assert other_notification.is_read is False

    forbidden_response = client.patch(
        "/api/v1/notifications/other-notification/read",
        headers=_auth_headers(owner_token),
    )

    assert forbidden_response.status_code == 404
    assert forbidden_response.json["error"]["code"] == "NOTIFICATION_NOT_FOUND"
    assert other_token

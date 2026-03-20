from datetime import datetime, timezone

from app.extensions import db
from app.models import Post


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


def _create_community_post(app, *, user_id, content, created_at, title="Community Post"):
    with app.app_context():
        post = Post(
            title=title,
            author="Trader",
            avatar="https://example.com/avatar.png",
            likes=0,
            comments=0,
            timestamp=1,
            tags=[],
            user_id=user_id,
            content=content,
            strategy_id=None,
            likes_count=0,
            comments_count=0,
            created_at=created_at,
        )
        db.session.add(post)
        db.session.commit()
        return post.id


def _create_legacy_post(app, *, user_id, title="Legacy Post"):
    with app.app_context():
        post = Post(
            title=title,
            author="Legacy Trader",
            avatar="https://example.com/legacy.png",
            likes=2,
            comments=1,
            timestamp=1700000000000,
            tags=["legacy"],
            user_id=user_id,
            content=None,
            strategy_id=None,
            likes_count=0,
            comments_count=0,
            created_at=None,
        )
        db.session.add(post)
        db.session.commit()
        return post.id


def test_create_post_requires_auth(client):
    response = client.post("/api/v1/posts", json={"content": "hello"})

    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


def test_create_post_returns_community_payload(client):
    token, user_id = _login_user(client)

    response = client.post(
        "/api/v1/posts",
        headers=_auth_headers(token),
        json={"content": "First post"},
    )

    assert response.status_code == 200
    data = response.json["data"]
    assert data["content"] == "First post"
    assert data["user_id"] == user_id
    assert data["likes_count"] == 0
    assert data["comments_count"] == 0
    assert data["strategy_id"] is None
    assert data["author"]["nickname"] == "Trader"
    assert data["liked"] is False
    assert data["collected"] is False
    assert data["created_at"].endswith("+08:00")


def test_get_posts_returns_newest_first_with_pagination(client, app):
    _, user_id = _login_user(client)
    older_id = _create_community_post(
        app,
        user_id=user_id,
        content="Older",
        created_at=datetime(2026, 3, 20, 8, 0, 0, tzinfo=timezone.utc),
        title="Older Post",
    )
    newer_id = _create_community_post(
        app,
        user_id=user_id,
        content="Newer",
        created_at=datetime(2026, 3, 20, 9, 0, 0, tzinfo=timezone.utc),
        title="Newer Post",
    )

    response = client.get("/api/v1/posts?page=1&per_page=1")

    assert response.status_code == 200
    data = response.json["data"]
    assert data["total"] == 2
    assert data["page"] == 1
    assert data["per_page"] == 1
    assert [item["id"] for item in data["items"]] == [newer_id]
    assert older_id != newer_id


def test_get_posts_excludes_legacy_rows_without_content(client, app):
    _, user_id = _login_user(client)
    _create_legacy_post(app, user_id=user_id)
    community_id = _create_community_post(
        app,
        user_id=user_id,
        content="Community only",
        created_at=datetime(2026, 3, 20, 10, 0, 0, tzinfo=timezone.utc),
    )

    response = client.get("/api/v1/posts")

    assert response.status_code == 200
    items = response.json["data"]["items"]
    assert [item["id"] for item in items] == [community_id]


def test_get_post_detail_returns_404_for_missing_post(client):
    response = client.get("/api/v1/posts/missing-post")

    assert response.status_code == 404
    assert response.json["error"]["code"] == "POST_NOT_FOUND"

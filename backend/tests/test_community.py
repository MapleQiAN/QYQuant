from datetime import datetime, timezone

from app.extensions import db
from app.models import Post, PostComment, PostInteraction


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


def test_like_post_toggles_on_and_off(client, app):
    token, user_id = _login_user(client)
    post_id = _create_community_post(
        app,
        user_id=user_id,
        content="Toggle like",
        created_at=datetime(2026, 3, 20, 10, 0, 0, tzinfo=timezone.utc),
    )

    first = client.post(f"/api/v1/posts/{post_id}/like", headers=_auth_headers(token))
    second = client.post(f"/api/v1/posts/{post_id}/like", headers=_auth_headers(token))

    assert first.status_code == 200
    assert first.json["data"] == {"liked": True, "likes_count": 1}
    assert second.status_code == 200
    assert second.json["data"] == {"liked": False, "likes_count": 0}

    with app.app_context():
        assert PostInteraction.query.filter_by(post_id=post_id, user_id=user_id, type="like").count() == 0


def test_like_post_returns_404_for_missing_post(client):
    token, _ = _login_user(client)

    response = client.post("/api/v1/posts/missing-post/like", headers=_auth_headers(token))

    assert response.status_code == 404
    assert response.json["error"]["code"] == "POST_NOT_FOUND"


def test_collect_post_toggles_on_and_off(client, app):
    token, user_id = _login_user(client)
    post_id = _create_community_post(
        app,
        user_id=user_id,
        content="Toggle collect",
        created_at=datetime(2026, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
    )

    first = client.post(f"/api/v1/posts/{post_id}/collect", headers=_auth_headers(token))
    second = client.post(f"/api/v1/posts/{post_id}/collect", headers=_auth_headers(token))

    assert first.status_code == 200
    assert first.json["data"] == {"collected": True}
    assert second.status_code == 200
    assert second.json["data"] == {"collected": False}

    with app.app_context():
        assert PostInteraction.query.filter_by(post_id=post_id, user_id=user_id, type="collect").count() == 0


def test_get_comments_returns_oldest_first(client, app):
    _, user_id = _login_user(client)
    post_id = _create_community_post(
        app,
        user_id=user_id,
        content="Commented post",
        created_at=datetime(2026, 3, 20, 11, 0, 0, tzinfo=timezone.utc),
    )

    with app.app_context():
        first = PostComment(
            post_id=post_id,
            user_id=user_id,
            content="First comment",
            created_at=datetime(2026, 3, 20, 11, 1, 0, tzinfo=timezone.utc),
        )
        second = PostComment(
            post_id=post_id,
            user_id=user_id,
            content="Second comment",
            created_at=datetime(2026, 3, 20, 11, 2, 0, tzinfo=timezone.utc),
        )
        db.session.add_all([first, second])
        db.session.commit()

    response = client.get(f"/api/v1/posts/{post_id}/comments")

    assert response.status_code == 200
    data = response.json["data"]
    assert data["total"] == 2
    assert [item["content"] for item in data["items"]] == ["First comment", "Second comment"]
    assert data["items"][0]["author"]["nickname"] == "Trader"


def test_create_comment_requires_auth(client, app):
    _, user_id = _login_user(client)
    post_id = _create_community_post(
        app,
        user_id=user_id,
        content="Protected comments",
        created_at=datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc),
    )

    response = client.post(f"/api/v1/posts/{post_id}/comments", json={"content": "hello"})

    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


def test_create_comment_rejects_empty_or_too_long_content(client, app):
    token, user_id = _login_user(client)
    post_id = _create_community_post(
        app,
        user_id=user_id,
        content="Validation comments",
        created_at=datetime(2026, 3, 20, 12, 30, 0, tzinfo=timezone.utc),
    )

    empty_response = client.post(
        f"/api/v1/posts/{post_id}/comments",
        headers=_auth_headers(token),
        json={"content": "   "},
    )
    long_response = client.post(
        f"/api/v1/posts/{post_id}/comments",
        headers=_auth_headers(token),
        json={"content": "x" * 501},
    )

    assert empty_response.status_code == 422
    assert empty_response.json["error"]["code"] == "CONTENT_REQUIRED"
    assert long_response.status_code == 422
    assert long_response.json["error"]["code"] == "CONTENT_TOO_LONG"


def test_create_comment_returns_payload_and_updates_count(client, app):
    token, user_id = _login_user(client)
    post_id = _create_community_post(
        app,
        user_id=user_id,
        content="Happy comments",
        created_at=datetime(2026, 3, 20, 13, 0, 0, tzinfo=timezone.utc),
    )

    response = client.post(
        f"/api/v1/posts/{post_id}/comments",
        headers=_auth_headers(token),
        json={"content": "Nice post"},
    )

    assert response.status_code == 200
    data = response.json["data"]
    assert data["content"] == "Nice post"
    assert data["user_id"] == user_id
    assert data["author"]["nickname"] == "Trader"
    assert data["created_at"].endswith("+08:00")

    with app.app_context():
        post = db.session.get(Post, post_id)
        assert post.comments_count == 1
        assert PostComment.query.filter_by(post_id=post_id).count() == 1

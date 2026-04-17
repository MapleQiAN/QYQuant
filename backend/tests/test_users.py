from datetime import datetime, timezone

from app.extensions import db
from app.models import AuditLog, Post, Strategy, User


def _normalize_email(email=None, phone=None):
    if email:
        return email
    if phone:
        digits = ''.join(ch for ch in phone if ch.isdigit()) or 'user'
        return f"{digits}@example.com"
    return "user@example.com"


def _login_user(client, phone="13800138000", email=None, nickname="Trader"):
    response = _login_user_response(client, phone=phone, email=email, nickname=nickname)
    assert response.status_code == 200
    return response.json["access_token"], response.json["data"]["user_id"]


def _login_user_response(client, phone="13800138000", email=None, nickname="Trader"):
    resolved_email = _normalize_email(email=email, phone=phone)
    register = client.post(
        "/api/v1/auth/register",
        json={"email": resolved_email, "password": "Secret123!", "nickname": nickname},
    )
    if register.status_code == 200:
        return register
    return client.post(
        "/api/v1/auth/login",
        json={"email": resolved_email, "password": "Secret123!"},
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


def _delete_payload(password="Secret123!"):
    return {"password": password}


def _create_strategy(
    app,
    *,
    owner_id,
    strategy_id,
    name,
    created_at,
    is_public,
    category="trend-following",
    returns=12.5,
    max_drawdown=-4.2,
    win_rate=58.0,
    tags=None,
):
    with app.app_context():
        strategy = Strategy(
            id=strategy_id,
            name=name,
            title=name,
            symbol="BTCUSDT",
            status="published" if is_public else "draft",
            description=f"{name} description",
            category=category,
            source="upload",
            owner_id=owner_id,
            created_at=created_at,
            updated_at=created_at,
            last_update=created_at,
            is_public=is_public,
            returns=returns,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            tags=tags or [],
        )
        db.session.add(strategy)
        db.session.commit()
        return strategy.id


def _create_post(
    app,
    *,
    user_id,
    post_id,
    content,
    created_at,
    likes_count=0,
    comments_count=0,
):
    with app.app_context():
        post = Post(
            id=post_id,
            title=f"Title {post_id}",
            author="Trader",
            avatar="https://example.com/avatar.png",
            likes=likes_count,
            comments=comments_count,
            timestamp=1700000000000,
            tags=[],
            user_id=user_id,
            content=content,
            strategy_id=None,
            likes_count=likes_count,
            comments_count=comments_count,
            created_at=created_at,
        )
        db.session.add(post)
        db.session.commit()
        return post.id


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
    assert data["phone"] is None
    assert data["email"] == "13***@example.com"
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


def test_get_user_strategies_returns_only_public_strategies_sorted_by_newest(client, app):
    _, user_id = _login_user(client, phone="13900139001", nickname="StrategyOwner")
    _, other_user_id = _login_user(client, phone="13900139002", nickname="OtherOwner")
    older_public_id = _create_strategy(
        app,
        owner_id=user_id,
        strategy_id="strategy-public-older",
        name="Public Older",
        created_at=1700000000000,
        is_public=True,
        tags=["alpha"],
    )
    newer_public_id = _create_strategy(
        app,
        owner_id=user_id,
        strategy_id="strategy-public-newer",
        name="Public Newer",
        created_at=1700000001000,
        is_public=True,
        tags=["beta", "swing"],
    )
    _create_strategy(
        app,
        owner_id=user_id,
        strategy_id="strategy-private",
        name="Private Strategy",
        created_at=1700000002000,
        is_public=False,
    )
    _create_strategy(
        app,
        owner_id=other_user_id,
        strategy_id="strategy-other-user",
        name="Other User Strategy",
        created_at=1700000003000,
        is_public=True,
    )

    response = client.get(f"/api/v1/users/{user_id}/strategies")

    assert response.status_code == 200
    data = response.json["data"]
    assert [item["id"] for item in data["items"]] == [newer_public_id, older_public_id]
    assert data["total"] == 2
    assert data["page"] == 1
    assert data["per_page"] == 20
    assert data["items"][0] == {
        "id": newer_public_id,
        "name": "Public Newer",
        "category": "trend-following",
        "returns": 12.5,
        "max_drawdown": -4.2,
        "win_rate": 58.0,
        "tags": ["beta", "swing"],
    }


def test_get_user_strategies_returns_empty_list_when_no_public_strategies(client):
    _, user_id = _login_user(client, phone="13900139003", nickname="NoPublicStrategy")

    response = client.get(f"/api/v1/users/{user_id}/strategies")

    assert response.status_code == 200
    assert response.json["data"] == {
        "items": [],
        "total": 0,
        "page": 1,
        "per_page": 20,
    }


def test_get_user_strategies_returns_404_for_missing_user(client):
    response = client.get("/api/v1/users/missing-user/strategies")

    assert response.status_code == 404
    assert response.json["error"]["code"] == "USER_NOT_FOUND"


def test_get_user_strategies_allows_anonymous_requests(client, app):
    _, user_id = _login_user(client, phone="13900139004", nickname="AnonymousVisible")
    _create_strategy(
        app,
        owner_id=user_id,
        strategy_id="strategy-anon",
        name="Anonymous Visible Strategy",
        created_at=1700000000000,
        is_public=True,
    )

    response = client.get(f"/api/v1/users/{user_id}/strategies")

    assert response.status_code == 200
    assert response.json["data"]["total"] == 1


def test_get_user_posts_returns_newest_public_community_posts(client, app):
    _, user_id = _login_user(client, phone="13900139005", nickname="PostOwner")
    _create_post(
        app,
        user_id=user_id,
        post_id="post-older",
        content="Older post",
        created_at=datetime(2026, 3, 14, 10, 0, 0, tzinfo=timezone.utc),
        likes_count=1,
        comments_count=2,
    )
    newer_post_id = _create_post(
        app,
        user_id=user_id,
        post_id="post-newer",
        content="Newer post",
        created_at=datetime(2026, 3, 14, 11, 0, 0, tzinfo=timezone.utc),
        likes_count=5,
        comments_count=8,
    )

    response = client.get(f"/api/v1/users/{user_id}/posts")

    assert response.status_code == 200
    data = response.json["data"]
    assert [item["id"] for item in data["items"]] == [newer_post_id, "post-older"]
    assert data["total"] == 2
    assert data["items"][0] == {
        "id": newer_post_id,
        "content": "Newer post",
        "likes_count": 5,
        "comments_count": 8,
        "created_at": "2026-03-14T19:00:00+08:00",
    }


def test_get_user_posts_returns_empty_list_when_no_posts(client):
    _, user_id = _login_user(client, phone="13900139006", nickname="NoPosts")

    response = client.get(f"/api/v1/users/{user_id}/posts")

    assert response.status_code == 200
    assert response.json["data"] == {
        "items": [],
        "total": 0,
        "page": 1,
        "per_page": 20,
    }


def test_get_user_posts_returns_404_for_missing_user(client):
    response = client.get("/api/v1/users/missing-user/posts")

    assert response.status_code == 404
    assert response.json["error"]["code"] == "USER_NOT_FOUND"


def test_get_user_posts_truncates_content_to_200_characters(client, app):
    _, user_id = _login_user(client, phone="13900139007", nickname="LongPost")
    _create_post(
        app,
        user_id=user_id,
        post_id="post-long",
        content="x" * 250,
        created_at=datetime(2026, 3, 14, 12, 0, 0, tzinfo=timezone.utc),
    )

    response = client.get(f"/api/v1/users/{user_id}/posts")

    assert response.status_code == 200
    assert response.json["data"]["items"][0]["content"] == "x" * 200


def test_get_user_posts_excludes_legacy_rows_without_content(client, app):
    _, user_id = _login_user(client, phone="13900139008", nickname="LegacyFilter")
    _create_post(
        app,
        user_id=user_id,
        post_id="legacy-post",
        content=None,
        created_at=None,
    )
    _create_post(
        app,
        user_id=user_id,
        post_id="community-post",
        content="Community post",
        created_at=datetime(2026, 3, 14, 13, 0, 0, tzinfo=timezone.utc),
    )

    response = client.get(f"/api/v1/users/{user_id}/posts")

    assert response.status_code == 200
    assert [item["id"] for item in response.json["data"]["items"]] == ["community-post"]


def test_deleted_user_returns_404_for_profile_related_public_endpoints(client, app):
    _, user_id = _login_user(client, phone="13900139009", nickname="DeletedPublicUser")

    with app.app_context():
        user = db.session.get(User, user_id)
        user.deleted_at = datetime(2026, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        db.session.commit()

    for path in (
        f"/api/v1/users/{user_id}",
        f"/api/v1/users/{user_id}/strategies",
        f"/api/v1/users/{user_id}/posts",
    ):
        response = client.get(path)
        assert response.status_code == 404
        assert response.json["error"]["code"] == "USER_NOT_FOUND"


def test_delete_me_requires_auth(client):
    response = client.delete("/api/v1/users/me", json=_delete_payload())

    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


def test_delete_me_rejects_invalid_password(client):
    token, _ = _login_user(client, phone="13600136000", nickname="DeleteMe")

    response = client.delete(
        "/api/v1/users/me",
        headers=_auth_headers(token),
        json=_delete_payload("WrongSecret123!"),
    )

    assert response.status_code == 422
    assert response.json["error"]["code"] == "INVALID_PASSWORD"


def test_delete_me_soft_deletes_user_revokes_all_refresh_tokens_and_writes_audit_log(client, app):
    phone = "13500135000"
    email = _normalize_email(phone=phone)

    device_a = client
    device_a_login = _login_user_response(device_a, phone=phone, nickname="DeleteFlow")
    assert device_a_login.status_code == 200
    access_token = device_a_login.json["access_token"]
    user_id = device_a_login.json["data"]["user_id"]
    device_a_cookie = _extract_refresh_cookie(device_a_login)

    device_b = app.test_client()
    device_b_login = device_b.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Secret123!"},
    )
    device_b_cookie = _extract_refresh_cookie(device_b_login)

    response = device_a.delete(
        "/api/v1/users/me",
        headers=_auth_headers(access_token),
        json=_delete_payload(),
    )

    assert response.status_code == 200
    assert response.json["data"]["message"] == "账号已注销，所有个人数据已清除"
    assert "Max-Age=0" in _extract_refresh_cookie(response)

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        assert user.deleted_at is not None
        assert user.phone is None
        assert user.email is None
        assert user.password_hash is None
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
    delete_response = client.delete(
        "/api/v1/users/me",
        headers=_auth_headers(access_token),
        json=_delete_payload(),
    )
    assert delete_response.status_code == 200

    response = client.get("/api/v1/users/me", headers=_auth_headers(access_token))

    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


def test_deleted_user_email_can_register_a_new_account(client, app):
    email = _normalize_email(phone="13300133000")
    first_access_token, first_user_id = _login_user(client, phone="13300133000", nickname="FirstOwner")
    delete_response = client.delete(
        "/api/v1/users/me",
        headers=_auth_headers(first_access_token),
        json=_delete_payload(),
    )
    assert delete_response.status_code == 200

    relogin = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Secret123!",
            "nickname": "SecondOwner",
        },
    )

    assert relogin.status_code == 200
    assert relogin.json["data"]["user_id"] != first_user_id
    assert relogin.json["data"]["nickname"] == "SecondOwner"


def test_get_my_quota_returns_quota_data(client):
    token, _ = _login_user(client, phone="13900139100", nickname="QuotaUser")

    response = client.get(
        "/api/v1/users/me/quota",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    data = response.json["data"]
    assert data["plan_level"] == "free"
    assert isinstance(data["used_count"], int)
    assert data["plan_limit"] == 10
    assert isinstance(data["remaining"], int)
    assert data["remaining"] == data["plan_limit"] - data["used_count"]
    assert data["reset_at"] is None


def test_get_my_quota_requires_auth(client):
    response = client.get("/api/v1/users/me/quota")

    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


def test_get_my_quota_auto_creates_quota_record(client, app):
    from app.models import UserQuota

    token, user_id = _login_user(client, phone="13900139101", nickname="NewQuotaUser")

    with app.app_context():
        quota = db.session.get(UserQuota, user_id)
        if quota is not None:
            db.session.delete(quota)
            db.session.commit()

    response = client.get(
        "/api/v1/users/me/quota",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200

    with app.app_context():
        quota = db.session.get(UserQuota, user_id)
        assert quota is not None
        assert quota.plan_level == "free"
        assert quota.used_count == 0


def test_get_my_quota_reflects_plan_level_change(client, app):
    from app.models import User

    token, user_id = _login_user(client, phone="13900139102", nickname="PlanChanger")

    with app.app_context():
        user = db.session.get(User, user_id)
        user.plan_level = "pro"
        db.session.commit()

    response = client.get(
        "/api/v1/users/me/quota",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    data = response.json["data"]
    assert data["plan_level"] == "pro"
    assert data["plan_limit"] == 500
    assert data["remaining"] == 500 - data["used_count"]


def test_account_deletion_soft_deletes_private_strategies(client, app):
    phone = "13900139200"
    token, user_id = _login_user(client, phone=phone, nickname="StrategyOwner")
    private_id = _create_strategy(
        app,
        owner_id=user_id,
        strategy_id="strategy-private-del",
        name="Private Strategy",
        created_at=1700000000000,
        is_public=False,
    )
    public_id = _create_strategy(
        app,
        owner_id=user_id,
        strategy_id="strategy-public-del",
        name="Public Strategy",
        created_at=1700000001000,
        is_public=True,
    )

    response = client.delete(
        "/api/v1/users/me",
        headers=_auth_headers(token),
        json=_delete_payload(),
    )
    assert response.status_code == 200

    with app.app_context():
        private_strategy = db.session.get(Strategy, private_id)
        assert private_strategy.deleted_at is not None

        public_strategy = db.session.get(Strategy, public_id)
        assert public_strategy.deleted_at is None


def test_account_deletion_preserves_imported_copies(client, app):
    phone_a = "13900139210"
    phone_b = "13900139211"
    token_a, user_a_id = _login_user(client, phone=phone_a, nickname="PublisherA")
    _, user_b_id = _login_user(client, phone=phone_b, nickname="ImporterB")

    source_id = _create_strategy(
        app,
        owner_id=user_a_id,
        strategy_id="strategy-source-pub",
        name="Public Source Strategy",
        created_at=1700000000000,
        is_public=True,
    )
    imported_id = _create_strategy(
        app,
        owner_id=user_b_id,
        strategy_id="strategy-imported-copy",
        name="Imported Copy",
        created_at=1700000001000,
        is_public=False,
    )
    with app.app_context():
        imported = db.session.get(Strategy, imported_id)
        imported.source_strategy_id = source_id
        db.session.commit()

    response = client.delete(
        "/api/v1/users/me",
        headers=_auth_headers(token_a),
        json=_delete_payload(),
    )
    assert response.status_code == 200

    with app.app_context():
        imported = db.session.get(Strategy, imported_id)
        assert imported.deleted_at is None
        assert imported.owner_id == user_b_id


def test_list_strategies_excludes_soft_deleted(client, app):
    phone = "13900139220"
    token, user_id = _login_user(client, phone=phone, nickname="SoftDelOwner")
    _create_strategy(
        app,
        owner_id=user_id,
        strategy_id="strategy-soft-del",
        name="Soft Deleted Strategy",
        created_at=1700000000000,
        is_public=False,
    )
    _create_strategy(
        app,
        owner_id=user_id,
        strategy_id="strategy-active",
        name="Active Strategy",
        created_at=1700000001000,
        is_public=False,
    )

    with app.app_context():
        soft_deleted = db.session.get(Strategy, "strategy-soft-del")
        soft_deleted.deleted_at = datetime(2026, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        db.session.commit()

    response = client.get(
        "/api/v1/strategies/",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    data = response.json["data"]
    ids = [item["id"] for item in data["items"]]
    assert "strategy-soft-del" not in ids
    assert "strategy-active" in ids


def test_get_my_quota_preserves_basic_plan_snapshot(client, app):
    from app.models import User, UserQuota

    token, user_id = _login_user(client, phone="13900139103", nickname="LegacyPlanUser")

    with app.app_context():
        user = db.session.get(User, user_id)
        user.plan_level = "basic"
        quota = db.session.get(UserQuota, user_id)
        quota.plan_level = "basic"
        quota.used_count = 12
        db.session.commit()

    response = client.get(
        "/api/v1/users/me/quota",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    data = response.json["data"]
    assert data["plan_level"] == "basic"
    assert data["plan_limit"] == 100
    assert data["remaining"] == 88

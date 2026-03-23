from app.models import User


def _seed_code(app, phone, code="123456", ttl=300):
    from app.utils.redis_client import get_auth_store

    with app.app_context():
        get_auth_store().set_verification_code(phone, code, ttl=ttl)


def _login_user(client, phone="13800138200", nickname="PayUser"):
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


def test_create_payment_order_requires_auth(client):
    response = client.post(
        "/api/v1/payments/orders",
        json={"plan_level": "lite", "provider": "wechat"},
    )

    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


def test_create_payment_order_returns_pending_order_payload(client):
    token, _ = _login_user(client)

    response = client.post(
        "/api/v1/payments/orders",
        headers=_auth_headers(token),
        json={"plan_level": "lite", "provider": "wechat"},
    )

    assert response.status_code == 201
    data = response.json["data"]
    assert data["plan_level"] == "lite"
    assert data["amount"] == 200
    assert data["provider"] == "wechat"
    assert data["order_id"]
    assert data["pay_url"].startswith("https://")


def test_create_payment_order_rejects_legacy_plan_names(client):
    token, _ = _login_user(client, phone="13800138201", nickname="LegacyPlanReject")

    response = client.post(
        "/api/v1/payments/orders",
        headers=_auth_headers(token),
        json={"plan_level": "basic", "provider": "wechat"},
    )

    assert response.status_code == 400
    assert response.json["error"]["code"] == "INVALID_PLAN"
    assert "lite" in response.json["error"]["message"]
    assert "expert" in response.json["error"]["message"]


def test_create_payment_order_rejects_free_plan(client):
    token, _ = _login_user(client, phone="13800138202", nickname="FreePlanReject")

    response = client.post(
        "/api/v1/payments/orders",
        headers=_auth_headers(token),
        json={"plan_level": "free", "provider": "wechat"},
    )

    assert response.status_code == 400
    assert response.json["error"]["code"] == "INVALID_PLAN"


def test_create_payment_order_rejects_invalid_provider(client):
    token, _ = _login_user(client, phone="13800138203", nickname="ProviderReject")

    response = client.post(
        "/api/v1/payments/orders",
        headers=_auth_headers(token),
        json={"plan_level": "pro", "provider": "paypal"},
    )

    assert response.status_code == 400
    assert response.json["error"]["code"] == "INVALID_PROVIDER"


def test_create_payment_order_is_idempotent_for_same_plan_level(client):
    token, _ = _login_user(client, phone="13800138204", nickname="IdempotentPayUser")

    first = client.post(
        "/api/v1/payments/orders",
        headers=_auth_headers(token),
        json={"plan_level": "pro", "provider": "wechat"},
    )
    second = client.post(
        "/api/v1/payments/orders",
        headers=_auth_headers(token),
        json={"plan_level": "pro", "provider": "wechat"},
    )

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json["data"]["order_id"] == second.json["data"]["order_id"]
    assert second.json["data"]["plan_level"] == "pro"


def test_create_payment_order_keeps_current_user_scope(client, app):
    token, user_id = _login_user(client, phone="13800138205", nickname="ScopedPayUser")

    response = client.post(
        "/api/v1/payments/orders",
        headers=_auth_headers(token),
        json={"plan_level": "expert", "provider": "alipay"},
    )

    assert response.status_code == 201

    with app.app_context():
        user = User.query.filter_by(id=user_id).one()
        assert user.plan_level == "free"

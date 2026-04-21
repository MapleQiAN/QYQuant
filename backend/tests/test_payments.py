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


def _create_pending_order(client, token, plan_level="plus", provider="wechat"):
    response = client.post(
        "/api/v1/payments/orders",
        headers=_auth_headers(token),
        json={"plan_level": plan_level, "provider": provider},
    )
    assert response.status_code == 201
    return response.json["data"]["order_id"]


def test_create_payment_order_requires_auth(client):
    response = client.post(
        "/api/v1/payments/orders",
        json={"plan_level": "plus", "provider": "wechat"},
    )

    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


def test_create_payment_order_returns_pending_order_payload(client):
    token, _ = _login_user(client)

    response = client.post(
        "/api/v1/payments/orders",
        headers=_auth_headers(token),
        json={"plan_level": "plus", "provider": "wechat"},
    )

    assert response.status_code == 201
    data = response.json["data"]
    assert data["plan_level"] == "plus"
    assert data["amount"] == 69
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
    assert "go" in response.json["error"]["message"]
    assert "ultra" in response.json["error"]["message"]


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


def test_create_payment_order_is_idempotent_for_same_plan_and_provider(client):
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


def test_create_payment_order_separates_pending_orders_by_provider(client):
    token, _ = _login_user(client, phone="13800138205", nickname="ProviderScopedPending")

    wechat = client.post(
        "/api/v1/payments/orders",
        headers=_auth_headers(token),
        json={"plan_level": "plus", "provider": "wechat"},
    )
    alipay = client.post(
        "/api/v1/payments/orders",
        headers=_auth_headers(token),
        json={"plan_level": "plus", "provider": "alipay"},
    )

    assert wechat.status_code == 201
    assert alipay.status_code == 201
    assert wechat.json["data"]["order_id"] != alipay.json["data"]["order_id"]
    assert wechat.json["data"]["provider"] == "wechat"
    assert alipay.json["data"]["provider"] == "alipay"


def test_create_payment_order_keeps_current_user_scope(client, app):
    token, user_id = _login_user(client, phone="13800138206", nickname="ScopedPayUser")

    response = client.post(
        "/api/v1/payments/orders",
        headers=_auth_headers(token),
        json={"plan_level": "ultra", "provider": "alipay"},
    )

    assert response.status_code == 201

    with app.app_context():
        user = User.query.filter_by(id=user_id).one()
        assert user.plan_level == "free"


def test_wechat_webhook_activates_subscription(client, app):
    token, user_id = _login_user(client, phone="13800138210", nickname="WxWebhookUser")
    order_id = _create_pending_order(client, token, plan_level="plus", provider="wechat")

    response = client.post(
        "/api/v1/payments/webhook/wechat",
        json={"order_id": order_id, "transaction_id": "wx_tx_001"},
    )

    assert response.status_code == 200
    assert response.json["data"]["message"] == "ok"

    with app.app_context():
        from app.extensions import db
        from app.models import PaymentOrder, Subscription, User

        order = db.session.get(PaymentOrder, order_id)
        assert order.status == "paid"
        assert order.provider_order_id == "wx_tx_001"

        subscription = Subscription.query.filter_by(user_id=user_id).one()
        assert subscription.plan_level == "plus"
        assert subscription.status == "active"

        user = db.session.get(User, user_id)
        assert user.plan_level == "plus"


def test_wechat_webhook_is_idempotent(client, app):
    token, user_id = _login_user(client, phone="13800138211", nickname="WxIdempUser")
    order_id = _create_pending_order(client, token, plan_level="pro", provider="wechat")

    first = client.post("/api/v1/payments/webhook/wechat", json={"order_id": order_id})
    second = client.post("/api/v1/payments/webhook/wechat", json={"order_id": order_id})

    assert first.status_code == 200
    assert second.status_code == 200

    with app.app_context():
        from app.models import Subscription

        assert Subscription.query.filter_by(user_id=user_id).count() == 1


def test_wechat_webhook_rejects_invalid_order_id(client):
    response = client.post(
        "/api/v1/payments/webhook/wechat",
        json={"order_id": "nonexistent-order-id"},
    )

    assert response.status_code == 400
    assert response.json["error"]["code"] == "INVALID_CALLBACK"


def test_wechat_webhook_requires_order_id(client):
    response = client.post("/api/v1/payments/webhook/wechat", json={})

    assert response.status_code == 400
    assert response.json["error"]["code"] == "INVALID_CALLBACK"


def test_wechat_webhook_rejects_provider_mismatch(client, app):
    token, _ = _login_user(client, phone="13800138212", nickname="WrongProviderWebhookUser")
    order_id = _create_pending_order(client, token, plan_level="plus", provider="alipay")

    response = client.post(
        "/api/v1/payments/webhook/wechat",
        json={"order_id": order_id, "transaction_id": "wx_tx_wrong"},
    )

    assert response.status_code == 400
    assert response.json["error"]["code"] == "INVALID_CALLBACK"

    with app.app_context():
        from app.extensions import db
        from app.models import PaymentOrder

        order = db.session.get(PaymentOrder, order_id)
        assert order.status == "pending"
        assert order.provider_order_id is None


def test_alipay_webhook_activates_subscription(client, app):
    token, user_id = _login_user(client, phone="13800138213", nickname="AliWebhookUser")
    order_id = _create_pending_order(client, token, plan_level="ultra", provider="alipay")

    response = client.post(
        "/api/v1/payments/webhook/alipay",
        json={"order_id": order_id, "trade_no": "ali_tx_001"},
    )

    assert response.status_code == 200
    assert response.data == b"success"

    with app.app_context():
        from app.extensions import db
        from app.models import PaymentOrder, User

        order = db.session.get(PaymentOrder, order_id)
        assert order.provider_order_id == "ali_tx_001"

        user = db.session.get(User, user_id)
        assert user.plan_level == "ultra"


def test_alipay_webhook_is_idempotent(client, app):
    token, user_id = _login_user(client, phone="13800138214", nickname="AliIdempUser")
    order_id = _create_pending_order(client, token, plan_level="plus", provider="alipay")

    first = client.post("/api/v1/payments/webhook/alipay", json={"order_id": order_id})
    second = client.post("/api/v1/payments/webhook/alipay", json={"order_id": order_id})

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.data == b"success"

    with app.app_context():
        from app.models import Subscription

        assert Subscription.query.filter_by(user_id=user_id).count() == 1


def test_webhook_rejects_duplicate_provider_order_id(client, app):
    token, _ = _login_user(client, phone="13800138215", nickname="DuplicateProviderOrderUser")
    first_order_id = _create_pending_order(client, token, plan_level="plus", provider="wechat")
    second_order_id = _create_pending_order(client, token, plan_level="pro", provider="wechat")

    first = client.post(
        "/api/v1/payments/webhook/wechat",
        json={"order_id": first_order_id, "transaction_id": "wx_tx_dup"},
    )
    second = client.post(
        "/api/v1/payments/webhook/wechat",
        json={"order_id": second_order_id, "transaction_id": "wx_tx_dup"},
    )

    assert first.status_code == 200
    assert second.status_code == 400

    with app.app_context():
        from app.extensions import db
        from app.models import PaymentOrder

        second_order = db.session.get(PaymentOrder, second_order_id)
        assert second_order.status == "pending"
        assert second_order.provider_order_id is None


def test_webhook_sends_notification(client, app):
    token, user_id = _login_user(client, phone="13800138216", nickname="NotifTestUser")
    order_id = _create_pending_order(client, token, plan_level="plus", provider="wechat")

    client.post("/api/v1/payments/webhook/wechat", json={"order_id": order_id})

    with app.app_context():
        from app.models import Notification

        notification = Notification.query.filter_by(
            user_id=user_id, type="subscription_activated"
        ).first()
        assert notification is not None
        assert "plus" in notification.content
        assert "200" in notification.content


def test_ultra_notification_does_not_show_unlimited_literal(client, app):
    token, user_id = _login_user(client, phone="13800138217", nickname="UltraNotifUser")
    order_id = _create_pending_order(client, token, plan_level="ultra", provider="wechat")

    client.post("/api/v1/payments/webhook/wechat", json={"order_id": order_id})

    with app.app_context():
        from app.models import Notification

        notification = Notification.query.filter_by(
            user_id=user_id, type="subscription_activated"
        ).first()
        assert notification is not None
        assert "无限次" in notification.content
        assert "unlimited" not in notification.content


def test_wechat_webhook_rejects_non_sandbox(client, app):
    app.config["PAYMENT_SANDBOX"] = False
    token, _ = _login_user(client, phone="13800138218", nickname="NonSandboxWx")
    app.config["PAYMENT_SANDBOX"] = True
    order_id = _create_pending_order(client, token, plan_level="plus", provider="wechat")

    app.config["PAYMENT_SANDBOX"] = False
    response = client.post("/api/v1/payments/webhook/wechat", json={"order_id": order_id})
    app.config["PAYMENT_SANDBOX"] = True

    assert response.status_code == 400

    with app.app_context():
        from app.extensions import db
        from app.models import PaymentOrder

        order = db.session.get(PaymentOrder, order_id)
        assert order.status == "pending"


def test_alipay_webhook_rejects_non_sandbox(client, app):
    app.config["PAYMENT_SANDBOX"] = False
    token, _ = _login_user(client, phone="13800138219", nickname="NonSandboxAli")
    app.config["PAYMENT_SANDBOX"] = True
    order_id = _create_pending_order(client, token, plan_level="plus", provider="alipay")

    app.config["PAYMENT_SANDBOX"] = False
    response = client.post("/api/v1/payments/webhook/alipay", json={"order_id": order_id})
    app.config["PAYMENT_SANDBOX"] = True

    assert response.status_code == 400
    assert response.data == b"fail"

    with app.app_context():
        from app.extensions import db
        from app.models import PaymentOrder

        order = db.session.get(PaymentOrder, order_id)
        assert order.status == "pending"


def test_alipay_webhook_captures_provider_order_id(client, app):
    token, _ = _login_user(client, phone="13800138220", nickname="AliTradeNoUser")
    order_id = _create_pending_order(client, token, plan_level="pro", provider="alipay")

    response = client.post(
        "/api/v1/payments/webhook/alipay",
        json={"order_id": order_id, "trade_no": "ali_tx_002"},
    )

    assert response.status_code == 200

    with app.app_context():
        from app.extensions import db
        from app.models import PaymentOrder

        order = db.session.get(PaymentOrder, order_id)
        assert order.provider_order_id == "ali_tx_002"


def test_webhook_writes_audit_log(client, app):
    token, user_id = _login_user(client, phone="13800138221", nickname="AuditTestUser")
    order_id = _create_pending_order(client, token, plan_level="pro", provider="wechat")

    client.post("/api/v1/payments/webhook/wechat", json={"order_id": order_id})

    with app.app_context():
        from app.models import AuditLog

        log = AuditLog.query.filter_by(
            action="subscription_activated", target_id=user_id
        ).first()
        assert log is not None
        assert log.details["plan_level"] == "pro"


def test_webhook_sets_quota_reset_at_to_next_month_first_day(client, app):
    token, user_id = _login_user(client, phone="13800138222", nickname="QuotaResetAtUser")
    order_id = _create_pending_order(client, token, plan_level="plus", provider="wechat")

    client.post("/api/v1/payments/webhook/wechat", json={"order_id": order_id})

    with app.app_context():
        from datetime import timedelta, timezone

        from app.models import UserQuota

        quota = UserQuota.query.filter_by(user_id=user_id).one()
        beijing_tz = timezone(timedelta(hours=8))
        reset_at = quota.reset_at.astimezone(beijing_tz)

        assert quota.plan_level == "plus"
        assert reset_at.day == 1
        assert reset_at.hour == 0
        assert reset_at.minute == 0

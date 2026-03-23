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


# ── Story 8.3: Webhook 回调处理 ──────────────────────────────────────────────

def _create_pending_order(client, token, plan_level='lite', provider='wechat'):
    """辅助：创建一个 pending 订单，返回 order_id"""
    resp = client.post(
        '/api/v1/payments/orders',
        headers=_auth_headers(token),
        json={'plan_level': plan_level, 'provider': provider},
    )
    assert resp.status_code == 201
    return resp.json['data']['order_id']


def test_wechat_webhook_activates_subscription(client, app):
    """微信回调成功：订单变为 paid，用户 plan_level 升级，存在 subscription 记录"""
    token, user_id = _login_user(client, phone='13800138210', nickname='WxWebhookUser')
    order_id = _create_pending_order(client, token, plan_level='lite', provider='wechat')

    resp = client.post(
        '/api/v1/payments/webhook/wechat',
        json={'order_id': order_id, 'transaction_id': 'wx_tx_001'},
    )

    assert resp.status_code == 200
    assert resp.json['data']['message'] == 'ok'

    with app.app_context():
        from app.models import PaymentOrder, Subscription, User
        from app.extensions import db
        order = db.session.get(PaymentOrder, order_id)
        assert order.status == 'paid'
        assert order.provider_order_id == 'wx_tx_001'

        sub = Subscription.query.filter_by(user_id=user_id).first()
        assert sub is not None
        assert sub.plan_level == 'lite'
        assert sub.status == 'active'

        user = db.session.get(User, user_id)
        assert user.plan_level == 'lite'


def test_wechat_webhook_idempotent(client, app):
    """重复回调不重复激活：第二次回调直接返回 200，不创建第二个 subscription"""
    token, user_id = _login_user(client, phone='13800138211', nickname='WxIdempUser')
    order_id = _create_pending_order(client, token, plan_level='pro', provider='wechat')

    resp1 = client.post('/api/v1/payments/webhook/wechat', json={'order_id': order_id})
    assert resp1.status_code == 200

    resp2 = client.post('/api/v1/payments/webhook/wechat', json={'order_id': order_id})
    assert resp2.status_code == 200

    with app.app_context():
        from app.models import Subscription
        count = Subscription.query.filter_by(user_id=user_id).count()
        assert count == 1


def test_wechat_webhook_invalid_order_id(client):
    """不存在的 order_id 返回 400"""
    resp = client.post(
        '/api/v1/payments/webhook/wechat',
        json={'order_id': 'nonexistent-order-id'},
    )
    assert resp.status_code == 400
    assert resp.json['error']['code'] == 'INVALID_CALLBACK'


def test_wechat_webhook_missing_order_id(client):
    """缺少 order_id 返回 400"""
    resp = client.post('/api/v1/payments/webhook/wechat', json={})
    assert resp.status_code == 400


def test_alipay_webhook_activates_subscription(client, app):
    """支付宝回调成功：响应纯文本 'success'，用户套餐升级"""
    token, user_id = _login_user(client, phone='13800138212', nickname='AliWebhookUser')
    order_id = _create_pending_order(client, token, plan_level='expert', provider='alipay')

    resp = client.post(
        '/api/v1/payments/webhook/alipay',
        json={'order_id': order_id, 'trade_no': 'ali_tx_001'},
    )

    assert resp.status_code == 200
    assert resp.data == b'success'

    with app.app_context():
        from app.models import User
        from app.extensions import db
        user = db.session.get(User, user_id)
        assert user.plan_level == 'expert'


def test_alipay_webhook_idempotent(client, app):
    """支付宝重复回调：第二次直接返回 success，不重复激活"""
    token, user_id = _login_user(client, phone='13800138213', nickname='AliIdempUser')
    order_id = _create_pending_order(client, token, plan_level='lite', provider='alipay')

    resp1 = client.post('/api/v1/payments/webhook/alipay', json={'order_id': order_id})
    resp2 = client.post('/api/v1/payments/webhook/alipay', json={'order_id': order_id})

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp2.data == b'success'

    with app.app_context():
        from app.models import Subscription
        count = Subscription.query.filter_by(user_id=user_id).count()
        assert count == 1


def test_webhook_sends_notification(client, app):
    """回调激活后发送站内通知"""
    token, user_id = _login_user(client, phone='13800138214', nickname='NotifTestUser')
    order_id = _create_pending_order(client, token, plan_level='lite', provider='wechat')

    client.post('/api/v1/payments/webhook/wechat', json={'order_id': order_id})

    with app.app_context():
        from app.models import Notification
        notif = Notification.query.filter_by(
            user_id=user_id, type='subscription_activated'
        ).first()
        assert notif is not None
        assert 'lite' in notif.content
        assert '200' in notif.content


def test_webhook_expert_notification_shows_unlimited(client, app):
    """expert 套餐通知文本应显示"无限次"而非 unlimited"""
    token, user_id = _login_user(client, phone='13800138216', nickname='ExpertNotifUser')
    order_id = _create_pending_order(client, token, plan_level='expert', provider='wechat')

    client.post('/api/v1/payments/webhook/wechat', json={'order_id': order_id})

    with app.app_context():
        from app.models import Notification
        notif = Notification.query.filter_by(
            user_id=user_id, type='subscription_activated'
        ).first()
        assert notif is not None
        assert '无限次' in notif.content
        assert 'unlimited' not in notif.content


def test_wechat_webhook_rejects_non_sandbox(client, app):
    """非沙箱模式下微信 Webhook 拒绝所有请求"""
    app.config['PAYMENT_SANDBOX'] = False
    token, user_id = _login_user(client, phone='13800138217', nickname='NonSandboxWx')
    app.config['PAYMENT_SANDBOX'] = True
    order_id = _create_pending_order(client, token, plan_level='lite', provider='wechat')

    app.config['PAYMENT_SANDBOX'] = False
    resp = client.post('/api/v1/payments/webhook/wechat', json={'order_id': order_id})
    app.config['PAYMENT_SANDBOX'] = True

    assert resp.status_code == 400

    with app.app_context():
        from app.models import PaymentOrder
        from app.extensions import db
        order = db.session.get(PaymentOrder, order_id)
        assert order.status == 'pending'


def test_alipay_webhook_rejects_non_sandbox(client, app):
    """非沙箱模式下支付宝 Webhook 拒绝所有请求"""
    app.config['PAYMENT_SANDBOX'] = False
    token, user_id = _login_user(client, phone='13800138218', nickname='NonSandboxAli')
    app.config['PAYMENT_SANDBOX'] = True
    order_id = _create_pending_order(client, token, plan_level='lite', provider='alipay')

    app.config['PAYMENT_SANDBOX'] = False
    resp = client.post('/api/v1/payments/webhook/alipay', json={'order_id': order_id})
    app.config['PAYMENT_SANDBOX'] = True

    assert resp.status_code == 400
    assert resp.data == b'fail'

    with app.app_context():
        from app.models import PaymentOrder
        from app.extensions import db
        order = db.session.get(PaymentOrder, order_id)
        assert order.status == 'pending'


def test_alipay_webhook_captures_provider_order_id(client, app):
    """支付宝 JSON 模式下 trade_no 应被正确记录为 provider_order_id"""
    token, user_id = _login_user(client, phone='13800138219', nickname='AliTradeNoUser')
    order_id = _create_pending_order(client, token, plan_level='pro', provider='alipay')

    resp = client.post(
        '/api/v1/payments/webhook/alipay',
        json={'order_id': order_id, 'trade_no': 'ali_tx_002'},
    )
    assert resp.status_code == 200

    with app.app_context():
        from app.models import PaymentOrder
        from app.extensions import db
        order = db.session.get(PaymentOrder, order_id)
        assert order.provider_order_id == 'ali_tx_002'


def test_webhook_writes_audit_log(client, app):
    """回调激活后写入审计日志"""
    token, user_id = _login_user(client, phone='13800138215', nickname='AuditTestUser')
    order_id = _create_pending_order(client, token, plan_level='pro', provider='wechat')

    client.post('/api/v1/payments/webhook/wechat', json={'order_id': order_id})

    with app.app_context():
        from app.models import AuditLog
        log = AuditLog.query.filter_by(
            action='subscription_activated', target_id=user_id
        ).first()
        assert log is not None
        assert log.details['plan_level'] == 'pro'

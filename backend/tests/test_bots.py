from decimal import Decimal
from datetime import date

from app.extensions import db
from app.models import BotEquitySnapshot, BotInstance, IntegrationProvider, Order, Strategy, User, UserIntegration, UserIntegrationSecret


def _login_user(client, email="bots@example.com", nickname="BotUser"):
    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Secret123!", "nickname": nickname},
    )
    assert register.status_code == 200
    return register.json["access_token"], register.json["data"]["user_id"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _seed_strategy(app, *, strategy_id, owner_id, name="托管策略"):
    with app.app_context():
        strategy = Strategy(
            id=strategy_id,
            name=name,
            title=name,
            symbol="000001.XSHG",
            status="draft",
            owner_id=owner_id,
            returns=0,
            win_rate=0,
            max_drawdown=0,
            tags=["托管", "实盘"],
            trades=0,
        )
        db.session.add(strategy)
        db.session.commit()


def _set_user_plan(app, *, user_id, plan_level):
    with app.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        user.plan_level = plan_level
        db.session.commit()


def _seed_broker_integration(app, *, user_id, provider_key="xtquant"):
    with app.app_context():
        provider = db.session.get(IntegrationProvider, provider_key)
        if provider is None:
            provider = IntegrationProvider(
                key=provider_key,
                name="XtQuant",
                type="broker_account",
                mode="local_connector",
                capabilities={"account_summary": True, "positions": True},
                config_schema={"public_fields": ["endpoint", "account_id"], "secret_fields": []},
                is_enabled=True,
            )
            db.session.add(provider)
            db.session.flush()

        integration = UserIntegration(
            user_id=user_id,
            provider_key=provider_key,
            display_name="主账户",
            status="active",
            config_public={"endpoint": "tcp://127.0.0.1:19000", "account_id": "A10001"},
        )
        db.session.add(integration)
        db.session.flush()
        db.session.add(
            UserIntegrationSecret(
                integration_id=integration.id,
                encrypted_payload="ciphertext",
                schema_version=1,
            )
        )
        db.session.commit()
        return integration.id


def test_create_managed_bot_persists_snapshot_and_returns_dashboard_fields(client, app, monkeypatch):
    token, user_id = _login_user(client, email="managed-create@example.com", nickname="ManagedCreate")
    _seed_strategy(app, strategy_id="strategy-managed-1", owner_id=user_id, name="沪深择时")
    integration_id = _seed_broker_integration(app, user_id=user_id)

    class FakeBrokerAdapter:
        def get_account_summary(self, integration):
            assert integration.id == integration_id
            return {"currency": "CNY", "available_cash": "200000.00", "equity": "320000.00"}

    from app.services import bots as bots_service

    monkeypatch.setattr(bots_service.integrations_service, "attach_secret_payload", lambda integration, session=None: integration)
    monkeypatch.setattr(bots_service.integrations_service, "get_broker_adapter", lambda provider_key: FakeBrokerAdapter())

    response = client.post(
        "/api/bots",
        headers=_auth_headers(token),
        json={
            "name": "沪深择时一号",
            "strategy_id": "strategy-managed-1",
            "integration_id": integration_id,
            "capital": 80000,
        },
    )

    assert response.status_code == 201
    data = response.json["data"]
    assert data["name"] == "沪深择时一号"
    assert data["strategy_id"] == "strategy-managed-1"
    assert data["strategy_name"] == "沪深择时"
    assert data["integration_id"] == integration_id
    assert data["integration_display_name"] == "主账户"
    assert data["status"] == "active"
    assert data["capital"] == 80000
    assert data["profit"] == 0
    assert data["total_return_rate"] == 0
    assert data["created_at"].endswith("+08:00")

    with app.app_context():
        bot = db.session.get(BotInstance, data["id"])
        assert bot is not None
        assert bot.user_id == user_id
        assert bot.strategy_id == "strategy-managed-1"
        assert bot.integration_id == integration_id
        assert bot.paper is False
        snapshots = BotEquitySnapshot.query.filter_by(bot_id=bot.id).all()
        assert len(snapshots) == 1
        assert snapshots[0].equity == Decimal("80000.00")
        assert snapshots[0].total_profit == Decimal("0.00")


def test_create_managed_bot_rejects_capital_above_available_balance(client, app, monkeypatch):
    token, user_id = _login_user(client, email="managed-balance@example.com", nickname="ManagedBalance")
    _seed_strategy(app, strategy_id="strategy-managed-2", owner_id=user_id, name="ETF 轮动")
    integration_id = _seed_broker_integration(app, user_id=user_id)

    class FakeBrokerAdapter:
        def get_account_summary(self, _integration):
            return {"currency": "CNY", "available_cash": "10000.00"}

    from app.services import bots as bots_service

    monkeypatch.setattr(bots_service.integrations_service, "attach_secret_payload", lambda integration, session=None: integration)
    monkeypatch.setattr(bots_service.integrations_service, "get_broker_adapter", lambda provider_key: FakeBrokerAdapter())

    response = client.post(
        "/api/bots",
        headers=_auth_headers(token),
        json={
            "name": "ETF 轮动实盘",
            "strategy_id": "strategy-managed-2",
            "integration_id": integration_id,
            "capital": 20000,
        },
    )

    assert response.status_code == 422
    assert response.json["error"]["code"] == "CAPITAL_EXCEEDS_AVAILABLE_BALANCE"


def test_create_managed_bot_rejects_when_available_balance_is_zero(client, app, monkeypatch):
    token, user_id = _login_user(client, email="managed-zero-balance@example.com", nickname="ManagedZero")
    _seed_strategy(app, strategy_id="strategy-managed-2b", owner_id=user_id, name="中性套利")
    integration_id = _seed_broker_integration(app, user_id=user_id)

    class FakeBrokerAdapter:
        def get_account_summary(self, _integration):
            return {"currency": "CNY", "available_cash": "0.00"}

    from app.services import bots as bots_service

    monkeypatch.setattr(bots_service.integrations_service, "attach_secret_payload", lambda integration, session=None: integration)
    monkeypatch.setattr(bots_service.integrations_service, "get_broker_adapter", lambda provider_key: FakeBrokerAdapter())

    response = client.post(
        "/api/bots",
        headers=_auth_headers(token),
        json={
            "name": "中性套利实盘",
            "strategy_id": "strategy-managed-2b",
            "integration_id": integration_id,
            "capital": 1000,
        },
    )

    assert response.status_code == 422
    assert response.json["error"]["code"] == "CAPITAL_EXCEEDS_AVAILABLE_BALANCE"


def test_list_recent_positions_and_performance_for_managed_bot(client, app):
    token, user_id = _login_user(client, email="managed-metrics@example.com", nickname="ManagedMetrics")
    _seed_strategy(app, strategy_id="strategy-managed-3", owner_id=user_id, name="商品 CTA")
    integration_id = _seed_broker_integration(app, user_id=user_id)

    with app.app_context():
        bot = BotInstance(
            name="商品 CTA 一号",
            strategy="商品 CTA",
            strategy_id="strategy-managed-3",
            integration_id=integration_id,
            status="active",
            profit=8000,
            runtime="2d",
            capital=100000,
            tags=["托管", "CTA"],
            paper=False,
            user_id=user_id,
        )
        db.session.add(bot)
        db.session.flush()

        db.session.add_all(
            [
                BotEquitySnapshot(
                    bot_id=bot.id,
                    snapshot_date=date(2026, 4, 16),
                    equity=Decimal("100000.00"),
                    available_cash=Decimal("40000.00"),
                    position_value=Decimal("60000.00"),
                    total_profit=Decimal("0.00"),
                    total_return_rate=Decimal("0.000000"),
                ),
                BotEquitySnapshot(
                    bot_id=bot.id,
                    snapshot_date=date(2026, 4, 17),
                    equity=Decimal("108000.00"),
                    available_cash=Decimal("38000.00"),
                    position_value=Decimal("70000.00"),
                    total_profit=Decimal("8000.00"),
                    total_return_rate=Decimal("0.080000"),
                ),
                Order(
                    bot_id=bot.id,
                    symbol="AU2406",
                    side="buy",
                    price=500.0,
                    quantity=10,
                    status="filled",
                    pnl=None,
                    timestamp=1713350400000,
                    client_order_id="managed-order-1",
                ),
                Order(
                    bot_id=bot.id,
                    symbol="AU2406",
                    side="sell",
                    price=520.0,
                    quantity=4,
                    status="filled",
                    pnl=80.0,
                    timestamp=1713436800000,
                    client_order_id="managed-order-2",
                ),
            ]
        )
        db.session.commit()
        bot_id = bot.id

    recent_response = client.get("/api/bots/recent", headers=_auth_headers(token))
    positions_response = client.get(f"/api/bots/{bot_id}/positions", headers=_auth_headers(token))
    performance_response = client.get(f"/api/bots/{bot_id}/performance", headers=_auth_headers(token))

    assert recent_response.status_code == 200
    recent = recent_response.json["data"]
    assert len(recent) == 1
    assert recent[0]["name"] == "商品 CTA 一号"
    assert recent[0]["strategy"] == "商品 CTA"
    assert recent[0]["profit"] == 8000
    assert recent[0]["capital"] == 100000

    assert positions_response.status_code == 200
    assert positions_response.json["data"] == [
        {
            "symbol": "AU2406",
            "quantity": "6.0000",
            "avg_cost": "500.0000",
            "market_value": "3120.0000",
            "realized_pnl": "80.0000",
        }
    ]

    assert performance_response.status_code == 200
    performance = performance_response.json["data"]
    assert performance["summary"]["total_profit"] == 8000
    assert performance["summary"]["total_return_rate"] == 0.08
    assert performance["summary"]["latest_equity"] == 108000
    assert len(performance["equity_curve"]) == 2
    assert performance["equity_curve"][1] == {
        "snapshot_date": "2026-04-17",
        "equity": 108000,
        "available_cash": 38000,
        "position_value": 70000,
        "total_profit": 8000,
        "total_return_rate": 0.08,
    }
    assert performance["orders"][0]["client_order_id"] == "managed-order-2"


def test_resume_managed_bot_respects_slot_limit(client, app):
    token, user_id = _login_user(client, email="managed-resume@example.com", nickname="ManagedResume")
    _set_user_plan(app, user_id=user_id, plan_level="free")
    _seed_strategy(app, strategy_id="strategy-managed-4a", owner_id=user_id, name="趋势跟踪 A")
    _seed_strategy(app, strategy_id="strategy-managed-4b", owner_id=user_id, name="趋势跟踪 B")
    integration_id = _seed_broker_integration(app, user_id=user_id)

    with app.app_context():
        db.session.add_all(
            [
                BotInstance(
                    name="机器人 A",
                    strategy="趋势跟踪 A",
                    strategy_id="strategy-managed-4a",
                    integration_id=integration_id,
                    status="active",
                    profit=0,
                    runtime="1h",
                    capital=10000,
                    tags=["托管"],
                    paper=False,
                    user_id=user_id,
                ),
                BotInstance(
                    name="机器人 B",
                    strategy="趋势跟踪 B",
                    strategy_id="strategy-managed-4b",
                    integration_id=integration_id,
                    status="paused",
                    profit=0,
                    runtime="1h",
                    capital=10000,
                    tags=["托管"],
                    paper=False,
                    user_id=user_id,
                ),
            ]
        )
        db.session.commit()
        paused_bot = (
            BotInstance.query.filter_by(user_id=user_id, name="机器人 B")
            .first()
        )
        assert paused_bot is not None
        paused_bot_id = paused_bot.id

    response = client.patch(
        f"/api/bots/{paused_bot_id}/status",
        headers=_auth_headers(token),
        json={"status": "active"},
    )

    assert response.status_code == 403
    assert response.json["error"]["code"] == "BOT_SLOT_LIMIT_REACHED"

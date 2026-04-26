from app.extensions import db
from app.models import BotInstance, IntegrationProvider, Order, Strategy, User, UserIntegration, UserIntegrationSecret


def _seed_managed_bot(app, *, status="active", paper=False):
    with app.app_context():
        user = User(email="managed-dry-run@example.com", nickname="ManagedDryRun")
        db.session.add(user)
        db.session.flush()

        strategy = Strategy(
            id="strategy-managed-dry-run",
            name="Dry Run Strategy",
            title="Dry Run Strategy",
            symbol="00700.HK",
            status="draft",
            owner_id=user.id,
            returns=0,
            win_rate=0,
            max_drawdown=0,
            tags=["托管"],
            trades=0,
        )
        db.session.add(strategy)

        provider = IntegrationProvider(
            key="dry_run_broker",
            name="Dry Run Broker",
            type="broker_account",
            mode="hosted",
            capabilities={"account_summary": True, "positions": True, "orders": False},
            config_schema={"public_fields": [], "secret_fields": []},
            is_enabled=True,
        )
        db.session.add(provider)
        db.session.flush()

        integration = UserIntegration(
            user_id=user.id,
            provider_key=provider.key,
            display_name="Dry Run Account",
            status="active",
            config_public={},
        )
        db.session.add(integration)
        db.session.flush()
        db.session.add(
            UserIntegrationSecret(
                integration_id=integration.id,
                encrypted_payload="{}",
                schema_version=1,
            )
        )

        bot = BotInstance(
            name="Dry Run Bot",
            strategy=strategy.title,
            strategy_id=strategy.id,
            integration_id=integration.id,
            status=status,
            profit=0,
            runtime="0h",
            capital=100000,
            tags=["dry-run"],
            paper=paper,
            user_id=user.id,
        )
        db.session.add(bot)
        db.session.commit()
        return bot.id


class _FakeBrokerAdapter:
    def get_account_summary(self, _integration):
        return {"currency": "HKD", "cash": "100000.00", "equity": "100000.00"}

    def get_positions(self, _integration):
        return [{"symbol": "00700.HK", "quantity": "0"}]


def test_execute_managed_bot_dry_run_persists_order_intents(app, monkeypatch):
    from app.services import managed_bot_execution as service

    bot_id = _seed_managed_bot(app)
    monkeypatch.setattr(
        service.integrations_service,
        "attach_secret_payload",
        lambda integration, session=None: integration,
    )
    monkeypatch.setattr(service.integrations_service, "get_broker_adapter", lambda _provider_key: _FakeBrokerAdapter())
    monkeypatch.setattr(
        service,
        "load_strategy_package",
        lambda strategy_id, version, user_id=None: {
            "strategy_id": strategy_id,
            "version": "1.0.0",
            "manifest": {"symbol": "00700.HK"},
            "source": "",
            "entrypoint_callable": "on_bar",
        },
    )
    monkeypatch.setattr(
        service,
        "execute_backtest_strategy",
        lambda *args, **kwargs: {
            "ok": True,
            "trades": [
                {"symbol": "00700.HK", "side": "buy", "quantity": "100", "price": "320.5"},
            ],
        },
    )

    with app.app_context():
        bot = db.session.get(BotInstance, bot_id)
        result = service.execute_managed_bot_dry_run(bot=bot, run_started_at=1777132800000)

        assert result == {"bot_id": bot_id, "status": "dry_run_completed", "orders": 1, "rejected": 0}
        order = Order.query.filter_by(bot_id=bot_id).one()
        assert order.status == "dry_run"
        assert order.client_order_id == f"{bot_id}:dry-run:1777132800000:0"
        assert order.integration_id == bot.integration_id
        assert order.strategy_id == bot.strategy_id
        assert order.order_type == "market"
        assert order.raw_broker_payload["mode"] == "managed_dry_run"

        refreshed = db.session.get(BotInstance, bot_id)
        assert refreshed.last_run_at == 1777132800000
        assert refreshed.last_signal_at == 1777132800000
        assert refreshed.failure_count == 0
        assert refreshed.last_error_message is None


def test_execute_managed_bot_dry_run_persists_rejected_order_intents(app, monkeypatch):
    from app.services import managed_bot_execution as service

    bot_id = _seed_managed_bot(app)
    monkeypatch.setattr(
        service.integrations_service,
        "attach_secret_payload",
        lambda integration, session=None: integration,
    )
    monkeypatch.setattr(service.integrations_service, "get_broker_adapter", lambda _provider_key: _FakeBrokerAdapter())
    monkeypatch.setattr(
        service,
        "load_strategy_package",
        lambda strategy_id, version, user_id=None: {
            "strategy_id": strategy_id,
            "version": "1.0.0",
            "manifest": {"symbol": "00700.HK"},
            "source": "",
            "entrypoint_callable": "on_bar",
        },
    )
    monkeypatch.setattr(
        service,
        "execute_backtest_strategy",
        lambda *args, **kwargs: {
            "ok": True,
            "trades": [
                {"symbol": "AAPL.US", "side": "buy", "quantity": "10", "price": "180"},
            ],
        },
    )

    with app.app_context():
        bot = db.session.get(BotInstance, bot_id)
        result = service.execute_managed_bot_dry_run(bot=bot, run_started_at=1777132800001)

        assert result == {"bot_id": bot_id, "status": "dry_run_completed", "orders": 0, "rejected": 1}
        order = Order.query.filter_by(bot_id=bot_id).one()
        assert order.status == "rejected"
        assert order.rejected_reason == "symbol_not_allowed"
        assert order.raw_broker_payload["raw_intent"]["symbol"] == "AAPL.US"


def test_run_managed_bots_dry_run_skips_paused_bots(app, monkeypatch):
    from app.services import managed_bot_execution as service

    _seed_managed_bot(app, status="paused")
    calls = []
    monkeypatch.setattr(service, "execute_managed_bot_dry_run", lambda **kwargs: calls.append(kwargs))

    with app.app_context():
        result = service.run_managed_bots_dry_run()

    assert result == {"processed": 0, "failed": 0, "skipped": 0}
    assert calls == []


def test_managed_bot_dry_run_task_is_registered_every_five_minutes():
    from app.celery_app import celery_app

    assert "app.tasks.managed_bot_tasks" in celery_app.conf.imports
    assert celery_app.conf.task_routes["app.tasks.managed_bot_tasks.*"] == {"queue": "trading"}

    schedule = celery_app.conf.beat_schedule["run-managed-bots-dry-run"]
    assert schedule["task"] == "app.tasks.managed_bot_tasks.run_managed_bots_dry_run"
    assert schedule["options"] == {"queue": "trading"}
    assert schedule["schedule"]._orig_minute == "*/5"

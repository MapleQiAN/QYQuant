from datetime import date
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import SimulationBot, SimulationPosition, SimulationRecord, Strategy, User


class _FixedDate(date):
    @classmethod
    def today(cls):
        return cls(2026, 3, 23)


def _create_strategy(strategy_id, owner_id):
    strategy = Strategy(
        id=strategy_id,
        name=f"Strategy {strategy_id}",
        title=f"Strategy {strategy_id}",
        symbol="000001.XSHG",
        status="draft",
        owner_id=owner_id,
        returns=0,
        win_rate=0,
        max_drawdown=0,
        tags=[],
        trades=0,
    )
    db.session.add(strategy)
    return strategy


@pytest.fixture
def active_bot(app):
    with app.app_context():
        user = User(phone="13800138200", nickname="SimOwner")
        db.session.add(user)
        db.session.flush()
        _create_strategy("sim-strategy", user.id)
        bot = SimulationBot(
            user_id=user.id,
            strategy_id="sim-strategy",
            initial_capital=Decimal("100000"),
            status="active",
        )
        db.session.add(bot)
        db.session.commit()
        return bot.id


def test_run_daily_simulation_creates_record_and_positions(monkeypatch, app, active_bot):
    from app.tasks.simulation_tasks import run_daily_simulation

    seen = {}
    monkeypatch.setattr("app.tasks.simulation_tasks.date", _FixedDate)
    monkeypatch.setattr(
        "app.tasks.simulation_tasks.load_strategy_package",
        lambda strategy_id, version=None, user_id=None: seen.update(
            {
                "strategy_id": strategy_id,
                "user_id": user_id,
            }
        )
        or {
            "strategy_id": strategy_id,
            "manifest": {"symbol": "000001.XSHG"},
        },
    )
    monkeypatch.setattr(
        "app.tasks.simulation_tasks.execute_backtest_strategy",
        lambda **kwargs: {
            "equity": 102000,
            "cash": 50000,
            "positions": {
                "000001.XSHG": {"quantity": 1000, "avg_cost": 52.0},
            },
            "trades": [],
        },
    )

    result = run_daily_simulation.run()

    assert result == {"processed": 1}

    with app.app_context():
        bot = db.session.get(SimulationBot, active_bot)
        assert seen == {"strategy_id": "sim-strategy", "user_id": bot.user_id}
        record = SimulationRecord.query.filter_by(bot_id=active_bot).one()
        assert record.trade_date == date(2026, 3, 23)
        assert record.equity == Decimal("102000")
        assert record.cash == Decimal("50000")
        assert record.daily_return == Decimal("0.02")

        position = SimulationPosition.query.filter_by(bot_id=active_bot, symbol="000001.XSHG").one()
        assert position.quantity == Decimal("1000")
        assert position.avg_cost == Decimal("52.0")


def test_run_daily_simulation_skips_non_active_bots(monkeypatch, app):
    from app.tasks.simulation_tasks import run_daily_simulation

    with app.app_context():
        user = User(phone="13800138201", nickname="PausedOwner")
        db.session.add(user)
        db.session.flush()
        _create_strategy("paused-strategy", user.id)
        db.session.add(
            SimulationBot(
                user_id=user.id,
                strategy_id="paused-strategy",
                initial_capital=Decimal("100000"),
                status="paused",
            )
        )
        db.session.commit()

    called = {"value": False}

    def _unexpected(*args, **kwargs):
        called["value"] = True
        return {}

    monkeypatch.setattr("app.tasks.simulation_tasks.load_strategy_package", _unexpected)

    result = run_daily_simulation.run()

    assert result == {"processed": 0}
    assert called["value"] is False


def test_run_daily_simulation_isolates_bot_failures(monkeypatch, app):
    from app.tasks.simulation_tasks import run_daily_simulation

    with app.app_context():
        user = User(phone="13800138202", nickname="MixedOwner")
        db.session.add(user)
        db.session.flush()
        _create_strategy("failing-strategy", user.id)
        _create_strategy("healthy-strategy", user.id)
        db.session.add(
            SimulationBot(
                id="bot-fail",
                user_id=user.id,
                strategy_id="failing-strategy",
                initial_capital=Decimal("100000"),
                status="active",
            )
        )
        db.session.add(
            SimulationBot(
                id="bot-ok",
                user_id=user.id,
                strategy_id="healthy-strategy",
                initial_capital=Decimal("100000"),
                status="active",
            )
        )
        db.session.commit()

    monkeypatch.setattr("app.tasks.simulation_tasks.date", _FixedDate)

    def _fake_execute_single_bot(bot):
        if bot.id == "bot-fail":
            raise RuntimeError("boom")
        with app.app_context():
            db.session.add(
                SimulationRecord(
                    bot_id=bot.id,
                    trade_date=date(2026, 3, 23),
                    equity=Decimal("101000"),
                    cash=Decimal("51000"),
                    daily_return=Decimal("0.01"),
                )
            )
            db.session.commit()

    monkeypatch.setattr("app.tasks.simulation_tasks._execute_single_bot", _fake_execute_single_bot)

    result = run_daily_simulation.run()

    assert result == {"processed": 1}

    with app.app_context():
        assert SimulationRecord.query.filter_by(bot_id="bot-fail").count() == 0
        assert SimulationRecord.query.filter_by(bot_id="bot-ok").count() == 1


def test_run_daily_simulation_upserts_same_trade_date(monkeypatch, app, active_bot):
    from app.tasks.simulation_tasks import run_daily_simulation

    with app.app_context():
        db.session.add(
            SimulationRecord(
                bot_id=active_bot,
                trade_date=date(2026, 3, 23),
                equity=Decimal("101000"),
                cash=Decimal("60000"),
                daily_return=Decimal("0.01"),
            )
        )
        db.session.commit()

    monkeypatch.setattr("app.tasks.simulation_tasks.date", _FixedDate)
    monkeypatch.setattr(
        "app.tasks.simulation_tasks.load_strategy_package",
        lambda strategy_id, version=None, user_id=None: {
            "strategy_id": strategy_id,
            "manifest": {"symbol": "000001.XSHG"},
        },
    )
    monkeypatch.setattr(
        "app.tasks.simulation_tasks.execute_backtest_strategy",
        lambda **kwargs: {
            "equity": 103000,
            "cash": 55000,
            "positions": {},
            "trades": [],
        },
    )

    result = run_daily_simulation.run()

    assert result == {"processed": 1}

    with app.app_context():
        records = SimulationRecord.query.filter_by(bot_id=active_bot).all()
        assert len(records) == 1
        assert records[0].equity == Decimal("103000")
        assert records[0].cash == Decimal("55000")


def test_run_daily_simulation_persists_trades(monkeypatch, app, active_bot):
    from app.tasks.simulation_tasks import run_daily_simulation
    from app.models import SimulationTrade

    monkeypatch.setattr("app.tasks.simulation_tasks.date", _FixedDate)
    monkeypatch.setattr(
        "app.tasks.simulation_tasks.load_strategy_package",
        lambda strategy_id, version=None, user_id=None: {
            "strategy_id": strategy_id,
            "manifest": {"symbol": "000001.XSHG"},
        },
    )
    monkeypatch.setattr(
        "app.tasks.simulation_tasks.execute_backtest_strategy",
        lambda **kwargs: {
            "equity": 100000,
            "cash": 100000,
            "positions": {},
            "trades": [
                {
                    "symbol": "000001.XSHG",
                    "side": "buy",
                    "price": 15.23,
                    "quantity": 1000,
                }
            ],
        },
    )

    result = run_daily_simulation.run()

    assert result == {"processed": 1}

    with app.app_context():
        trades = SimulationTrade.query.filter_by(bot_id=active_bot).all()
        assert len(trades) == 1
        assert trades[0].trade_date == date(2026, 3, 23)
        assert trades[0].symbol == "000001.XSHG"
        assert trades[0].side == "buy"
        assert trades[0].price == Decimal("15.23")
        assert trades[0].quantity == Decimal("1000")

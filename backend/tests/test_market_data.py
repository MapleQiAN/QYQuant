from datetime import date
from types import SimpleNamespace

import pytest

from app.extensions import db


def _cache_row(**overrides):
    from app.models import MarketDataCache

    payload = {
        "symbol": "000001.XSHE",
        "trade_date": date(2025, 1, 2),
        "open": 10.0,
        "high": 10.5,
        "low": 9.8,
        "close": 10.2,
        "volume": 100000,
    }
    payload.update(overrides)
    return MarketDataCache(**payload)


def test_market_data_cache_persists_composite_key_defaults(app):
    from app.models import MarketDataCache

    with app.app_context():
        row = _cache_row()
        db.session.add(row)
        db.session.commit()

        saved = db.session.get(MarketDataCache, ("000001.XSHE", date(2025, 1, 2)))
        assert saved is not None
        assert saved.source == "joinquant"
        assert saved.cached_at is not None


def test_market_data_service_returns_cached_rows_without_external_fetch(app):
    from app.services.market_data import MarketDataService

    with app.app_context():
        db.session.add_all(
            [
                _cache_row(trade_date=date(2025, 1, 2), close=10.2),
                _cache_row(trade_date=date(2025, 1, 3), close=10.4),
            ]
        )
        db.session.commit()

        def _unexpected_fetch(*args, **kwargs):
            raise AssertionError("external provider should not be called on cache hit")

        service = MarketDataService(client=SimpleNamespace(fetch_daily_data=_unexpected_fetch))
        result = service.get_market_data("000001.XSHE", date(2025, 1, 2), date(2025, 1, 3))

        assert [bar["trade_date"] for bar in result["bars"]] == [date(2025, 1, 2), date(2025, 1, 3)]
        assert result["data_range_notice"] is None


def test_market_data_service_fetches_missing_rows_and_persists_cache(app):
    from app.models import MarketDataCache
    from app.services.market_data import MarketDataService

    with app.app_context():
        db.session.add(_cache_row(trade_date=date(2025, 1, 2), close=10.2))
        db.session.commit()

        calls = []

        def _fetch_daily_data(symbol, start_date, end_date):
            calls.append((symbol, start_date, end_date))
            return [
                {
                    "symbol": symbol,
                    "trade_date": date(2025, 1, 3),
                    "open": 10.2,
                    "high": 10.7,
                    "low": 10.1,
                    "close": 10.6,
                    "volume": 120000,
                    "source": "joinquant",
                },
                {
                    "symbol": symbol,
                    "trade_date": date(2025, 1, 6),
                    "open": 10.6,
                    "high": 10.9,
                    "low": 10.3,
                    "close": 10.8,
                    "volume": 140000,
                    "source": "joinquant",
                },
            ]

        service = MarketDataService(client=SimpleNamespace(fetch_daily_data=_fetch_daily_data))
        result = service.get_market_data("000001.XSHE", date(2025, 1, 2), date(2025, 1, 6))

        assert calls == [("000001.XSHE", date(2025, 1, 3), date(2025, 1, 6))]
        assert [bar["trade_date"] for bar in result["bars"]] == [
            date(2025, 1, 2),
            date(2025, 1, 3),
            date(2025, 1, 6),
        ]
        assert result["data_range_notice"] is None
        assert db.session.query(MarketDataCache).count() == 3


def test_market_data_service_returns_cached_rows_with_notice_on_provider_failure(app):
    from app.services.market_data import MarketDataService

    with app.app_context():
        db.session.add(_cache_row(trade_date=date(2025, 1, 2), close=10.2))
        db.session.commit()

        def _raise_failure(*args, **kwargs):
            raise RuntimeError("joinquant unavailable")

        service = MarketDataService(client=SimpleNamespace(fetch_daily_data=_raise_failure))
        result = service.get_market_data("000001.XSHE", date(2025, 1, 2), date(2025, 1, 6))

        assert [bar["trade_date"] for bar in result["bars"]] == [date(2025, 1, 2)]
        assert result["data_range_notice"] is not None
        assert "2025-01-02" in result["data_range_notice"]


def test_market_data_service_bulk_insert_is_idempotent(app):
    from app.models import MarketDataCache
    from app.services.market_data import MarketDataService

    rows = [
        {
            "symbol": "000001.XSHE",
            "trade_date": date(2025, 1, 2),
            "open": 10.0,
            "high": 10.5,
            "low": 9.8,
            "close": 10.2,
            "volume": 100000,
            "source": "joinquant",
        }
    ]

    with app.app_context():
        service = MarketDataService(client=SimpleNamespace(fetch_daily_data=lambda *args, **kwargs: []))
        service._bulk_insert(rows)
        db.session.commit()
        service._bulk_insert(rows)
        db.session.commit()

        assert db.session.query(MarketDataCache).count() == 1


def test_market_data_service_supports_akshare_daily_contract(app):
    from app.services.market_data import MarketDataService

    calls = []

    class FakeAkShareClient:
        def fetch_stock_history(self, symbol, start_date, end_date, period="daily", adjust="qfq"):
            calls.append((symbol, start_date, end_date, period, adjust))
            return [
                {
                    "symbol": symbol,
                    "trade_date": date(2025, 1, 2),
                    "open": 10.0,
                    "high": 10.5,
                    "low": 9.8,
                    "close": 10.2,
                    "volume": 100000,
                    "source": "akshare",
                }
            ]

    with app.app_context():
        service = MarketDataService(client=FakeAkShareClient(), provider_key="akshare")
        result = service.get_market_data("000001.XSHE", date(2025, 1, 2), date(2025, 1, 2))

        assert calls == [("000001.XSHE", date(2025, 1, 2), date(2025, 1, 2), "daily", "qfq")]
        assert result["bars"] == [
            {
                "symbol": "000001.XSHE",
                "trade_date": date(2025, 1, 2),
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.2,
                "volume": 100000,
                "source": "akshare",
            }
        ]


def test_market_data_service_uses_env_provider_when_client_is_not_supplied(monkeypatch):
    from app.services.market_data import MarketDataService

    class FakeAkShareClient:
        def fetch_stock_history(self, symbol, start_date, end_date, period="daily", adjust="qfq"):
            return []

    monkeypatch.setenv("MARKET_DATA_PROVIDER", "akshare")
    monkeypatch.setattr("app.services.market_data.AkShareClient", FakeAkShareClient)
    monkeypatch.setattr("app.services.market_data.JoinQuantClient", lambda: (_ for _ in ()).throw(AssertionError("joinquant should not be used")))

    service = MarketDataService()

    assert service.provider_key == "akshare"
    assert hasattr(service.client, "fetch_daily_data")


def test_run_backtest_includes_data_range_notice_from_provider(monkeypatch):
    from app.backtest.engine import run_backtest

    class StubProvider:
        def __init__(self):
            self.last_data_range_notice = "仅返回缓存区间 2025-01-02 至 2025-01-02"

        def get_bars(self, symbol, limit=200, interval=None, start_time=None, end_time=None):
            return [
                {
                    "time": 1735776000000,
                    "open": 10.0,
                    "high": 10.5,
                    "low": 9.8,
                    "close": 10.2,
                    "volume": 100000,
                }
            ]

    monkeypatch.setattr("app.backtest.engine.get_backtest_provider", lambda provider_override=None: StubProvider())
    monkeypatch.setattr("app.backtest.engine.resolve_data_source", lambda provider_override=None, symbol=None: "joinquant")

    result = run_backtest(
        "000001.XSHE",
        interval="1d",
        start_time="2025-01-02",
        end_time="2025-01-06",
        data_source="joinquant",
    )

    assert result["dataSource"] == "joinquant"
    assert result["data_range_notice"] == "仅返回缓存区间 2025-01-02 至 2025-01-02"

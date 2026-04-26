from datetime import date
from types import SimpleNamespace


def test_joinquant_market_data_adapter_normalizes_daily_bars():
    from app.integrations.market_data.joinquant import JoinQuantMarketDataAdapter

    class FakeJoinQuantClient:
        def fetch_daily_data(self, symbol, start_date, end_date):
            assert symbol == "000001.XSHE"
            assert start_date == date(2025, 1, 2)
            assert end_date == date(2025, 1, 3)
            return [
                {
                    "symbol": symbol,
                    "trade_date": date(2025, 1, 2),
                    "open": 10.0,
                    "high": 10.5,
                    "low": 9.8,
                    "close": 10.2,
                    "volume": 100000,
                }
            ]

        def healthcheck(self):
            return True

    adapter = JoinQuantMarketDataAdapter(client=FakeJoinQuantClient())
    bars = adapter.get_bars("000001.XSHE", interval="1d", start_time="2025-01-02", end_time="2025-01-03")

    assert bars == [
        {
            "time": 1735776000000,
            "open": 10.0,
            "high": 10.5,
            "low": 9.8,
            "close": 10.2,
            "volume": 100000,
        }
    ]
    assert adapter.supports_interval("1d") is True
    assert adapter.supports_market("cn") is True
    assert adapter.healthcheck() is True


def test_akshare_like_market_data_adapter_uses_public_client_contract():
    from app.integrations.market_data.akshare_like import AKShareLikeMarketDataAdapter

    class FakePublicClient:
        def fetch_bars(self, symbol, start_date, end_date, interval):
            assert symbol == "600519.SH"
            assert interval == "1d"
            return [
                {
                    "trade_date": date(2025, 1, 2),
                    "open": 1500.0,
                    "high": 1510.0,
                    "low": 1490.0,
                    "close": 1505.0,
                    "volume": 12345,
                }
            ]

        def get_latest_quote(self, symbol):
            assert symbol == "600519.SH"
            return {"symbol": symbol, "price": 1505.0}

    adapter = AKShareLikeMarketDataAdapter(client=FakePublicClient())

    assert adapter.get_bars("600519.SH", interval="1d", start_time="2025-01-02", end_time="2025-01-02")[0]["close"] == 1505.0
    assert adapter.get_latest_quote("600519.SH") == {"symbol": "600519.SH", "price": 1505.0}
    assert adapter.supports_market("cn") is True


def test_longport_broker_adapter_uses_sdk_ready_client_contract():
    from app.integrations.brokers.longport import LongPortBrokerAdapter

    class FakeLongPortClient:
        def get_account_balance(self):
            return {"currency": "HKD", "total_cash": "10000.00", "net_assets": "12345.67"}

        def get_positions(self):
            return [{"symbol": "00700.HK", "quantity": "100", "market": "hk"}]

    adapter = LongPortBrokerAdapter(client_factory=lambda _config: FakeLongPortClient())
    validation = adapter.validate_credentials(
        {
            "secret_payload": {"app_key": "a", "app_secret": "b", "access_token": "c"},
            "config_public": {"region": "hk"},
        }
    )
    account = adapter.get_account_summary(SimpleNamespace(_secret_payload={"app_key": "a", "app_secret": "b", "access_token": "c"}, config_public={"region": "hk"}))
    positions = adapter.get_positions(SimpleNamespace(_secret_payload={"app_key": "a", "app_secret": "b", "access_token": "c"}, config_public={"region": "hk"}))

    assert validation == {"status": "valid", "message": "ok"}
    assert account["currency"] == "HKD"
    assert account["equity"] == "12345.67"
    assert positions == [{"symbol": "00700.HK", "quantity": "100", "market": "hk"}]


def test_gmtrade_broker_adapter_requires_token_and_account_id():
    from app.integrations.brokers.gmtrade import GMTradeBrokerAdapter

    class FakeGMClient:
        def connect(self, token, account_id, endpoint=None):
            assert token == "token-1"
            assert account_id == "acct-1"
            assert endpoint == "api.myquant.cn:9000"
            return True

        def get_account_summary(self):
            return {"account_id": "acct-1", "currency": "CNY", "equity": "200000.00"}

        def get_positions(self):
            return [{"symbol": "600519.SH", "quantity": "10", "market": "cn"}]

    adapter = GMTradeBrokerAdapter(client_factory=lambda _config: FakeGMClient())
    config = {
        "secret_payload": {"token": "token-1"},
        "config_public": {"account_id": "acct-1", "endpoint": "api.myquant.cn:9000"},
    }
    assert adapter.validate_credentials(config) == {"status": "valid", "message": "ok"}
    context = SimpleNamespace(_secret_payload=config["secret_payload"], config_public=config["config_public"])
    assert adapter.get_account_summary(context)["currency"] == "CNY"
    assert adapter.get_positions(context)[0]["symbol"] == "600519.SH"


def test_xtquant_broker_adapter_supports_local_connector_contract():
    from app.integrations.brokers.xtquant import XtQuantBrokerAdapter

    class FakeXtClient:
        def connect(self, endpoint, account_id, client_path=None):
            assert endpoint == "http://127.0.0.1:5010"
            assert account_id == "qmt-1"
            assert client_path == "C:/QMT/bin"
            return True

        def get_account_summary(self):
            return {"account_id": "qmt-1", "currency": "CNY", "equity": "500000.00"}

        def get_positions(self):
            return [{"symbol": "510300.SH", "quantity": "1000", "market": "cn"}]

    adapter = XtQuantBrokerAdapter(client_factory=lambda _config: FakeXtClient())
    config = {
        "secret_payload": {},
        "config_public": {
            "endpoint": "http://127.0.0.1:5010",
            "account_id": "qmt-1",
            "client_path": "C:/QMT/bin",
        },
    }
    assert adapter.validate_credentials(config) == {"status": "valid", "message": "ok"}
    context = SimpleNamespace(_secret_payload={}, config_public=config["config_public"])
    assert adapter.get_account_summary(context)["equity"] == "500000.00"
    assert adapter.get_positions(context)[0]["symbol"] == "510300.SH"


def test_broker_order_contract_payloads_are_stable():
    from app.integrations.brokers import BrokerFill, BrokerOrderRequest, BrokerOrderResponse, BrokerOrderStatus

    request = BrokerOrderRequest(
        client_order_id="bot-1-20260426-1",
        symbol="00700.HK",
        side="buy",
        quantity="100",
        limit_price="320.50",
        metadata={"bot_id": "bot-1", "strategy_id": "strategy-1"},
    )
    response = BrokerOrderResponse(
        client_order_id=request.client_order_id,
        broker_order_id="broker-1",
        status="submitted",
        raw_payload={"id": "broker-1"},
    )
    status = BrokerOrderStatus(
        client_order_id=request.client_order_id,
        broker_order_id="broker-1",
        status="filled",
        filled_quantity="100",
        filled_avg_price="320.45",
    )
    fill = BrokerFill(
        broker_order_id="broker-1",
        symbol="00700.HK",
        side="buy",
        price="320.45",
        quantity="100",
        filled_at=1777132800000,
    )

    assert request.to_payload() == {
        "client_order_id": "bot-1-20260426-1",
        "symbol": "00700.HK",
        "side": "buy",
        "quantity": "100",
        "order_type": "market",
        "limit_price": "320.50",
        "time_in_force": "day",
        "metadata": {"bot_id": "bot-1", "strategy_id": "strategy-1"},
    }
    assert response.to_payload()["broker_order_id"] == "broker-1"
    assert status.to_payload()["filled_avg_price"] == "320.45"
    assert fill.to_payload()["filled_at"] == 1777132800000


def test_read_only_broker_adapters_reject_live_orders():
    import pytest

    from app.integrations.brokers import BrokerOrderNotSupported, BrokerOrderRequest
    from app.integrations.brokers.longport import LongPortBrokerAdapter

    adapter = LongPortBrokerAdapter(client_factory=lambda _config: object())
    request = BrokerOrderRequest(
        client_order_id="bot-1-20260426-1",
        symbol="00700.HK",
        side="buy",
        quantity="100",
    )

    with pytest.raises(BrokerOrderNotSupported):
        adapter.place_order(SimpleNamespace(), request)

    with pytest.raises(BrokerOrderNotSupported):
        adapter.cancel_order(SimpleNamespace(), "broker-1")

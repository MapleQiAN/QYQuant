from datetime import date

import pandas as pd


DATE_CN = "\u65e5\u671f"
OPEN_CN = "\u5f00\u76d8"
HIGH_CN = "\u6700\u9ad8"
LOW_CN = "\u6700\u4f4e"
CLOSE_CN = "\u6536\u76d8"
VOLUME_CN = "\u6210\u4ea4\u91cf"
CODE_CN = "\u4ee3\u7801"
NAME_CN = "\u540d\u79f0"
LATEST_PRICE_CN = "\u6700\u65b0\u4ef7"
TODAY_OPEN_CN = "\u4eca\u5f00"
PREV_CLOSE_CN = "\u6628\u6536"
TURNOVER_CN = "\u6210\u4ea4\u989d"
TIMESTAMP_CN = "\u65f6\u95f4\u6233"
FUND_CODE_CN = "\u57fa\u91d1\u4ee3\u7801"
FUND_NAME_CN = "\u57fa\u91d1\u7b80\u79f0"
UNIT_NAV_CN = "\u5355\u4f4d\u51c0\u503c"
ACC_NAV_CN = "\u7d2f\u8ba1\u51c0\u503c"
DAILY_GROWTH_RATE_CN = "\u65e5\u589e\u957f\u7387"
PURCHASE_STATUS_CN = "\u7533\u8d2d\u72b6\u6001"
REDEMPTION_STATUS_CN = "\u8d4e\u56de\u72b6\u6001"


def test_akshare_client_normalizes_stock_history_and_realtime_quote():
    from app.providers.akshare import AkShareClient

    class FakeSDK:
        def stock_zh_a_hist(self, symbol, period, start_date, end_date, adjust):
            assert symbol == "000001"
            assert period == "daily"
            assert start_date == "20250102"
            assert end_date == "20250103"
            assert adjust == "qfq"
            return pd.DataFrame(
                [
                    {
                        DATE_CN: "2025-01-02",
                        "\u80a1\u7968\u4ee3\u7801": "000001",
                        OPEN_CN: 10.0,
                        CLOSE_CN: 10.2,
                        HIGH_CN: 10.5,
                        LOW_CN: 9.8,
                        VOLUME_CN: 100000,
                    }
                ]
            )

        def stock_zh_a_spot(self):
            return pd.DataFrame(
                [
                    {
                        CODE_CN: "000001",
                        NAME_CN: "\u5e73\u5b89\u94f6\u884c",
                        LATEST_PRICE_CN: 10.2,
                        TODAY_OPEN_CN: 10.0,
                        HIGH_CN: 10.5,
                        LOW_CN: 9.8,
                        PREV_CLOSE_CN: 10.1,
                        VOLUME_CN: 100000,
                        TURNOVER_CN: 1002000.0,
                        TIMESTAMP_CN: "15:00:00",
                    }
                ]
            )

    client = AkShareClient(sdk=FakeSDK())

    history = client.fetch_stock_history("000001.XSHE", date(2025, 1, 2), date(2025, 1, 3))
    quote = client.get_latest_quote("000001.XSHE")

    assert history == [
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
    assert quote["symbol"] == "000001.XSHE"
    assert quote["name"] == "\u5e73\u5b89\u94f6\u884c"
    assert quote["price"] == 10.2


def test_akshare_client_exposes_futures_and_fund_snapshots():
    from app.providers.akshare import AkShareClient

    class FakeSDK:
        def futures_zh_spot(self, symbol, market, adjust):
            assert symbol == "SN0"
            assert market == "CF"
            assert adjust == "0"
            return pd.DataFrame(
                [
                    {
                        "symbol": "SN0",
                        "time": "110337",
                        "open": 264860.0,
                        "high": 291510.0,
                        "low": 264080.0,
                        "current_price": 291510.0,
                        "volume": 41903.0,
                    }
                ]
            )

        def fund_open_fund_daily_em(self):
            return pd.DataFrame(
                [
                    {
                        FUND_CODE_CN: "519212",
                        FUND_NAME_CN: "\u4e07\u5bb6\u5b8f\u89c2\u62e9\u65f6\u591a\u7b56\u7565\u6df7\u5408A",
                        f"2025-01-03-{UNIT_NAV_CN}": 2.1819,
                        f"2025-01-03-{ACC_NAV_CN}": 2.1819,
                        DAILY_GROWTH_RATE_CN: 4.42,
                        PURCHASE_STATUS_CN: "\u9650\u5927\u989d",
                        REDEMPTION_STATUS_CN: "\u5f00\u653e\u8d4e\u56de",
                    }
                ]
            )

    client = AkShareClient(sdk=FakeSDK())

    futures_quote = client.fetch_futures_quote("SN0", market="CF", adjust="0")
    fund_nav = client.fetch_fund_nav("519212")

    assert futures_quote["symbol"] == "SN0"
    assert futures_quote["price"] == 291510.0
    assert fund_nav["symbol"] == "519212"
    assert fund_nav["unit_nav"] == 2.1819


def test_akshare_client_falls_back_to_recent_history_when_spot_quote_fails():
    from app.providers.akshare import AkShareClient

    class FakeSDK:
        def stock_zh_a_spot_em(self):
            raise RuntimeError("spot em unavailable")

        def stock_zh_a_spot(self):
            raise RuntimeError("spot unavailable")

        def stock_zh_a_hist(self, symbol, period, start_date, end_date, adjust):
            return pd.DataFrame(
                [
                    {DATE_CN: "2025-01-02", OPEN_CN: 10.0, HIGH_CN: 10.5, LOW_CN: 9.8, CLOSE_CN: 10.2, VOLUME_CN: 100000},
                    {DATE_CN: "2025-01-03", OPEN_CN: 10.2, HIGH_CN: 10.6, LOW_CN: 10.1, CLOSE_CN: 10.4, VOLUME_CN: 110000},
                ]
            )

    client = AkShareClient(sdk=FakeSDK())

    quote = client.get_latest_quote("000001.XSHE")

    assert quote["symbol"] == "000001.XSHE"
    assert quote["price"] == 10.4
    assert quote["prev_close"] == 10.2
    assert quote["source"] == "akshare_history_fallback"


def test_akshare_backtest_provider_supports_daily_a_share_bars():
    from app.backtest.providers import AkShareBacktestProvider, get_backtest_provider, resolve_data_source

    class FakeClient:
        def fetch_stock_history(self, symbol, start_date, end_date, period="daily", adjust="qfq"):
            assert symbol == "000001.XSHE"
            assert start_date == date(2025, 1, 2)
            assert end_date == date(2025, 1, 2)
            assert period == "daily"
            assert adjust == "qfq"
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

        def get_latest_quote(self, symbol):
            assert symbol == "000001.XSHE"
            return {"symbol": symbol, "price": 10.2}

    provider = AkShareBacktestProvider(client=FakeClient())
    bars = provider.get_bars("000001.XSHE", interval="1d", start_time="2025-01-02", end_time="2025-01-02")

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
    assert provider.get_latest_price("000001.XSHE") == 10.2
    assert isinstance(get_backtest_provider("akshare"), AkShareBacktestProvider)
    assert resolve_data_source("akshare", symbol="000001.XSHE") == "akshare"

from datetime import date

import pandas as pd


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
                        "日期": "2025-01-02",
                        "股票代码": "000001",
                        "开盘": 10.0,
                        "收盘": 10.2,
                        "最高": 10.5,
                        "最低": 9.8,
                        "成交量": 100000,
                    }
                ]
            )

        def stock_zh_a_spot(self):
            return pd.DataFrame(
                [
                    {
                        "代码": "000001",
                        "名称": "平安银行",
                        "最新价": 10.2,
                        "今开": 10.0,
                        "最高": 10.5,
                        "最低": 9.8,
                        "昨收": 10.1,
                        "成交量": 100000,
                        "成交额": 1002000.0,
                        "时间戳": "15:00:00",
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
    assert quote["name"] == "平安银行"
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
                        "基金代码": "519212",
                        "基金简称": "万家宏观择时多策略混合A",
                        "单位净值": 2.1819,
                        "累计净值": 2.1819,
                        "日增长率": 4.42,
                        "申购状态": "限大额",
                        "赎回状态": "开放赎回",
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

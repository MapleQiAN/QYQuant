import os

from ..marketdata import BinanceClient


class MockProvider:
    def get_bars(self, symbol, limit=100, **_kwargs):
        bars = []
        for i in range(limit):
            bars.append({
                "time": 1700000000000 + i * 60000,
                "open": 100 + i * 0.1,
                "high": 100 + i * 0.2,
                "low": 100 + i * 0.05,
                "close": 100 + i * 0.15,
                "volume": 1000 + i,
            })
        return bars


class BinanceProvider:
    def __init__(self, client=None, default_interval=None):
        self.client = client or BinanceClient()
        self.default_interval = default_interval or os.getenv('BACKTEST_INTERVAL', '1m')

    def get_bars(self, symbol, limit=200, interval=None, start_time=None, end_time=None):
        interval = interval or self.default_interval
        return self.client.get_klines(
            symbol,
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
            use_cache=True,
        )

    def get_latest_price(self, symbol):
        return self.client.get_latest_price(symbol, use_cache=True)


def get_backtest_provider():
    provider = os.getenv('BACKTEST_DATA_PROVIDER')
    if not provider:
        env = os.getenv('FLASK_ENV', 'development').lower()
        provider = 'mock' if env in {'test', 'testing'} else 'binance'

    provider = provider.lower()
    if provider in {'mock', 'demo'}:
        return MockProvider()
    if provider in {'binance', 'live', 'real'}:
        return BinanceProvider()

    raise ValueError(f"Unknown BACKTEST_DATA_PROVIDER: {provider}")

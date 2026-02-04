import os

from ..marketdata import BinanceClient, FreeGoldClient


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
        if symbol and not _is_gold_symbol(symbol):
            raise ValueError(f"FreeGold provider only supports XAUUSD (got {symbol})")
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


def _is_gold_symbol(symbol):
    if not symbol:
        return False
    normalized = str(symbol).upper().replace('/', '').replace('-', '')
    return normalized in {'XAUUSD', 'XAU', 'GOLD', 'GCF', 'GC=F'}


class FreeGoldProvider:
    def __init__(self, client=None, default_interval=None):
        self.client = client or FreeGoldClient()
        self.default_interval = default_interval or os.getenv('FREEGOLD_INTERVAL', '1d')

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
        if symbol and not _is_gold_symbol(symbol):
            raise ValueError(f"FreeGold provider only supports XAUUSD (got {symbol})")
        return self.client.get_latest_price(symbol, use_cache=True)


class AutoProvider:
    def __init__(self, gold_provider=None, binance_provider=None):
        self.gold_provider = gold_provider or FreeGoldProvider()
        self.binance_provider = binance_provider or BinanceProvider()

    def _select(self, symbol):
        if _is_gold_symbol(symbol):
            return self.gold_provider
        return self.binance_provider

    def get_bars(self, symbol, limit=200, interval=None, start_time=None, end_time=None):
        return self._select(symbol).get_bars(
            symbol,
            limit=limit,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
        )

    def get_latest_price(self, symbol):
        return self._select(symbol).get_latest_price(symbol)


def get_backtest_provider():
    provider = os.getenv('BACKTEST_DATA_PROVIDER')
    if not provider:
        env = os.getenv('FLASK_ENV', 'development').lower()
        provider = 'mock' if env in {'test', 'testing'} else 'auto'

    provider = provider.lower()
    if provider in {'mock', 'demo'}:
        return MockProvider()
    if provider in {'auto', 'hybrid', 'mixed'}:
        return AutoProvider()
    if provider in {'gold', 'xau', 'freegold'}:
        return FreeGoldProvider()
    if provider in {'binance', 'live', 'real'}:
        return BinanceProvider()

    raise ValueError(f"Unknown BACKTEST_DATA_PROVIDER: {provider}")

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


_CANONICAL_PROVIDERS = {'mock', 'auto', 'freegold', 'binance'}
_PROVIDER_ALIASES = {
    'mock': 'mock',
    'demo': 'mock',
    'auto': 'auto',
    'hybrid': 'auto',
    'mixed': 'auto',
    'gold': 'freegold',
    'xau': 'freegold',
    'freegold': 'freegold',
    'binance': 'binance',
    'live': 'binance',
    'real': 'binance',
}


def _normalize_provider_name(value):
    if value is None:
        return None
    normalized = str(value).strip().lower()
    if not normalized:
        return None
    return _PROVIDER_ALIASES.get(normalized, normalized)


def _default_provider_name():
    provider = os.getenv('BACKTEST_DATA_PROVIDER')
    if not provider:
        env = os.getenv('FLASK_ENV', 'development').lower()
        provider = 'mock' if env in {'test', 'testing'} else 'auto'
    provider = _normalize_provider_name(provider)
    if provider not in _CANONICAL_PROVIDERS:
        return 'auto'
    return provider


def resolve_data_source(provider_override=None, symbol=None):
    provider = _normalize_provider_name(provider_override)
    if provider not in _CANONICAL_PROVIDERS:
        provider = _default_provider_name()
    if provider == 'auto':
        return 'freegold' if _is_gold_symbol(symbol) else 'binance'
    return provider


def get_backtest_provider(provider_override=None):
    provider = _normalize_provider_name(provider_override)
    if provider not in _CANONICAL_PROVIDERS:
        provider = _default_provider_name()

    if provider == 'mock':
        return MockProvider()
    if provider == 'auto':
        return AutoProvider()
    if provider == 'freegold':
        return FreeGoldProvider()
    if provider == 'binance':
        return BinanceProvider()

    return AutoProvider()

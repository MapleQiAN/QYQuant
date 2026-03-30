import os
from datetime import date, datetime, time, timedelta, timezone

from ..marketdata import BinanceClient, FreeGoldClient
from ..providers import AkShareClient
from ..services import MarketDataService


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


def _coerce_date(value):
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000 if value > 1_000_000_000_000 else value, tz=timezone.utc).date()
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None
        return date.fromisoformat(normalized[:10])
    raise TypeError(f"Unsupported date type: {type(value)}")


def _to_bar(row):
    ts = datetime.combine(row["trade_date"], time.min, tzinfo=timezone.utc)
    return {
        "time": int(ts.timestamp() * 1000),
        "open": row["open"],
        "high": row["high"],
        "low": row["low"],
        "close": row["close"],
        "volume": row["volume"],
    }


def _daily_range(limit, start_time, end_time):
    end_date = _coerce_date(end_time) or datetime.now(timezone.utc).date()
    start_date = _coerce_date(start_time)
    if start_date is None:
        lookback = max(int(limit or 200), 1)
        start_date = end_date - timedelta(days=lookback * 2)
    return start_date, end_date


class JoinQuantBacktestProvider:
    def __init__(self, market_data_service=None, default_interval=None):
        self.market_data_service = market_data_service or MarketDataService()
        self.default_interval = default_interval or os.getenv('JOINQUANT_INTERVAL', '1d')
        self.last_data_range_notice = None

    def get_bars(self, symbol, limit=200, interval=None, start_time=None, end_time=None):
        interval = (interval or self.default_interval).strip().lower()
        if interval not in {'1d', '1day', 'day', 'daily'}:
            raise ValueError(f"JoinQuant provider only supports daily interval (got {interval})")

        start_date, end_date = _daily_range(limit=limit, start_time=start_time, end_time=end_time)
        result = self.market_data_service.get_market_data(symbol, start_date, end_date)
        self.last_data_range_notice = result.get("data_range_notice")

        bars = [_to_bar(row) for row in result["bars"]]
        try:
            limit = int(limit) if limit is not None else None
        except (TypeError, ValueError):
            limit = None
        if limit and len(bars) > limit:
            bars = bars[-limit:]
        return bars

    def get_latest_price(self, symbol):
        bars = self.get_bars(symbol, limit=1)
        if not bars:
            raise ValueError(f"No market data available for {symbol}")
        return bars[-1]["close"]


class AkShareBacktestProvider:
    def __init__(self, client=None, default_interval=None, default_adjust=None):
        self.client = client or AkShareClient()
        self.default_interval = default_interval or os.getenv('AKSHARE_INTERVAL', '1d')
        self.default_adjust = default_adjust or os.getenv('AKSHARE_ADJUST', 'qfq')

    def get_bars(self, symbol, limit=200, interval=None, start_time=None, end_time=None):
        interval = (interval or self.default_interval).strip().lower()
        interval_map = {
            '1d': 'daily',
            '1day': 'daily',
            'day': 'daily',
            'daily': 'daily',
            '1w': 'weekly',
            'week': 'weekly',
            'weekly': 'weekly',
            '1m': 'monthly',
            'month': 'monthly',
            'monthly': 'monthly',
        }
        period = interval_map.get(interval)
        if period is None:
            raise ValueError(f"AkShare provider does not support interval {interval}")

        start_date, end_date = _daily_range(limit=limit, start_time=start_time, end_time=end_time)
        rows = self.client.fetch_stock_history(
            symbol,
            start_date,
            end_date,
            period=period,
            adjust=self.default_adjust,
        )
        bars = [_to_bar(row) for row in rows]
        try:
            limit = int(limit) if limit is not None else None
        except (TypeError, ValueError):
            limit = None
        if limit and len(bars) > limit:
            return bars[-limit:]
        return bars

    def get_latest_price(self, symbol):
        quote = self.client.get_latest_quote(symbol)
        if not quote:
            raise ValueError(f"No AkShare quote available for {symbol}")
        return quote["price"]


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


_CANONICAL_PROVIDERS = {'mock', 'auto', 'freegold', 'binance', 'joinquant', 'akshare'}
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
    'joinquant': 'joinquant',
    'jq': 'joinquant',
    'jqdata': 'joinquant',
    'cached': 'joinquant',
    'akshare': 'akshare',
    'ak': 'akshare',
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
    if provider == 'joinquant':
        return JoinQuantBacktestProvider()
    if provider == 'akshare':
        return AkShareBacktestProvider()

    return AutoProvider()

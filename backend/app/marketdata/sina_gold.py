import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..utils.cache import cache_get_json, cache_set_json

logger = logging.getLogger(__name__)

_SINA_API_URL = (
    "https://stock2.finance.sina.com.cn/futures/api/jsonp.php/"
    "var%20{var}=/InnerFuturesNewService.getDailyKLine"
    "?symbol={symbol}&_={ts}"
)

_GOLD_FUTURES_SYMBOLS = {
    "AU0",   # Gold continuous main contract
    "AU1",   # Gold 1st month
    "AU2",   # Gold 2nd month
    "AU3",   # Gold 3rd month
}

_SYMBOL_MAP = {
    "XAUUSD": "AU0",
    "XAU": "AU0",
    "GOLD": "AU0",
    "GCF": "AU0",
    "GC=F": "AU0",
    "AU0": "AU0",
    "AU1": "AU1",
    "AU2": "AU2",
    "AU3": "AU3",
}


class SinaGoldAPIError(RuntimeError):
    pass


def _resolve_symbol(symbol):
    if not symbol:
        return "AU0"
    key = str(symbol).upper().replace("/", "").replace("-", "")
    return _SYMBOL_MAP.get(key, "AU0")


def _to_millis(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return _to_millis(float(value))
        except ValueError:
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return int(parsed.timestamp() * 1000)
            except ValueError as exc:
                raise TypeError(f"Unsupported timestamp value: {value}") from exc
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return int(value.timestamp() * 1000)
    if isinstance(value, (int, float)):
        if value > 1_000_000_000_000:
            return int(value)
        return int(value * 1000)
    raise TypeError(f"Unsupported timestamp type: {type(value)}")


def _date_to_millis(date_str):
    parsed = datetime.strptime(date_str, "%Y-%m-%d")
    parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp() * 1000)


class SinaGoldClient:
    """Free gold futures data from Sina Finance (上海期货交易所黄金期货).

    Provides OHLCV daily bars from 2008 to present, denominated in CNY/gram.
    No API key required. Accessible from within China.
    """

    def __init__(self, data_cache_ttl=None, timeout=None):
        self.data_cache_ttl = int(
            data_cache_ttl or os.getenv("SINA_GOLD_CACHE_TTL", "21600")
        )
        self.timeout = float(timeout or os.getenv("SINA_GOLD_API_TIMEOUT", "15"))

    def _fetch_daily_kline(self, sina_symbol):
        var_name = sina_symbol
        url = _SINA_API_URL.format(
            var=var_name,
            symbol=sina_symbol,
            ts=int(time.time() * 1000),
        )
        request = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "*/*",
        })
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            raise SinaGoldAPIError(f"Sina API error {exc.code}: {exc.reason}")
        except URLError as exc:
            raise SinaGoldAPIError(f"Sina API request failed: {exc.reason}")

        match = re.search(r'=\((\[.*\])\)', body, re.DOTALL)
        if not match:
            raise SinaGoldAPIError("Sina API returned unexpected format")
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            raise SinaGoldAPIError("Sina API returned non-JSON payload") from exc

    def _load_dataset(self, symbol, use_cache=True):
        sina_symbol = _resolve_symbol(symbol)
        cache_key = f"sinagold:daily:{sina_symbol}"

        if use_cache:
            cached = cache_get_json(cache_key)
            if cached is not None:
                return cached

        raw = self._fetch_daily_kline(sina_symbol)
        if not isinstance(raw, list):
            raise SinaGoldAPIError("Sina API returned unexpected payload")

        if use_cache:
            cache_set_json(cache_key, raw, ttl=self.data_cache_ttl)
        return raw

    def get_klines(
        self,
        symbol=None,
        interval="1d",
        limit=200,
        start_time=None,
        end_time=None,
        use_cache=True,
    ):
        raw_interval = (interval or "1d").strip().lower()
        if raw_interval not in {"1d", "1day", "day", "daily"}:
            logger.warning(
                "Sina Gold API only supports daily interval; got interval=%s",
                raw_interval,
            )

        data = self._load_dataset(symbol, use_cache=use_cache)

        bars = []
        for item in data:
            date_str = item.get("d")
            if not date_str:
                continue
            try:
                ts = _date_to_millis(date_str)
                bar = {
                    "time": ts,
                    "open": float(item["o"]),
                    "high": float(item["h"]),
                    "low": float(item["l"]),
                    "close": float(item["c"]),
                    "volume": float(item["v"]),
                }
            except (ValueError, TypeError, KeyError):
                continue
            bars.append(bar)

        bars.sort(key=lambda bar: bar["time"])

        start_ms = _to_millis(start_time)
        end_ms = _to_millis(end_time)
        if start_ms is not None:
            bars = [bar for bar in bars if bar["time"] >= start_ms]
        if end_ms is not None:
            bars = [bar for bar in bars if bar["time"] <= end_ms]

        try:
            limit = int(limit) if limit is not None else None
        except (TypeError, ValueError):
            limit = None
        if limit and limit > 0 and len(bars) > limit:
            bars = bars[-limit:]

        return bars

    def get_latest_price(self, symbol=None, use_cache=True):
        bars = self.get_klines(symbol, interval="1d", limit=1, use_cache=use_cache)
        if not bars:
            raise SinaGoldAPIError("No gold price data available from Sina Finance")
        return bars[-1]["close"]

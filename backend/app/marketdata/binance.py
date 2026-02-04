import json
import logging
import os
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..utils.cache import cache_get_json, cache_set_json


logger = logging.getLogger(__name__)


class BinanceAPIError(RuntimeError):
    pass


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
                parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return int(parsed.timestamp() * 1000)
            except ValueError as exc:
                raise TypeError(f"Unsupported timestamp value: {value}") from exc
    if isinstance(value, datetime):
        return int(value.timestamp() * 1000)
    if isinstance(value, (int, float)):
        if value > 1_000_000_000_000:
            return int(value)
        return int(value * 1000)
    raise TypeError(f"Unsupported timestamp type: {type(value)}")


class BinanceClient:
    def __init__(
        self,
        base_url=None,
        timeout=None,
        kline_cache_ttl=None,
        price_cache_ttl=None,
    ):
        self.base_url = base_url or os.getenv('BINANCE_BASE_URL', 'https://api.binance.com')
        self.timeout = float(timeout or os.getenv('BINANCE_API_TIMEOUT', '10'))
        self.kline_cache_ttl = int(kline_cache_ttl or os.getenv('BINANCE_KLINE_CACHE_TTL', '300'))
        self.price_cache_ttl = int(price_cache_ttl or os.getenv('BINANCE_PRICE_CACHE_TTL', '2'))

    def _request(self, path, params=None):
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{urlencode(params)}"
        request = Request(url, headers={'Accept': 'application/json'})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode('utf-8')
                status = getattr(response, 'status', 200)
                if status >= 400:
                    raise BinanceAPIError(f"Binance API error {status}: {body}")
        except HTTPError as exc:
            body = ''
            try:
                body = exc.read().decode('utf-8')
            except Exception:
                body = exc.reason
            raise BinanceAPIError(f"Binance API error {exc.code}: {body}")
        except URLError as exc:
            raise BinanceAPIError(f"Binance API request failed: {exc.reason}")

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise BinanceAPIError("Binance API returned non-JSON response") from exc

        if isinstance(payload, dict) and payload.get('code') is not None and payload.get('msg'):
            raise BinanceAPIError(f"Binance API error {payload['code']}: {payload['msg']}")
        return payload

    def get_klines(self, symbol, interval='1m', limit=200, start_time=None, end_time=None, use_cache=True):
        symbol = symbol.upper()
        limit = max(1, min(int(limit), 1000))
        start_ms = _to_millis(start_time)
        end_ms = _to_millis(end_time)
        cache_key = f"binance:klines:{symbol}:{interval}:{start_ms or 'none'}:{end_ms or 'none'}:{limit}"

        if use_cache:
            cached = cache_get_json(cache_key)
            if cached is not None:
                return cached

        params = {'symbol': symbol, 'interval': interval, 'limit': limit}
        if start_ms is not None:
            params['startTime'] = start_ms
        if end_ms is not None:
            params['endTime'] = end_ms

        data = self._request('/api/v3/klines', params=params)
        bars = [
            {
                "time": item[0],
                "open": float(item[1]),
                "high": float(item[2]),
                "low": float(item[3]),
                "close": float(item[4]),
                "volume": float(item[5]),
            }
            for item in data
        ]

        if use_cache:
            cache_set_json(cache_key, bars, ttl=self.kline_cache_ttl)
        return bars

    def get_latest_price(self, symbol, use_cache=True):
        symbol = symbol.upper()
        cache_key = f"binance:price:{symbol}"
        if use_cache:
            cached = cache_get_json(cache_key)
            if cached is not None:
                return float(cached["price"])

        data = self._request('/api/v3/ticker/price', params={'symbol': symbol})
        price = float(data['price'])
        if use_cache:
            cache_set_json(cache_key, {"price": price}, ttl=self.price_cache_ttl)
        return price

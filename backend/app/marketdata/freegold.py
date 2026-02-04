import json
import logging
import os
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..utils.cache import cache_get_json, cache_set_json


logger = logging.getLogger(__name__)


class FreeGoldAPIError(RuntimeError):
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
    if not date_str:
        raise ValueError("Missing date value")
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        parsed = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)
    return int(parsed.timestamp() * 1000)


class FreeGoldClient:
    def __init__(self, base_url=None, timeout=None, data_cache_ttl=None):
        self.base_url = base_url or os.getenv('FREEGOLD_BASE_URL', 'https://freegoldapi.com')
        self.timeout = float(timeout or os.getenv('FREEGOLD_API_TIMEOUT', '10'))
        self.data_cache_ttl = int(data_cache_ttl or os.getenv('FREEGOLD_DATA_CACHE_TTL', '21600'))

    def _request(self, path):
        url = f"{self.base_url}{path}"
        request = Request(url, headers={'Accept': 'application/json'})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode('utf-8')
                status = getattr(response, 'status', 200)
                if status >= 400:
                    raise FreeGoldAPIError(f"FreeGold API error {status}: {body}")
        except HTTPError as exc:
            body = ''
            try:
                body = exc.read().decode('utf-8')
            except Exception:
                body = exc.reason
            raise FreeGoldAPIError(f"FreeGold API error {exc.code}: {body}")
        except URLError as exc:
            raise FreeGoldAPIError(f"FreeGold API request failed: {exc.reason}")

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise FreeGoldAPIError("FreeGold API returned non-JSON response") from exc
        return payload

    def _load_latest_dataset(self, use_cache=True):
        cache_key = "freegold:data:latest"
        if use_cache:
            cached = cache_get_json(cache_key)
            if cached is not None:
                return cached

        payload = self._request('/data/latest.json')
        if not isinstance(payload, list):
            raise FreeGoldAPIError("FreeGold API returned unexpected payload")

        if use_cache:
            cache_set_json(cache_key, payload, ttl=self.data_cache_ttl)
        return payload

    def get_klines(self, symbol=None, interval='1d', limit=200, start_time=None, end_time=None, use_cache=True):
        interval = (interval or '1d').strip().lower()
        if interval not in {'1d', '1day', 'day', 'daily'}:
            logger.warning("FreeGold API only supports daily data; got interval=%s", interval)

        data = self._load_latest_dataset(use_cache=use_cache)
        bars = []
        for item in data:
            date_value = item.get('date')
            price_value = item.get('price')
            if date_value is None or price_value is None:
                continue
            try:
                price = float(price_value)
                ts = _date_to_millis(date_value)
            except (ValueError, TypeError):
                continue
            bars.append({
                "time": ts,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": 0.0,
            })

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
        data = self._load_latest_dataset(use_cache=use_cache)
        if not data:
            raise FreeGoldAPIError("FreeGold API returned empty dataset")
        latest = data[-1]
        return float(latest['price'])

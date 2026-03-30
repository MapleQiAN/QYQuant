from datetime import date, datetime, time, timezone

from ...providers import AkShareClient
from .base import MarketDataAdapter


def _coerce_date(value):
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None
        return date.fromisoformat(normalized[:10])
    raise TypeError(f"Unsupported date type: {type(value)}")


def _to_bar(row):
    trade_date = _coerce_date(row["trade_date"])
    timestamp = datetime.combine(trade_date, time.min, tzinfo=timezone.utc)
    return {
        "time": int(timestamp.timestamp() * 1000),
        "open": row["open"],
        "high": row["high"],
        "low": row["low"],
        "close": row["close"],
        "volume": row["volume"],
    }


class AKShareLikeMarketDataAdapter(MarketDataAdapter):
    def __init__(self, client=None):
        self.client = client or AkShareClient()

    def get_bars(self, symbol, interval, start_time=None, end_time=None, limit=None):
        if hasattr(self.client, "fetch_stock_history"):
            interval_map = {
                "1d": "daily",
                "daily": "daily",
                "1w": "weekly",
                "weekly": "weekly",
                "1m": "monthly",
                "monthly": "monthly",
            }
            period = interval_map.get(str(interval or "1d").strip().lower())
            if period is None:
                raise ValueError(f"Unsupported interval for AkShare adapter: {interval}")
            rows = self.client.fetch_stock_history(
                symbol,
                _coerce_date(start_time),
                _coerce_date(end_time),
                period=period,
            )
        else:
            rows = self.client.fetch_bars(
                symbol,
                _coerce_date(start_time),
                _coerce_date(end_time),
                interval,
            )
        bars = [_to_bar(row) for row in rows]
        try:
            limit = int(limit) if limit is not None else None
        except (TypeError, ValueError):
            limit = None
        if limit and len(bars) > limit:
            return bars[-limit:]
        return bars

    def get_latest_quote(self, symbol):
        return self.client.get_latest_quote(symbol)

    def supports_market(self, market):
        return str(market or "").strip().lower() in {"cn", "a", "ashare", "a_share"}

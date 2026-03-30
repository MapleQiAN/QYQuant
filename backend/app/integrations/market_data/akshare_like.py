from datetime import date, datetime, time, timezone

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
        self.client = client

    def get_bars(self, symbol, interval, start_time=None, end_time=None, limit=None):
        if self.client is None:
            raise RuntimeError("AKShare-like adapter requires an injected public market data client")
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
        if self.client is None:
            raise RuntimeError("AKShare-like adapter requires an injected public market data client")
        return self.client.get_latest_quote(symbol)

    def supports_market(self, market):
        return str(market or "").strip().lower() in {"cn", "a", "ashare", "a_share"}

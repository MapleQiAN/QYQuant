from datetime import date, datetime, time, timezone

from ...providers.joinquant import JoinQuantClient
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


class JoinQuantMarketDataAdapter(MarketDataAdapter):
    def __init__(self, client=None):
        self.client = client or JoinQuantClient()

    def get_bars(self, symbol, interval, start_time=None, end_time=None, limit=None):
        if not self.supports_interval(interval):
            raise ValueError(f"Unsupported interval for JoinQuant adapter: {interval}")

        rows = self.client.fetch_daily_data(
            symbol,
            _coerce_date(start_time),
            _coerce_date(end_time),
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
        bars = self.get_bars(symbol, interval="1d", limit=1)
        if not bars:
            return None
        latest = bars[-1]
        return {"symbol": symbol, "price": latest["close"], "time": latest["time"]}

    def supports_interval(self, interval):
        normalized = str(interval or "1d").strip().lower()
        return normalized in {"1d", "1day", "day", "daily"}

    def supports_market(self, market):
        return str(market or "").strip().lower() in {"cn", "a", "ashare", "a_share"}

    def healthcheck(self):
        if hasattr(self.client, "healthcheck"):
            return bool(self.client.healthcheck())
        return True

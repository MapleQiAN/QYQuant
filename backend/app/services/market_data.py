from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from ..extensions import db
from ..models import MarketDataCache
from ..providers.joinquant import JoinQuantClient


def _coerce_date(value):
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            raise ValueError("Missing date value")
        return date.fromisoformat(normalized[:10])
    raise TypeError(f"Unsupported date type: {type(value)}")


def _weekday_dates(start_date, end_date):
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:
            yield current
        current += timedelta(days=1)


class MarketDataService:
    def __init__(self, client=None, session=None):
        self.client = client or JoinQuantClient()
        self.session = session or db.session

    def get_market_data(self, symbol, start_date, end_date):
        start_date = _coerce_date(start_date)
        end_date = _coerce_date(end_date)
        if end_date < start_date:
            raise ValueError("end_date must be greater than or equal to start_date")

        cached_rows = self._query_cached(symbol, start_date, end_date)
        missing_dates = self._compute_missing_weekdays(start_date, end_date, cached_rows)
        if not missing_dates:
            return {
                "bars": [self._to_payload(row) for row in cached_rows],
                "data_range_notice": None,
            }

        try:
            fetched_rows = self.client.fetch_daily_data(symbol, min(missing_dates), max(missing_dates))
        except Exception:
            return {
                "bars": [self._to_payload(row) for row in cached_rows],
                "data_range_notice": self._build_range_notice(cached_rows),
            }

        if fetched_rows:
            self._bulk_insert(fetched_rows)
            self.session.commit()

        refreshed_rows = self._query_cached(symbol, start_date, end_date)
        return {
            "bars": [self._to_payload(row) for row in refreshed_rows],
            "data_range_notice": None,
        }

    def _query_cached(self, symbol, start_date, end_date):
        stmt = (
            select(MarketDataCache)
            .where(MarketDataCache.symbol == symbol)
            .where(MarketDataCache.trade_date >= start_date)
            .where(MarketDataCache.trade_date <= end_date)
            .order_by(MarketDataCache.trade_date.asc())
        )
        return list(self.session.execute(stmt).scalars())

    def _compute_missing_weekdays(self, start_date, end_date, cached_rows):
        cached_dates = {row.trade_date for row in cached_rows}
        return [trade_date for trade_date in _weekday_dates(start_date, end_date) if trade_date not in cached_dates]

    def _bulk_insert(self, rows):
        payload = [
            {
                "symbol": item["symbol"],
                "trade_date": _coerce_date(item["trade_date"]),
                "open": item["open"],
                "high": item["high"],
                "low": item["low"],
                "close": item["close"],
                "volume": item["volume"],
                "source": item.get("source", "joinquant"),
            }
            for item in rows
        ]
        if not payload:
            return

        table = MarketDataCache.__table__
        dialect = self.session.get_bind().dialect.name
        if dialect == "postgresql":
            stmt = pg_insert(table).values(payload).on_conflict_do_nothing(index_elements=["symbol", "trade_date"])
            self.session.execute(stmt)
            return
        if dialect == "sqlite":
            stmt = sqlite_insert(table).values(payload).on_conflict_do_nothing(index_elements=["symbol", "trade_date"])
            self.session.execute(stmt)
            return

        for item in payload:
            exists = self.session.get(MarketDataCache, (item["symbol"], item["trade_date"]))
            if exists is None:
                self.session.add(MarketDataCache(**item))

    def _build_range_notice(self, rows):
        if not rows:
            return "数据源暂不可用，且缓存中没有可用的历史行情数据。"
        return (
            f"数据源暂不可用，仅返回缓存区间 {rows[0].trade_date.isoformat()} "
            f"至 {rows[-1].trade_date.isoformat()} 的历史行情数据。"
        )

    def _to_payload(self, row):
        return {
            "symbol": row.symbol,
            "trade_date": row.trade_date,
            "open": float(row.open),
            "high": float(row.high),
            "low": float(row.low),
            "close": float(row.close),
            "volume": int(row.volume),
            "source": row.source,
        }

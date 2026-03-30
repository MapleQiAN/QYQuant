import importlib
from datetime import date, datetime


class AkShareAPIError(RuntimeError):
    pass


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


def _normalize_symbol(symbol):
    raw = str(symbol or "").strip()
    if not raw:
        raise ValueError("symbol is required")
    upper = raw.upper()
    if "." in upper:
        upper = upper.split(".", 1)[0]
    if upper.startswith(("SH", "SZ", "BJ")) and len(upper) > 2:
        upper = upper[2:]
    if upper.endswith(("XSHE", "XSHG")) and len(upper) > 4:
        upper = upper[:-5]
    return upper


def _matches_symbol(value, symbol):
    return _normalize_symbol(value) == _normalize_symbol(symbol)


def _to_float(value):
    if value in (None, ""):
        return None
    return float(value)


def _to_int(value):
    if value in (None, ""):
        return None
    return int(float(value))


class AkShareClient:
    def __init__(self, sdk=None):
        self._sdk = sdk

    def _load_sdk(self):
        if self._sdk is not None:
            return self._sdk
        try:
            self._sdk = importlib.import_module("akshare")
        except ImportError as exc:
            raise AkShareAPIError("akshare is not installed") from exc
        return self._sdk

    def fetch_stock_history(self, symbol, start_date, end_date, period="daily", adjust="qfq"):
        sdk = self._load_sdk()
        normalized_symbol = _normalize_symbol(symbol)
        start_date = _coerce_date(start_date)
        end_date = _coerce_date(end_date)
        frame = sdk.stock_zh_a_hist(
            symbol=normalized_symbol,
            period=period,
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
            adjust=adjust,
        )
        if frame is None or frame.empty:
            return []

        rows = []
        for _, row in frame.iterrows():
            rows.append(
                {
                    "symbol": symbol,
                    "trade_date": _coerce_date(row["日期"]),
                    "open": _to_float(row["开盘"]),
                    "high": _to_float(row["最高"]),
                    "low": _to_float(row["最低"]),
                    "close": _to_float(row["收盘"]),
                    "volume": _to_int(row["成交量"]),
                    "source": "akshare",
                }
            )
        return rows

    def fetch_stock_spot(self, symbol):
        sdk = self._load_sdk()
        frame = sdk.stock_zh_a_spot()
        if frame is None or frame.empty:
            raise AkShareAPIError(f"No realtime quote available for {symbol}")

        for _, row in frame.iterrows():
            if _matches_symbol(row.get("代码"), symbol):
                return {
                    "symbol": symbol,
                    "name": row.get("名称"),
                    "price": _to_float(row.get("最新价")),
                    "open": _to_float(row.get("今开")),
                    "high": _to_float(row.get("最高")),
                    "low": _to_float(row.get("最低")),
                    "prev_close": _to_float(row.get("昨收")),
                    "volume": _to_int(row.get("成交量")),
                    "turnover": _to_float(row.get("成交额")),
                    "timestamp": row.get("时间戳"),
                    "source": "akshare",
                }
        raise AkShareAPIError(f"Symbol {symbol} was not found in AkShare realtime quotes")

    def fetch_futures_quote(self, symbol, market="CF", adjust="0"):
        sdk = self._load_sdk()
        try:
            frame = sdk.futures_zh_spot(symbol=symbol, market=market, adjust=adjust)
        except TypeError:
            frame = sdk.futures_zh_spot(subscribe_list=symbol, market=market, adjust=adjust)
        if frame is None or frame.empty:
            raise AkShareAPIError(f"No futures quote available for {symbol}")

        row = frame.iloc[0]
        return {
            "symbol": row.get("symbol", symbol),
            "time": row.get("time"),
            "open": _to_float(row.get("open")),
            "high": _to_float(row.get("high")),
            "low": _to_float(row.get("low")),
            "price": _to_float(row.get("current_price")),
            "volume": _to_int(row.get("volume")),
            "source": "akshare",
        }

    def fetch_fund_nav(self, symbol):
        sdk = self._load_sdk()
        frame = sdk.fund_open_fund_daily_em()
        if frame is None or frame.empty:
            raise AkShareAPIError(f"No fund NAV data available for {symbol}")

        for _, row in frame.iterrows():
            if str(row.get("基金代码")) == str(symbol):
                return {
                    "symbol": str(symbol),
                    "name": row.get("基金简称"),
                    "unit_nav": _to_float(row.get("单位净值")),
                    "accumulated_nav": _to_float(row.get("累计净值")),
                    "daily_growth_rate": _to_float(row.get("日增长率")),
                    "purchase_status": row.get("申购状态"),
                    "redemption_status": row.get("赎回状态"),
                    "source": "akshare",
                }
        raise AkShareAPIError(f"Fund {symbol} was not found in AkShare fund NAV data")

    def get_latest_quote(self, symbol):
        return self.fetch_stock_spot(symbol)

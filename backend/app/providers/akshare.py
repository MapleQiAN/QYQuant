import importlib
from datetime import date, datetime, timedelta


class AkShareAPIError(RuntimeError):
    pass


DATE_CN = "\u65e5\u671f"
OPEN_CN = "\u5f00\u76d8"
HIGH_CN = "\u6700\u9ad8"
LOW_CN = "\u6700\u4f4e"
CLOSE_CN = "\u6536\u76d8"
VOLUME_CN = "\u6210\u4ea4\u91cf"
CODE_CN = "\u4ee3\u7801"
NAME_CN = "\u540d\u79f0"
LATEST_PRICE_CN = "\u6700\u65b0\u4ef7"
LATEST_CN = "\u6700\u65b0"
TODAY_OPEN_CN = "\u4eca\u5f00"
PREV_CLOSE_CN = "\u6628\u6536"
TURNOVER_CN = "\u6210\u4ea4\u989d"
TIMESTAMP_CN = "\u65f6\u95f4\u6233"
UPDATED_AT_CN = "\u66f4\u65b0\u65f6\u95f4"
FUND_CODE_CN = "\u57fa\u91d1\u4ee3\u7801"
FUND_NAME_CN = "\u57fa\u91d1\u7b80\u79f0"
UNIT_NAV_CN = "\u5355\u4f4d\u51c0\u503c"
ACC_NAV_CN = "\u7d2f\u8ba1\u51c0\u503c"
DAILY_GROWTH_RATE_CN = "\u65e5\u589e\u957f\u7387"
PURCHASE_STATUS_CN = "\u7533\u8d2d\u72b6\u6001"
REDEMPTION_STATUS_CN = "\u8d4e\u56de\u72b6\u6001"


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


def _pick_first(row, *keys):
    for key in keys:
        if key in row and row.get(key) not in (None, ""):
            return row.get(key)
    return None


def _pick_suffix_value(row, suffix):
    for key in row.index:
        if str(key).endswith(suffix):
            value = row.get(key)
            if value not in (None, ""):
                return value
    return None


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
                    "trade_date": _coerce_date(_pick_first(row, DATE_CN, "\u93c3\u30e6\u6e67")),
                    "open": _to_float(_pick_first(row, OPEN_CN, "\u5bee\u20ac\u9429\u9429\u95bb")),
                    "high": _to_float(_pick_first(row, HIGH_CN, "\u93c8\u20ac\u6960\u59e4")),
                    "low": _to_float(_pick_first(row, LOW_CN, "\u93c8\u20ac\u5a34\u9429")),
                    "close": _to_float(_pick_first(row, CLOSE_CN, "\u93c1\u5280\u6d0f")),
                    "volume": _to_int(_pick_first(row, VOLUME_CN, "\u93b9\u6c2b\u52a0\u6c26\u6c26\u95c2")),
                    "source": "akshare",
                }
            )
        return rows

    def fetch_stock_spot(self, symbol):
        sdk = self._load_sdk()
        realtime_errors = []

        for loader in ("stock_zh_a_spot_em", "stock_zh_a_spot"):
            if not hasattr(sdk, loader):
                continue
            try:
                frame = getattr(sdk, loader)()
            except Exception as exc:
                realtime_errors.append(exc)
                continue
            if frame is None or frame.empty:
                continue

            for _, row in frame.iterrows():
                row_symbol = _pick_first(row, CODE_CN, "\u6d20\u72c5\u7d4b")
                if _matches_symbol(row_symbol, symbol):
                    return {
                        "symbol": symbol,
                        "name": _pick_first(row, NAME_CN, "\u95b8\u6a3a\u7d03"),
                        "price": _to_float(_pick_first(row, LATEST_PRICE_CN, LATEST_CN, "\u93c8\u20ac\u93c2\u95ca\u98a0\u73af")),
                        "open": _to_float(_pick_first(row, TODAY_OPEN_CN, "\u6d74\u72b2\u7d71")),
                        "high": _to_float(_pick_first(row, HIGH_CN, "\u93c8\u20ac\u6960\u59e4")),
                        "low": _to_float(_pick_first(row, LOW_CN, "\u93c8\u20ac\u5a34\u9429")),
                        "prev_close": _to_float(_pick_first(row, PREV_CLOSE_CN, "\u95ba\u52ed\u52c4\u93c1")),
                        "volume": _to_int(_pick_first(row, VOLUME_CN, "\u93b9\u6c2b\u52a0\u6c26\u6c26\u95c2")),
                        "turnover": _to_float(_pick_first(row, TURNOVER_CN, "\u93b9\u6c2b\u52a0\u6c26\u9865")),
                        "timestamp": _pick_first(row, TIMESTAMP_CN, UPDATED_AT_CN, "\u95ba\u4f74\u68ff\u59ab\u9a38"),
                        "source": "akshare",
                    }

        end_date = date.today()
        start_date = end_date - timedelta(days=14)
        history = self.fetch_stock_history(symbol, start_date, end_date)
        if history:
            latest = history[-1]
            previous = history[-2] if len(history) > 1 else None
            return {
                "symbol": symbol,
                "name": None,
                "price": latest.get("close"),
                "open": latest.get("open"),
                "high": latest.get("high"),
                "low": latest.get("low"),
                "prev_close": previous.get("close") if previous else latest.get("close"),
                "volume": latest.get("volume"),
                "turnover": None,
                "timestamp": latest.get("trade_date").isoformat() if latest.get("trade_date") else None,
                "source": "akshare_history_fallback",
            }

        if realtime_errors:
            raise AkShareAPIError(f"AkShare realtime quote failed for {symbol}: {realtime_errors[-1]}")
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
            fund_code = _pick_first(row, FUND_CODE_CN, "\u95b8\u7c34\u692d\u9377\u7487\u797a")
            if str(fund_code) == str(symbol):
                return {
                    "symbol": str(symbol),
                    "name": _pick_first(row, FUND_NAME_CN),
                    "unit_nav": _to_float(
                        _pick_first(row, UNIT_NAV_CN)
                        or _pick_suffix_value(row, f"-{UNIT_NAV_CN}")
                    ),
                    "accumulated_nav": _to_float(
                        _pick_first(row, ACC_NAV_CN)
                        or _pick_suffix_value(row, f"-{ACC_NAV_CN}")
                    ),
                    "daily_growth_rate": _to_float(_pick_first(row, DAILY_GROWTH_RATE_CN, "\u95ba\u51aa\u5134\u95c1\u57a8\u82b3")),
                    "purchase_status": _pick_first(row, PURCHASE_STATUS_CN, "\u95bb\u32bf\u8d1d\u9418\u8208\u20ac"),
                    "redemption_status": _pick_first(row, REDEMPTION_STATUS_CN, "\u9427\u5ea1\u3056\u9438\u822c\u20ac"),
                    "source": "akshare",
                }
        raise AkShareAPIError(f"Fund {symbol} was not found in AkShare fund NAV data")

    def get_latest_quote(self, symbol):
        return self.fetch_stock_spot(symbol)

import importlib
import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import date, datetime


class JoinQuantAPIError(RuntimeError):
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
        try:
            return date.fromisoformat(normalized[:10])
        except ValueError as exc:
            raise ValueError(f"Unsupported date value: {value}") from exc
    raise TypeError(f"Unsupported date type: {type(value)}")


class JoinQuantClient:
    def __init__(
        self,
        username=None,
        password=None,
        timeout=None,
        max_retries=None,
        sdk=None,
    ):
        self.username = username or os.getenv("JQDATA_USERNAME")
        self.password = password or os.getenv("JQDATA_PASSWORD")
        self.timeout = float(timeout or os.getenv("JQDATA_REQUEST_TIMEOUT_SECONDS", "3"))
        self.max_retries = int(max_retries or os.getenv("JQDATA_MAX_RETRIES", "2"))
        self._sdk = sdk
        self._authenticated = False

    def _load_sdk(self):
        if self._sdk is not None:
            return self._sdk
        try:
            self._sdk = importlib.import_module("jqdatasdk")
        except ImportError as exc:
            raise JoinQuantAPIError("jqdatasdk is not installed") from exc
        return self._sdk

    def _ensure_authenticated(self):
        if self._authenticated:
            return self._load_sdk()

        if not self.username or not self.password:
            raise JoinQuantAPIError("JQDATA_USERNAME and JQDATA_PASSWORD are required")

        sdk = self._load_sdk()
        try:
            sdk.auth(self.username, self.password)
        except Exception as exc:
            raise JoinQuantAPIError(f"JoinQuant authentication failed: {exc}") from exc

        self._authenticated = True
        return sdk

    def _run_with_timeout(self, func, timeout_seconds):
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(func)
        try:
            return future.result(timeout=timeout_seconds)
        except FutureTimeoutError as exc:
            future.cancel()
            raise JoinQuantAPIError(f"JoinQuant request timed out after {timeout_seconds:.2f} seconds") from exc
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def _execute(self, func):
        deadline = time.monotonic() + self.timeout
        last_error = None
        for attempt in range(self.max_retries + 1):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                return self._run_with_timeout(func, timeout_seconds=remaining)
            except Exception as exc:  # pragma: no cover - error wrapping is validated at service boundary
                last_error = exc
                if attempt >= self.max_retries:
                    break
        if isinstance(last_error, JoinQuantAPIError):
            raise last_error
        if last_error is None:
            raise JoinQuantAPIError(f"JoinQuant request timed out after {self.timeout} seconds")
        raise JoinQuantAPIError(f"JoinQuant request failed: {last_error}") from last_error

    def fetch_daily_data(self, symbol, start_date, end_date):
        sdk = self._ensure_authenticated()
        start_date = _coerce_date(start_date)
        end_date = _coerce_date(end_date)

        def _request():
            return sdk.get_price(
                symbol,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                frequency="daily",
                fields=["open", "high", "low", "close", "volume"],
                skip_paused=True,
                fq="pre",
            )

        payload = self._execute(_request)
        if payload is None or not hasattr(payload, "iterrows"):
            return []

        rows = []
        for index, item in payload.iterrows():
            trade_date = _coerce_date(index)
            rows.append(
                {
                    "symbol": symbol,
                    "trade_date": trade_date,
                    "open": float(item["open"]),
                    "high": float(item["high"]),
                    "low": float(item["low"]),
                    "close": float(item["close"]),
                    "volume": int(item["volume"]),
                    "source": "joinquant",
                }
            )
        return rows

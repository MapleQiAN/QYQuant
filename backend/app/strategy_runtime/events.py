from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from qysp import Account, BarData, ParameterAccessor, Position, StrategyContext as QYSPStrategyContext


INITIAL_CAPITAL = 100_000.0


class RuntimeBarData(BarData):
    def __init__(
        self,
        *,
        symbol: str,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: int,
        datetime: datetime,
        time: int | None = None,
    ) -> None:
        super().__init__(
            symbol=symbol,
            open=open,
            high=high,
            low=low,
            close=close,
            volume=volume,
            datetime=datetime,
        )
        self.time = time

    def get(self, key: str, default: Any = None) -> Any:
        if key == "time":
            return self.time if self.time is not None else default
        return getattr(self, key, default)


class StrategyContext(QYSPStrategyContext):
    def __init__(self, symbol: str, params: dict[str, Any] | None, initial_cash: float = INITIAL_CAPITAL) -> None:
        self.symbol = symbol
        self.params = dict(params or {})
        self.orders: list[dict[str, Any]] = []
        self.logs: list[str] = []
        self._latest_bar: RuntimeBarData | None = None
        super().__init__(
            account=Account(cash=float(initial_cash)),
            parameters=ParameterAccessor(self.params),
        )

    def sync_bar(self, bar: RuntimeBarData) -> None:
        self._latest_bar = bar
        self.symbol = bar.symbol or self.symbol
        self.current_dt = bar.datetime

        position = self.account.positions.get(self.symbol)
        if position is not None:
            position.current_price = float(bar.close)

    def emit_order(self, order: Any) -> None:
        normalized = normalize_order(order, default_symbol=self.symbol)
        if normalized is None:
            return
        self.orders.append(normalized)

    def consume_orders(self) -> list[dict[str, Any]]:
        items = list(self.orders)
        self.orders = []
        return items

    def log(self, message: Any) -> None:
        self.logs.append(str(message)[:500])

    def apply_trade(self, trade: dict[str, Any]) -> None:
        symbol = trade["symbol"]
        price = float(trade["price"])
        quantity = float(trade["quantity"])
        position = self.account.positions.get(symbol)

        if trade["side"] == "buy":
            current_quantity = position.quantity if position is not None else 0.0
            current_cost = position.avg_cost * current_quantity if position is not None else 0.0
            new_quantity = current_quantity + quantity
            avg_cost = (current_cost + price * quantity) / new_quantity if new_quantity > 0 else price
            self.account.positions[symbol] = Position(
                symbol=symbol,
                quantity=new_quantity,
                avg_cost=avg_cost,
                current_price=price,
            )
            self.account.cash -= price * quantity
            return

        self.account.cash += price * quantity
        if position is None:
            return

        remaining_quantity = position.quantity - quantity
        if remaining_quantity > 0:
            self.account.positions[symbol] = Position(
                symbol=symbol,
                quantity=remaining_quantity,
                avg_cost=position.avg_cost,
                current_price=price,
            )
            return

        self.account.positions.pop(symbol, None)


def make_bar(symbol: str, raw_bar: dict[str, Any]) -> RuntimeBarData:
    raw_time = raw_bar.get("time", raw_bar.get("datetime"))
    return RuntimeBarData(
        symbol=raw_bar.get("symbol") or symbol,
        open=float(raw_bar.get("open", 0.0)),
        high=float(raw_bar.get("high", 0.0)),
        low=float(raw_bar.get("low", 0.0)),
        close=float(raw_bar.get("close", 0.0)),
        volume=int(raw_bar.get("volume", 0) or 0),
        datetime=_coerce_datetime(raw_time),
        time=int(raw_time) if raw_time is not None else None,
    )


def normalize_order(order: Any, *, default_symbol: str) -> dict[str, Any] | None:
    if order is None:
        return None

    if isinstance(order, dict):
        side = str(order.get("side", "")).lower()
        if side not in {"buy", "sell"}:
            return None
        quantity = _coerce_float(order.get("quantity", 1))
        if quantity is None or quantity <= 0:
            return None
        price = _coerce_float(order.get("price"))
        limit_price = _coerce_float(order.get("limit_price"))
        order_type = str(order.get("order_type", "market")).lower()
        return {
            "symbol": order.get("symbol") or default_symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "limit_price": limit_price,
            "order_type": order_type,
        }

    side = getattr(order, "side", None)
    if hasattr(side, "value"):
        side = side.value
    side = str(side or "").lower()
    if side not in {"buy", "sell"}:
        return None

    quantity = _coerce_float(getattr(order, "quantity", None))
    if quantity is None or quantity <= 0:
        return None

    order_type = getattr(order, "order_type", None)
    if hasattr(order_type, "value"):
        order_type = order_type.value

    return {
        "symbol": getattr(order, "symbol", None) or default_symbol,
        "side": side,
        "quantity": quantity,
        "price": _coerce_float(getattr(order, "price", None)),
        "limit_price": _coerce_float(getattr(order, "limit_price", None)),
        "order_type": str(order_type or "market").lower(),
    }


def resolve_fill_price(order: dict[str, Any], bar: RuntimeBarData) -> float:
    if order.get("price") is not None:
        return float(order["price"])
    if order.get("order_type") == "limit" and order.get("limit_price") is not None:
        return float(order["limit_price"])
    return float(bar.close)


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value

    if value is None:
        return datetime.now(timezone.utc)

    timestamp = float(value)
    if abs(timestamp) >= 10_000_000_000:
        timestamp /= 1000.0
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

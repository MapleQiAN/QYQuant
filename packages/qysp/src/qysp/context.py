"""QYSP SDK 核心类：event_v1 接口规范与 StrategyContext。

定义策略开发所需的所有数据类和类型别名：
- BarData: K 线数据
- Order / OrderSide / OrderType: 订单意图
- Position: 持仓信息
- Account: 账户信息
- StrategyContext: 策略上下文（含 buy/sell 便捷方法）
- ParameterAccessor: 参数访问器
- OnBarCallable: event_v1 标准入口函数签名
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class OrderSide(Enum):
    """订单方向。"""

    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """订单类型。"""

    MARKET = "MARKET"
    LIMIT = "LIMIT"


@dataclass
class BarData:
    """K 线数据。"""

    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    datetime: datetime

    def __post_init__(self) -> None:
        for name in ("open", "high", "low", "close"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} 不能为负数: {getattr(self, name)}")
        if self.volume < 0:
            raise ValueError(f"volume 不能为负数: {self.volume}")


@dataclass
class Order:
    """订单意图指令（不含执行状态）。"""

    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType
    limit_price: float | None = None


@dataclass
class Position:
    """持仓信息。"""

    symbol: str
    quantity: float
    avg_cost: float
    current_price: float

    @property
    def market_value(self) -> float:
        """持仓市值。"""
        return self.quantity * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        """未实现盈亏。"""
        return (self.current_price - self.avg_cost) * self.quantity

    @property
    def unrealized_pnl_pct(self) -> float:
        """未实现盈亏百分比。"""
        return (self.current_price / self.avg_cost - 1) * 100


@dataclass
class Account:
    """账户信息。"""

    cash: float
    positions: dict[str, Position] = field(default_factory=dict)

    @property
    def total_value(self) -> float:
        """账户总价值 = 现金 + 所有持仓市值之和。"""
        return self.cash + sum(p.market_value for p in self.positions.values())


class ParameterAccessor:
    """简易版参数访问器（为 Story 1.3 ParameterProvider 预留接口）。"""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self._data: dict[str, Any] = data if data is not None else {}

    def get(self, key: str, default: Any = None) -> Any:
        """获取参数值，key 不存在时返回 default。"""
        return self._data.get(key, default)


class StrategyContext:
    """策略上下文，提供账户、参数访问及下单便捷方法。"""

    def __init__(
        self,
        account: Account,
        parameters: ParameterAccessor | None = None,  # 也接受 ParameterProvider（子类）
        current_dt: datetime | None = None,
    ) -> None:
        self.account: Account = account
        self.parameters: ParameterAccessor = parameters or ParameterAccessor()
        self.current_dt: datetime | None = current_dt

    def buy(
        self,
        symbol: str,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        limit_price: float | None = None,
    ) -> Order:
        """创建买单。"""
        return Order(
            symbol=symbol,
            side=OrderSide.BUY,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
        )

    def sell(
        self,
        symbol: str,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        limit_price: float | None = None,
    ) -> Order:
        """创建卖单。"""
        return Order(
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
        )


OnBarCallable = Callable[[StrategyContext, BarData], list[Order]]
"""event_v1 标准入口函数签名：on_bar(ctx, data) -> list[Order]。"""

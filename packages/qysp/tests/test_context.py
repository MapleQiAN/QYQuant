"""QYSP SDK 核心类单元测试。"""

from __future__ import annotations

from datetime import datetime

import pytest

from qysp.context import (
    Account,
    BarData,
    Order,
    OrderSide,
    OrderType,
    ParameterAccessor,
    Position,
    StrategyContext,
)


# ── BarData ──────────────────────────────────────────────────────


class TestBarData:
    def test_bardata_creation_valid(self) -> None:
        dt = datetime(2024, 1, 15, 9, 30)
        bar = BarData(
            symbol="600519",
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=10000,
            datetime=dt,
        )
        assert bar.symbol == "600519"
        assert bar.open == 100.0
        assert bar.high == 105.0
        assert bar.low == 99.0
        assert bar.close == 103.0
        assert bar.volume == 10000
        assert bar.datetime == dt

    def test_bardata_negative_price_rejected(self) -> None:
        with pytest.raises(ValueError, match="open 不能为负数"):
            BarData(
                symbol="600519",
                open=-1.0,
                high=105.0,
                low=99.0,
                close=103.0,
                volume=10000,
                datetime=datetime(2024, 1, 15),
            )

    def test_bardata_negative_high_rejected(self) -> None:
        with pytest.raises(ValueError, match="high 不能为负数"):
            BarData(
                symbol="600519",
                open=100.0,
                high=-1.0,
                low=99.0,
                close=103.0,
                volume=10000,
                datetime=datetime(2024, 1, 15),
            )

    def test_bardata_negative_low_rejected(self) -> None:
        with pytest.raises(ValueError, match="low 不能为负数"):
            BarData(
                symbol="600519",
                open=100.0,
                high=105.0,
                low=-1.0,
                close=103.0,
                volume=10000,
                datetime=datetime(2024, 1, 15),
            )

    def test_bardata_negative_close_rejected(self) -> None:
        with pytest.raises(ValueError, match="close 不能为负数"):
            BarData(
                symbol="600519",
                open=100.0,
                high=105.0,
                low=99.0,
                close=-1.0,
                volume=10000,
                datetime=datetime(2024, 1, 15),
            )

    def test_bardata_negative_volume_rejected(self) -> None:
        with pytest.raises(ValueError, match="volume 不能为负数"):
            BarData(
                symbol="600519",
                open=100.0,
                high=105.0,
                low=99.0,
                close=103.0,
                volume=-1,
                datetime=datetime(2024, 1, 15),
            )

    def test_bardata_zero_price_allowed(self) -> None:
        bar = BarData(
            symbol="600519",
            open=0.0,
            high=0.0,
            low=0.0,
            close=0.0,
            volume=0,
            datetime=datetime(2024, 1, 15),
        )
        assert bar.open == 0.0
        assert bar.volume == 0


# ── Order ────────────────────────────────────────────────────────


class TestOrder:
    def test_order_market_buy(self) -> None:
        order = Order(
            symbol="600519",
            side=OrderSide.BUY,
            quantity=100.0,
            order_type=OrderType.MARKET,
        )
        assert order.symbol == "600519"
        assert order.side == OrderSide.BUY
        assert order.quantity == 100.0
        assert order.order_type == OrderType.MARKET
        assert order.limit_price is None

    def test_order_limit_sell(self) -> None:
        order = Order(
            symbol="600519",
            side=OrderSide.SELL,
            quantity=50.0,
            order_type=OrderType.LIMIT,
            limit_price=200.0,
        )
        assert order.side == OrderSide.SELL
        assert order.order_type == OrderType.LIMIT
        assert order.limit_price == 200.0


# ── Position ─────────────────────────────────────────────────────


class TestPosition:
    def test_position_market_value(self) -> None:
        pos = Position(symbol="600519", quantity=100.0, avg_cost=150.0, current_price=180.0)
        assert pos.market_value == 18000.0

    def test_position_unrealized_pnl(self) -> None:
        pos = Position(symbol="600519", quantity=100.0, avg_cost=150.0, current_price=180.0)
        assert pos.unrealized_pnl == 3000.0

    def test_position_unrealized_pnl_pct(self) -> None:
        pos = Position(symbol="600519", quantity=100.0, avg_cost=150.0, current_price=180.0)
        assert pos.unrealized_pnl_pct == pytest.approx(20.0)

    def test_position_unrealized_pnl_negative(self) -> None:
        pos = Position(symbol="600519", quantity=100.0, avg_cost=200.0, current_price=180.0)
        assert pos.unrealized_pnl == -2000.0
        assert pos.unrealized_pnl_pct == pytest.approx(-10.0)


# ── Account ──────────────────────────────────────────────────────


class TestAccount:
    def test_account_total_value_no_positions(self) -> None:
        account = Account(cash=100000.0)
        assert account.total_value == 100000.0

    def test_account_total_value_with_positions(self) -> None:
        positions = {
            "600519": Position(symbol="600519", quantity=100.0, avg_cost=150.0, current_price=180.0),
            "000001": Position(symbol="000001", quantity=200.0, avg_cost=10.0, current_price=12.0),
        }
        account = Account(cash=50000.0, positions=positions)
        # 50000 + 100*180 + 200*12 = 50000 + 18000 + 2400 = 70400
        assert account.total_value == 70400.0


# ── StrategyContext ──────────────────────────────────────────────


class TestStrategyContext:
    def test_strategy_context_account_access(self) -> None:
        account = Account(cash=100000.0)
        ctx = StrategyContext(account=account)
        assert ctx.account is account
        assert ctx.account.cash == 100000.0

    def test_strategy_context_buy(self) -> None:
        ctx = StrategyContext(account=Account(cash=100000.0))
        order = ctx.buy("600519", 100.0)
        assert order.symbol == "600519"
        assert order.side == OrderSide.BUY
        assert order.quantity == 100.0
        assert order.order_type == OrderType.MARKET
        assert order.limit_price is None

    def test_strategy_context_buy_limit(self) -> None:
        ctx = StrategyContext(account=Account(cash=100000.0))
        order = ctx.buy("600519", 100.0, OrderType.LIMIT, 150.0)
        assert order.order_type == OrderType.LIMIT
        assert order.limit_price == 150.0

    def test_strategy_context_sell(self) -> None:
        ctx = StrategyContext(account=Account(cash=100000.0))
        order = ctx.sell("600519", 50.0)
        assert order.side == OrderSide.SELL
        assert order.order_type == OrderType.MARKET

    def test_strategy_context_sell_limit(self) -> None:
        ctx = StrategyContext(account=Account(cash=100000.0))
        order = ctx.sell("600519", 50.0, OrderType.LIMIT, 200.0)
        assert order.order_type == OrderType.LIMIT
        assert order.limit_price == 200.0

    def test_strategy_context_current_dt(self) -> None:
        dt = datetime(2024, 1, 15, 9, 30)
        ctx = StrategyContext(account=Account(cash=100000.0), current_dt=dt)
        assert ctx.current_dt == dt

    def test_strategy_context_default_parameters(self) -> None:
        ctx = StrategyContext(account=Account(cash=100000.0))
        assert isinstance(ctx.parameters, ParameterAccessor)


# ── ParameterAccessor ────────────────────────────────────────────


class TestParameterAccessor:
    def test_parameter_accessor_get_existing(self) -> None:
        accessor = ParameterAccessor({"fast_period": 5, "slow_period": 20})
        assert accessor.get("fast_period") == 5

    def test_parameter_accessor_get_missing_with_default(self) -> None:
        accessor = ParameterAccessor({"fast_period": 5})
        assert accessor.get("slow_period", 20) == 20

    def test_parameter_accessor_get_missing_no_default(self) -> None:
        accessor = ParameterAccessor({"fast_period": 5})
        assert accessor.get("slow_period") is None

    def test_parameter_accessor_empty(self) -> None:
        accessor = ParameterAccessor()
        assert accessor.get("any_key") is None


# ── Public Imports ───────────────────────────────────────────────


class TestPublicImports:
    def test_public_imports(self) -> None:
        from qysp import Account, BarData, Order, Position, StrategyContext

        assert StrategyContext is not None
        assert BarData is not None
        assert Order is not None
        assert Position is not None
        assert Account is not None

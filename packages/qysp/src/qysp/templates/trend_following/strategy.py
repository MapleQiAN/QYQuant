"""Trend following template strategy (dual SMA crossover)."""

from __future__ import annotations

import pandas as pd

from qysp.context import StrategyContext, BarData
from qysp.indicators import cross_over, cross_under, sma


def on_bar(ctx: StrategyContext, data: BarData) -> list:
    """event_v1 entry: buy on golden cross, sell on death cross."""
    fast_period = int(ctx.parameters.get("fast_period", 5))
    slow_period = int(ctx.parameters.get("slow_period", 20))
    if fast_period >= slow_period:
        return []

    # Keep recent close prices for indicator calculations.
    close_history = getattr(ctx, "_close_history", [])
    close_history.append(float(data.close))
    setattr(ctx, "_close_history", close_history[-(slow_period + 20) :])

    if len(close_history) < slow_period + 2:
        return []

    prices = pd.Series(close_history, dtype=float)
    fast_line = sma(prices, period=fast_period)
    slow_line = sma(prices, period=slow_period)

    # Entry condition: fast SMA crosses above slow SMA.
    if bool(cross_over(fast_line, slow_line).iloc[-1]):
        return [ctx.buy(data.symbol, quantity=1)]

    # Exit condition: fast SMA crosses below slow SMA.
    if bool(cross_under(fast_line, slow_line).iloc[-1]):
        return [ctx.sell(data.symbol, quantity=1)]

    return []

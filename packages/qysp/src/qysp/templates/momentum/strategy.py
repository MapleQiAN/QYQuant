"""Momentum template strategy (dual EMA confirmation)."""

from __future__ import annotations

import pandas as pd

from qysp.context import StrategyContext, BarData
from qysp.indicators import cross_over, cross_under, ema


def on_bar(ctx: StrategyContext, data: BarData) -> list:
    """event_v1 entry: trade on EMA crossover with direction filter."""
    ema_period = int(ctx.parameters.get("ema_period", 12))
    signal_period = int(ctx.parameters.get("signal_period", 26))
    if ema_period >= signal_period:
        return []

    close_history = getattr(ctx, "_close_history", [])
    close_history.append(float(data.close))
    setattr(ctx, "_close_history", close_history[-(signal_period + 30) :])

    if len(close_history) < signal_period + 2:
        return []

    prices = pd.Series(close_history, dtype=float)
    fast_ema = ema(prices, period=ema_period)
    slow_ema = ema(prices, period=signal_period)

    slow_up = slow_ema.iloc[-1] > slow_ema.iloc[-2]
    if bool(cross_over(fast_ema, slow_ema).iloc[-1]) and slow_up:
        return [ctx.buy(data.symbol, quantity=1)]

    slow_down = slow_ema.iloc[-1] < slow_ema.iloc[-2]
    if bool(cross_under(fast_ema, slow_ema).iloc[-1]) or slow_down:
        return [ctx.sell(data.symbol, quantity=1)]

    return []

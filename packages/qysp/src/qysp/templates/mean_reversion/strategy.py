"""Mean reversion template strategy (Bollinger bands)."""

from __future__ import annotations

import pandas as pd

from qysp.context import StrategyContext, BarData
from qysp.indicators import bollinger_bands


def on_bar(ctx: StrategyContext, data: BarData) -> list:
    """event_v1 entry: buy below lower band, sell above upper band."""
    bb_period = int(ctx.parameters.get("bb_period", 20))
    bb_std = float(ctx.parameters.get("bb_std", 2.0))

    close_history = getattr(ctx, "_close_history", [])
    close_history.append(float(data.close))
    setattr(ctx, "_close_history", close_history[-(bb_period + 20) :])

    if len(close_history) < bb_period + 2:
        return []

    prices = pd.Series(close_history, dtype=float)
    upper, _, lower = bollinger_bands(prices, period=bb_period, num_std=bb_std)

    last_close = prices.iloc[-1]
    last_upper = upper.iloc[-1]
    last_lower = lower.iloc[-1]

    if last_close < last_lower:
        return [ctx.buy(data.symbol, quantity=1)]

    if last_close > last_upper:
        return [ctx.sell(data.symbol, quantity=1)]

    return []

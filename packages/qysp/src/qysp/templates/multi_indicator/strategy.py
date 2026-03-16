"""Multi-indicator template strategy (SMA + ATR + Bollinger vote)."""

from __future__ import annotations

import pandas as pd

from qysp.context import StrategyContext, BarData
from qysp.indicators import atr, bollinger_bands, sma


def on_bar(ctx: StrategyContext, data: BarData) -> list:
    """event_v1 entry: place order only when 2 of 3 signals agree."""
    sma_period = int(ctx.parameters.get("sma_period", 20))
    atr_period = int(ctx.parameters.get("atr_period", 14))
    bb_period = int(ctx.parameters.get("bb_period", 20))
    bb_std = float(ctx.parameters.get("bb_std", 2.0))

    high_history = getattr(ctx, "_high_history", [])
    low_history = getattr(ctx, "_low_history", [])
    close_history = getattr(ctx, "_close_history", [])
    high_history.append(float(data.high))
    low_history.append(float(data.low))
    close_history.append(float(data.close))

    lookback = max(sma_period, atr_period, bb_period) + 20
    setattr(ctx, "_high_history", high_history[-lookback:])
    setattr(ctx, "_low_history", low_history[-lookback:])
    setattr(ctx, "_close_history", close_history[-lookback:])

    if len(close_history) < max(sma_period, atr_period, bb_period) + 2:
        return []

    close_series = pd.Series(close_history, dtype=float)
    high_series = pd.Series(high_history, dtype=float)
    low_series = pd.Series(low_history, dtype=float)

    trend_line = sma(close_series, period=sma_period)
    atr_line = atr(high_series, low_series, close_series, period=atr_period)
    upper, _, lower = bollinger_bands(close_series, period=bb_period, num_std=bb_std)

    trend_signal = 1 if close_series.iloc[-1] > trend_line.iloc[-1] else -1

    if close_series.iloc[-1] > upper.iloc[-1]:
        band_signal = 1
    elif close_series.iloc[-1] < lower.iloc[-1]:
        band_signal = -1
    else:
        band_signal = 0

    atr_rising = atr_line.iloc[-1] > atr_line.iloc[-2]
    momentum_signal = trend_signal if atr_rising else 0

    score = trend_signal + band_signal + momentum_signal
    if score >= 2:
        return [ctx.buy(data.symbol, quantity=1)]
    if score <= -2:
        return [ctx.sell(data.symbol, quantity=1)]
    return []

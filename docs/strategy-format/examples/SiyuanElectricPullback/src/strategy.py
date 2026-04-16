"""Siyuan Electric pullback strategy for daily A-share backtests."""

from __future__ import annotations

import pandas as pd

from qysp import BarData, Order, StrategyContext, bollinger_bands, sma


def _append_history(ctx: StrategyContext, data: BarData, size: int) -> tuple[list[float], list[float]]:
    close_history = list(getattr(ctx, "_siyuan_close_history", []))
    low_history = list(getattr(ctx, "_siyuan_low_history", []))

    close_history.append(float(data.close))
    low_history.append(float(data.low))

    close_history = close_history[-size:]
    low_history = low_history[-size:]

    setattr(ctx, "_siyuan_close_history", close_history)
    setattr(ctx, "_siyuan_low_history", low_history)
    return close_history, low_history


def on_bar(ctx: StrategyContext, data: BarData) -> list[Order]:
    """event_v1 entrypoint.

    Assumption for "pull back to 10-day SMA":
    - previous close is above previous 10-day SMA
    - current low touches or breaks below current 10-day SMA
    - current close recovers back to or above current 10-day SMA
    """

    fast_sma_period = int(ctx.parameters.get("fast_sma_period", 10))
    slow_sma_period = int(ctx.parameters.get("slow_sma_period", 30))
    bb_period = int(ctx.parameters.get("bb_period", 20))
    bb_std = float(ctx.parameters.get("bb_std", 2.0))
    position_pct = float(ctx.parameters.get("position_pct", 0.95))

    lookback = max(fast_sma_period, slow_sma_period, bb_period) + 5
    close_history, low_history = _append_history(ctx, data, lookback)
    min_history = max(fast_sma_period, slow_sma_period, bb_period) + 1
    if len(close_history) < min_history:
        return []

    close_series = pd.Series(close_history, dtype=float)
    low_series = pd.Series(low_history, dtype=float)

    fast_line = sma(close_series, period=fast_sma_period)
    slow_line = sma(close_series, period=slow_sma_period)
    upper_band, _, _ = bollinger_bands(close_series, period=bb_period, num_std=bb_std)

    current_fast = fast_line.iloc[-1]
    previous_fast = fast_line.iloc[-2]
    current_slow = slow_line.iloc[-1]
    current_upper = upper_band.iloc[-1]
    previous_close = close_series.iloc[-2]
    current_close = close_series.iloc[-1]
    current_low = low_series.iloc[-1]

    if pd.isna(current_fast) or pd.isna(previous_fast) or pd.isna(current_slow) or pd.isna(current_upper):
        return []

    symbol = data.symbol
    position = ctx.account.positions.get(symbol)
    has_position = position is not None and position.quantity > 0

    if has_position:
        if current_close < float(current_slow) or current_close >= float(current_upper):
            return [ctx.sell(symbol, position.quantity)]
        return []

    touched_fast_line = current_low <= float(current_fast)
    recovered_fast_line = current_close >= float(current_fast)
    above_previous_fast = previous_close > float(previous_fast)

    if not (above_previous_fast and touched_fast_line and recovered_fast_line):
        return []

    allocation = max(min(position_pct, 1.0), 0.0)
    quantity = ctx.account.cash * allocation / current_close if current_close > 0 else 0.0
    if quantity <= 0:
        return []

    return [ctx.buy(symbol, quantity)]

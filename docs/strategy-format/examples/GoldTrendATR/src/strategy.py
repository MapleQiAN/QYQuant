"""Gold trend-following strategy with ATR-based risk control."""

from __future__ import annotations

import pandas as pd

from qysp import BarData, Order, StrategyContext, atr, ema, sma


ATR_PERIOD = 14


def _update_history(ctx: StrategyContext, data: BarData, size: int) -> tuple[list[float], list[float], list[float]]:
    close_history = list(getattr(ctx, "_gold_trend_atr_close_history", []))
    high_history = list(getattr(ctx, "_gold_trend_atr_high_history", []))
    low_history = list(getattr(ctx, "_gold_trend_atr_low_history", []))

    close_history.append(float(data.close))
    high_history.append(float(data.high))
    low_history.append(float(data.low))

    close_history = close_history[-size:]
    high_history = high_history[-size:]
    low_history = low_history[-size:]

    setattr(ctx, "_gold_trend_atr_close_history", close_history)
    setattr(ctx, "_gold_trend_atr_high_history", high_history)
    setattr(ctx, "_gold_trend_atr_low_history", low_history)
    return close_history, high_history, low_history


def on_bar(ctx: StrategyContext, data: BarData) -> list[Order]:
    """event_v1 entrypoint for Gold Trend ATR."""
    trend_sma_period = int(ctx.parameters.get("trend_sma_period", 60))
    breakout_lookback = int(ctx.parameters.get("breakout_lookback", 20))
    exit_ema_period = int(ctx.parameters.get("exit_ema_period", 12))
    atr_stop_multiplier = float(ctx.parameters.get("atr_stop_multiplier", 2.8))
    max_entry_extension_atr = float(ctx.parameters.get("max_entry_extension_atr", 1.2))
    position_pct = float(ctx.parameters.get("position_pct", 0.95))

    history_size = max(trend_sma_period, breakout_lookback + 1, exit_ema_period, ATR_PERIOD) + 5
    close_history, high_history, low_history = _update_history(ctx, data, history_size)

    min_history = max(trend_sma_period, breakout_lookback + 1, exit_ema_period, ATR_PERIOD)
    if len(close_history) < min_history:
        return []

    close_series = pd.Series(close_history, dtype=float)
    high_series = pd.Series(high_history, dtype=float)
    low_series = pd.Series(low_history, dtype=float)

    trend_line = sma(close_series, period=trend_sma_period)
    exit_line = ema(close_series, period=exit_ema_period)
    atr_line = atr(high_series, low_series, close_series, period=ATR_PERIOD)

    current_trend = trend_line.iloc[-1]
    current_exit = exit_line.iloc[-1]
    current_atr = atr_line.iloc[-1]
    if pd.isna(current_trend) or pd.isna(current_exit) or pd.isna(current_atr) or current_atr <= 0:
        return []

    previous_breakout_high = max(high_history[-(breakout_lookback + 1) : -1])
    price = float(data.close)
    symbol = data.symbol
    position = ctx.account.positions.get(symbol)
    has_position = position is not None and position.quantity > 0

    if has_position:
        peak_price = float(
            getattr(
                ctx,
                "_gold_trend_atr_peak_price",
                max(position.current_price, position.avg_cost, price),
            )
        )
        peak_price = max(peak_price, float(data.high))
        setattr(ctx, "_gold_trend_atr_peak_price", peak_price)

        trailing_stop = peak_price - atr_stop_multiplier * float(current_atr)
        if price < float(current_exit) or price < trailing_stop:
            setattr(ctx, "_gold_trend_atr_peak_price", 0.0)
            return [ctx.sell(symbol, position.quantity)]

        return []

    setattr(ctx, "_gold_trend_atr_peak_price", 0.0)

    if price <= float(current_trend):
        return []
    if price <= previous_breakout_high:
        return []

    max_allowed_entry = float(current_trend) + max_entry_extension_atr * float(current_atr)
    if price > max_allowed_entry:
        return []

    allocation = max(min(position_pct, 1.0), 0.0)
    quantity = ctx.account.cash * allocation / price if price > 0 else 0.0
    if quantity <= 0:
        return []

    setattr(ctx, "_gold_trend_atr_peak_price", float(data.high))
    return [ctx.buy(symbol, quantity)]

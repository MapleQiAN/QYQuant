"""黄金均线趋势策略示例。"""

from __future__ import annotations

import pandas as pd

from qysp import BarData, Order, StrategyContext, sma


def on_bar(ctx: StrategyContext, data: BarData) -> list[Order]:
    """event_v1 入口：均线过滤后的突破跟踪策略。"""
    # 读取全部策略参数。
    trend_sma_period = int(ctx.parameters.get("trend_sma_period", 30))
    breakout_lookback = int(ctx.parameters.get("breakout_lookback", 20))
    max_drawdown_pct = float(ctx.parameters.get("max_drawdown_pct", 6.0))

    # 在上下文里维护收盘价历史，用于计算 SMA 和近期高点。
    close_history = list(getattr(ctx, "_gold_trend_close_history", []))
    close_history.append(float(data.close))
    close_history = close_history[-max(trend_sma_period + breakout_lookback + 5, 2) :]
    setattr(ctx, "_gold_trend_close_history", close_history)

    # 历史不足时不生成交易信号。
    if len(close_history) <= max(trend_sma_period, breakout_lookback):
        return []

    # 使用 SDK 的 sma 指标作为趋势过滤器。
    close_series = pd.Series(close_history, dtype=float)
    trend_line = sma(close_series, period=trend_sma_period)
    current_trend = float(trend_line.iloc[-1])
    previous_breakout_high = max(close_history[-(breakout_lookback + 1) : -1])

    # 读取当前持仓状态。
    symbol = data.symbol
    price = float(data.close)
    position = ctx.account.positions.get(symbol)
    has_position = position is not None and position.quantity > 0

    if has_position:
        # 持仓时记录峰值，用回撤比例控制退出。
        peak_price = float(
            getattr(
                ctx,
                "_gold_trend_peak_price",
                max(position.current_price, position.avg_cost, price),
            )
        )
        peak_price = max(peak_price, float(data.high))
        setattr(ctx, "_gold_trend_peak_price", peak_price)

        # 跌回趋势线下方时卖出。
        if price < current_trend:
            setattr(ctx, "_gold_trend_peak_price", 0.0)
            return [ctx.sell(symbol, position.quantity)]

        # 从持仓期间高点回撤过深时卖出。
        drawdown_pct = (peak_price - price) / peak_price * 100 if peak_price > 0 else 0.0
        if drawdown_pct >= max_drawdown_pct:
            setattr(ctx, "_gold_trend_peak_price", 0.0)
            return [ctx.sell(symbol, position.quantity)]

        return []

    # 空仓时仅在价格位于趋势线上方且突破近期高点时入场。
    if price <= current_trend or price <= previous_breakout_high:
        return []

    quantity = ctx.account.cash / price if price > 0 else 0.0
    if quantity <= 0:
        return []

    setattr(ctx, "_gold_trend_peak_price", float(data.high))
    return [ctx.buy(symbol, quantity)]

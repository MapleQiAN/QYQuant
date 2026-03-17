"""黄金阶梯突破策略示例。"""

from __future__ import annotations

from qysp import BarData, Order, StrategyContext


def _append_history(ctx: StrategyContext, data: BarData, lookback: int) -> list[BarData]:
    """在上下文中保留有限长度的 K 线历史。"""
    history = list(getattr(ctx, "_gold_step_history", []))
    history.append(data)
    trimmed = history[-max(lookback + 2, 2) :]
    setattr(ctx, "_gold_step_history", trimmed)
    return trimmed


def _get_previous_high(history: list[BarData], lookback: int) -> float | None:
    """返回不含当前 K 线的最近 lookback 根最高价。"""
    if len(history) <= 1:
        return None
    window = history[:-1][-lookback:]
    if not window:
        return None
    return max(bar.high for bar in window)


def on_bar(ctx: StrategyContext, data: BarData) -> list[Order]:
    """event_v1 入口：突破前高买入，跌破风控阈值卖出。"""
    # 从 strategy.json 读取全部策略参数。
    breakout_lookback = int(ctx.parameters.get("breakout_lookback", 20))
    drop_one_day_pct = float(ctx.parameters.get("drop_one_day_pct", 3.0))
    drop_from_peak_pct = float(ctx.parameters.get("drop_from_peak_pct", 6.0))

    # 缓存最近的 K 线，供突破判断和单日跌幅判断使用。
    history = _append_history(ctx, data, breakout_lookback)
    previous_high = _get_previous_high(history, breakout_lookback)
    previous_close = history[-2].close if len(history) >= 2 else None

    # 读取当前标的与持仓状态。
    symbol = data.symbol
    price = float(data.close)
    position = ctx.account.positions.get(symbol)
    has_position = position is not None and position.quantity > 0

    if has_position:
        # 持仓期间持续更新峰值，用于累计回撤止损。
        peak_price = float(
            getattr(
                ctx,
                "_gold_step_peak_price",
                max(position.current_price, position.avg_cost, price),
            )
        )
        peak_price = max(peak_price, float(data.high))
        setattr(ctx, "_gold_step_peak_price", peak_price)

        # 单日跌幅超过阈值时立即清仓。
        if previous_close and previous_close > 0:
            one_day_drop_pct = (previous_close - price) / previous_close * 100
            if one_day_drop_pct >= drop_one_day_pct:
                setattr(ctx, "_gold_step_peak_price", 0.0)
                return [ctx.sell(symbol, position.quantity)]

        # 从持仓期最高点回撤超过阈值时清仓。
        if peak_price > 0:
            drawdown_pct = (peak_price - price) / peak_price * 100
            if drawdown_pct >= drop_from_peak_pct:
                setattr(ctx, "_gold_step_peak_price", 0.0)
                return [ctx.sell(symbol, position.quantity)]

        # 风控条件都未触发时继续持有。
        return []

    # 空仓时重置峰值缓存，避免上一笔交易污染下一次判断。
    setattr(ctx, "_gold_step_peak_price", 0.0)

    # 历史不足时不做突破判断。
    if previous_high is None:
        return []

    # 只有收盘价突破前高时才发出买单。
    if price <= previous_high:
        return []

    # 示例使用全仓买入，便于展示 ctx.buy 的基本用法。
    quantity = ctx.account.cash / price if price > 0 else 0.0
    if quantity <= 0:
        return []

    # 记录当前峰值，供后续的累计回撤止损使用。
    setattr(ctx, "_gold_step_peak_price", float(data.high))
    return [ctx.buy(symbol, quantity)]

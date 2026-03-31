"""Minimal daily gold SMA crossover strategy for the current backtest runtime."""


def _average(values):
    if not values:
        return 0.0
    return sum(values) / len(values)


class Strategy:
    def __init__(self, ctx=None):
        self.ctx = ctx
        self.closes = []
        self.position_quantity = 0.0

    def on_bar(self, ctx, bar):
        fast_period = max(int((ctx.params or {}).get("fast_period", 5)), 2)
        slow_period = max(int((ctx.params or {}).get("slow_period", 20)), fast_period + 1)
        order_quantity = float((ctx.params or {}).get("order_quantity", 20.0))

        close = float(bar.get("close", 0.0))
        if close <= 0:
            return None

        self.closes.append(close)
        if len(self.closes) < slow_period + 1:
            return None

        previous_closes = self.closes[:-1]
        current_fast = _average(self.closes[-fast_period:])
        current_slow = _average(self.closes[-slow_period:])
        previous_fast = _average(previous_closes[-fast_period:])
        previous_slow = _average(previous_closes[-slow_period:])

        symbol = bar.get("symbol") or ctx.symbol

        crossed_up = previous_fast <= previous_slow and current_fast > current_slow
        crossed_down = previous_fast >= previous_slow and current_fast < current_slow

        if self.position_quantity <= 0 and crossed_up and order_quantity > 0:
            self.position_quantity = order_quantity
            ctx.emit_order(
                {
                    "symbol": symbol,
                    "side": "buy",
                    "price": close,
                    "quantity": order_quantity,
                }
            )
            ctx.log(f"buy {order_quantity} @ {close}")
            return None

        if self.position_quantity > 0 and crossed_down:
            quantity = self.position_quantity
            self.position_quantity = 0.0
            ctx.emit_order(
                {
                    "symbol": symbol,
                    "side": "sell",
                    "price": close,
                    "quantity": quantity,
                }
            )
            ctx.log(f"sell {quantity} @ {close}")

        return None

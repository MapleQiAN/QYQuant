# Gold SMA Cross

This is a minimal `XAUUSD` daily strategy for verifying that the current backtest runtime can:

- load a `.qys` package
- execute strategy code in the sandbox
- emit buy and sell orders
- generate trades and an equity curve

Logic:

- Buy when the fast SMA crosses above the slow SMA.
- Sell when the fast SMA crosses below the slow SMA.
- Use a fixed `order_quantity` so the strategy does not depend on account APIs.

Why this example exists:

- It does not depend on `pandas`, `qysp`, `ctx.account`, or `ctx.buy()/ctx.sell()`.
- It matches the current local runtime contract implemented in the backend sandbox.
- It is intended as a smoke-test strategy, not a production alpha strategy.

Suggested backtest settings:

- Symbol: `XAUUSD`
- Data source: `auto` or `freegold`
- Interval: `1d`
- Start: `2024-10-01`
- End: `2025-03-31`
- Parameters: `fast_period=3`, `slow_period=8`, `order_quantity=20`

Build package:

```bash
uv run qys build docs/strategy-format/examples/GoldSmaCross --output docs/strategy-format/examples/GoldSmaCross.qys
```

# Gold Trend ATR

This example is a long-only daily gold strategy for `XAUUSD`.

Logic:
- Buy when the close is above the long-term SMA trend filter.
- Require a breakout above the previous `breakout_lookback` bars.
- Skip entries if price is already too extended above the trend line.
- Exit on either a fast EMA breakdown or an ATR-based trailing stop.

Suggested use:
- Start with the default parameters.
- Backtest on daily gold data before importing into live workflows.
- Stress-test `trend_sma_period`, `breakout_lookback`, and `atr_stop_multiplier` instead of overfitting to one setting.

Build package:

```bash
uv run qys build docs/strategy-format/examples/GoldTrendATR --output GoldTrendATR.qys
```

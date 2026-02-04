import math

from app.backtest.engine import _calculate_summary


def test_summary_annualized_return_finite_for_short_duration():
    bars = []
    for i in range(120):
        bars.append({
            "time": 1700000000000 + i * 60000,
            "open": 100 + i * 0.1,
            "high": 100 + i * 0.2,
            "low": 100 + i * 0.05,
            "close": 100 + i * 0.15,
            "volume": 1000 + i,
        })

    summary = _calculate_summary(bars)
    assert math.isfinite(summary["annualizedReturn"])

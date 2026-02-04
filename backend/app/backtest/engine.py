import math

from .providers import get_backtest_provider


def _calculate_summary(bars):
    if len(bars) < 2:
        return {
            "totalReturn": 0,
            "annualizedReturn": 0,
            "sharpeRatio": 0,
            "maxDrawdown": 0,
            "winRate": 0,
            "profitFactor": 0,
            "totalTrades": 0,
            "avgHoldingDays": 0,
        }

    closes = [bar["close"] for bar in bars]
    total_return = (closes[-1] / closes[0] - 1) * 100

    start_ms = bars[0]["time"]
    end_ms = bars[-1]["time"]
    duration_days = max((end_ms - start_ms) / 86_400_000, 1)
    annualized_return = (pow(1 + total_return / 100, 365 / duration_days) - 1) * 100

    returns = [(closes[i] / closes[i - 1] - 1) for i in range(1, len(closes))]
    avg_return = sum(returns) / len(returns)
    variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
    std_dev = math.sqrt(variance)

    if len(bars) > 1:
        period_seconds = max((bars[1]["time"] - bars[0]["time"]) / 1000, 1)
    else:
        period_seconds = 60
    periods_per_year = 31_536_000 / period_seconds
    sharpe_ratio = (avg_return / std_dev * math.sqrt(periods_per_year)) if std_dev > 0 else 0

    max_drawdown = 0
    peak = closes[0]
    for close in closes:
        peak = max(peak, close)
        drawdown = (close / peak - 1) * 100
        if drawdown < max_drawdown:
            max_drawdown = drawdown

    wins = sum(1 for r in returns if r > 0)
    win_rate = wins / len(returns) * 100 if returns else 0
    profit = sum(r for r in returns if r > 0)
    loss = sum(r for r in returns if r < 0)
    profit_factor = profit / abs(loss) if loss < 0 else 0

    avg_holding_days = period_seconds / 86_400

    return {
        "totalReturn": round(total_return, 4),
        "annualizedReturn": round(annualized_return, 4),
        "sharpeRatio": round(sharpe_ratio, 4),
        "maxDrawdown": round(max_drawdown, 4),
        "winRate": round(win_rate, 2),
        "profitFactor": round(profit_factor, 4),
        "totalTrades": len(returns),
        "avgHoldingDays": round(avg_holding_days, 4),
    }


def run_backtest(symbol, strategy='sma', interval=None, limit=120, start_time=None, end_time=None):
    provider = get_backtest_provider()
    kline = provider.get_bars(
        symbol,
        limit=limit,
        interval=interval,
        start_time=start_time,
        end_time=end_time,
    )
    trades = []
    summary = _calculate_summary(kline)
    return {"kline": kline, "trades": trades, "summary": summary}

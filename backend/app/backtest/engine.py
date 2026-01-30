from .providers import MockProvider


def run_backtest(symbol, strategy='sma'):
    provider = MockProvider()
    kline = provider.get_bars(symbol, limit=120)
    trades = []
    summary = {
        "totalReturn": 0.12,
        "annualizedReturn": 0.18,
        "sharpeRatio": 1.2,
        "maxDrawdown": 0.08,
        "winRate": 0.55,
        "profitFactor": 1.4,
        "totalTrades": 12,
        "avgHoldingDays": 3.2,
    }
    return {"kline": kline, "trades": trades, "summary": summary}

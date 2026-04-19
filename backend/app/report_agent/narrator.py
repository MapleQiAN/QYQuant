CORE_KEYS = ("totalReturn", "maxDrawdown", "sharpeRatio", "winRate", "totalTrades")


def _fmt(value):
    if value is None:
        return "--"
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return str(value)


def generate_summary(metrics, tier):
    metrics = metrics or {}
    total_return = _fmt(metrics.get("totalReturn"))
    max_drawdown = _fmt(metrics.get("maxDrawdown"))
    sharpe = _fmt(metrics.get("sharpeRatio"))
    return (
        f"{tier} report summary: total return {total_return}%, "
        f"max drawdown {max_drawdown}%, sharpe {sharpe}."
    )


def annotate_metrics(metrics):
    metrics = metrics or {}
    narrations = {}
    for key in CORE_KEYS:
        if key in metrics:
            narrations[key] = f"{key} is {_fmt(metrics.get(key))} in this backtest."
    return narrations

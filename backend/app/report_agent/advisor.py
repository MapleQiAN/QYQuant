def generate_suggestions(payload, tier):
    metrics = (payload or {}).get("metrics") or {}
    sharpe = metrics.get("sharpeRatio", 0)
    return f"{tier} advisor: review position sizing and retest parameters. Sharpe is {sharpe}."


def generate_alerts(payload, tier):
    metrics = (payload or {}).get("metrics") or {}
    alerts = []

    max_drawdown = metrics.get("maxDrawdown")
    if isinstance(max_drawdown, (int, float)) and max_drawdown <= -20:
        alerts.append(
            {
                "level": "warning",
                "title": "Large drawdown",
                "message": "Maximum drawdown exceeded the review threshold.",
            }
        )

    total_trades = metrics.get("totalTrades")
    if isinstance(total_trades, (int, float)) and total_trades < 5:
        alerts.append(
            {
                "level": "info",
                "title": "Small trade sample",
                "message": "Trade count is low, so the conclusion may be fragile.",
            }
        )

    return alerts

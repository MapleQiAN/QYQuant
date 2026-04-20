def generate_suggestions(payload, tier, locale="en"):
    lang = "zh" if locale == "zh" else "en"
    metrics = (payload or {}).get("metrics") or {}
    sharpe = metrics.get("sharpeRatio", 0)
    if lang == "zh":
        return f"{tier} 建议：请审视仓位管理并重新测试参数。夏普比率为 {sharpe}。"
    return f"{tier} advisor: review position sizing and retest parameters. Sharpe is {sharpe}."


def generate_alerts(payload, tier, locale="en"):
    lang = "zh" if locale == "zh" else "en"
    metrics = (payload or {}).get("metrics") or {}
    alerts = []

    max_drawdown = metrics.get("maxDrawdown")
    if isinstance(max_drawdown, (int, float)) and max_drawdown <= -20:
        if lang == "zh":
            alerts.append(
                {
                    "level": "warning",
                    "title": "回撤过大",
                    "message": "最大回撤已超过审查阈值。",
                }
            )
        else:
            alerts.append(
                {
                    "level": "warning",
                    "title": "Large drawdown",
                    "message": "Maximum drawdown exceeded the review threshold.",
                }
            )

    total_trades = metrics.get("totalTrades")
    if isinstance(total_trades, (int, float)) and total_trades < 5:
        if lang == "zh":
            alerts.append(
                {
                    "level": "info",
                    "title": "交易样本过少",
                    "message": "交易次数较少，结论可能不够稳健。",
                }
            )
        else:
            alerts.append(
                {
                    "level": "info",
                    "title": "Small trade sample",
                    "message": "Trade count is low, so the conclusion may be fragile.",
                }
            )

    return alerts

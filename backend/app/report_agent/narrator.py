CORE_KEYS = ("totalReturn", "maxDrawdown", "sharpeRatio", "winRate", "totalTrades")

_LABELS = {
    "totalReturn": {"en": "Total return", "zh": "总收益率"},
    "maxDrawdown": {"en": "Max drawdown", "zh": "最大回撤"},
    "sharpeRatio": {"en": "Sharpe ratio", "zh": "夏普比率"},
    "winRate": {"en": "Win rate", "zh": "胜率"},
    "totalTrades": {"en": "Total trades", "zh": "总交易次数"},
}


def _fmt(value):
    if value is None:
        return "--"
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return str(value)


def generate_summary(metrics, tier, locale="en"):
    lang = "zh" if locale == "zh" else "en"
    metrics = metrics or {}
    total_return = _fmt(metrics.get("totalReturn"))
    max_drawdown = _fmt(metrics.get("maxDrawdown"))
    sharpe = _fmt(metrics.get("sharpeRatio"))
    if lang == "zh":
        return (
            f"{tier} 报告摘要：总收益率 {total_return}%，"
            f"最大回撤 {max_drawdown}%，夏普比率 {sharpe}。"
        )
    return (
        f"{tier} report summary: total return {total_return}%, "
        f"max drawdown {max_drawdown}%, sharpe {sharpe}."
    )


def annotate_metrics(metrics, locale="en"):
    lang = "zh" if locale == "zh" else "en"
    metrics = metrics or {}
    narrations = {}
    for key in CORE_KEYS:
        if key in metrics:
            label = _LABELS.get(key, {}).get(lang, key)
            value = _fmt(metrics.get(key))
            if lang == "zh":
                narrations[key] = f"{label}为 {value}。"
            else:
                narrations[key] = f"{label} is {value} in this backtest."
    return narrations

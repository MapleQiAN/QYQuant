import json

from .llm_client import call_llm

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


def _is_empty_metrics(metrics):
    """Check if metrics are all-zero placeholder values (no real data)."""
    if not metrics:
        return True
    return all(v == 0 or v == 0.0 for v in metrics.values() if isinstance(v, (int, float)))


def _template_summary(metrics, tier, lang):
    metrics = metrics or {}
    if _is_empty_metrics(metrics):
        if lang == "zh":
            return "回测数据不足，无法生成有效摘要。请确认回测任务已成功完成。"
        return "Insufficient backtest data to generate a summary. Please verify the backtest completed successfully."
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


def generate_summary(metrics, tier, locale="en", user_id=None):
    lang = "zh" if locale == "zh" else "en"

    if user_id is not None:
        lang_name = "Chinese" if lang == "zh" else "English"
        result = call_llm(
            user_id,
            "You are a quantitative trading analyst.",
            (
                f"Given these backtest metrics, write a concise executive summary (2-3 sentences).\n"
                f"Tier: {tier}\n"
                f"Language: {lang_name}\n"
                f"Metrics:\n{json.dumps(metrics or {}, ensure_ascii=False, indent=2)}"
            ),
            temperature=0.3,
            timeout=30,
        )
        if result is not None:
            return result

    return _template_summary(metrics, tier, lang)


def _template_annotations(metrics, lang):
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


def annotate_metrics(metrics, locale="en", user_id=None):
    lang = "zh" if locale == "zh" else "en"

    if user_id is not None:
        lang_name = "Chinese" if lang == "zh" else "English"
        result = call_llm(
            user_id,
            "You are a quantitative trading analyst.",
            (
                f"For each metric, write a one-sentence insight about what this value means for strategy performance.\n"
                f"Respond in JSON: {{\"metricKey\": \"insight sentence\"}}\n"
                f"Language: {lang_name}\n"
                f"Metrics:\n{json.dumps(metrics or {}, ensure_ascii=False, indent=2)}"
            ),
            temperature=0.3,
            timeout=30,
        )
        if result is not None:
            try:
                parsed = json.loads(result)
                if isinstance(parsed, dict) and parsed:
                    return parsed
            except json.JSONDecodeError:
                pass

    return _template_annotations(metrics, lang)

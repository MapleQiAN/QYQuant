import json
import logging

from .llm_client import call_llm

logger = logging.getLogger(__name__)


def _template_suggestions(payload, tier, lang):
    metrics = (payload or {}).get("metrics") or {}
    sharpe = metrics.get("sharpeRatio", 0)
    if lang == "zh":
        return f"{tier} 建议：请审视仓位管理并重新测试参数。夏普比率为 {sharpe}。"
    return f"{tier} advisor: review position sizing and retest parameters. Sharpe is {sharpe}."


def _template_alerts(payload, lang):
    metrics = (payload or {}).get("metrics") or {}
    alerts = []

    max_drawdown = metrics.get("maxDrawdown")
    if isinstance(max_drawdown, (int, float)) and max_drawdown <= -20:
        if lang == "zh":
            alerts.append({"level": "warning", "title": "回撤过大", "message": "最大回撤已超过审查阈值。"})
        else:
            alerts.append({"level": "warning", "title": "Large drawdown", "message": "Maximum drawdown exceeded the review threshold."})

    total_trades = metrics.get("totalTrades")
    if isinstance(total_trades, (int, float)) and total_trades < 5:
        if lang == "zh":
            alerts.append({"level": "info", "title": "交易样本过少", "message": "交易次数较少，结论可能不够稳健。"})
        else:
            alerts.append({"level": "info", "title": "Small trade sample", "message": "Trade count is low, so the conclusion may be fragile."})

    return alerts


def generate_suggestions(payload, tier, locale="en", user_id=None):
    lang = "zh" if locale == "zh" else "en"

    if user_id is not None:
        lang_name = "Chinese" if lang == "zh" else "English"
        result = call_llm(
            user_id,
            "You are a quantitative strategy advisor.",
            (
                f"Given these backtest results, suggest concrete improvements to the strategy. "
                f"Write a concise advice paragraph.\n"
                f"Language: {lang_name}\n"
                f"Data:\n{json.dumps(payload or {}, ensure_ascii=False, indent=2)}"
            ),
            temperature=0.3,
            timeout=30,
        )
        if result is not None:
            return result

    return _template_suggestions(payload, tier, lang)


def generate_alerts(payload, tier, locale="en", user_id=None):
    lang = "zh" if locale == "zh" else "en"

    if user_id is not None:
        lang_name = "Chinese" if lang == "zh" else "English"
        result = call_llm(
            user_id,
            "You are a quantitative risk advisor.",
            (
                f"Given these backtest results, identify any risk alerts.\n"
                f"Respond with a JSON array: "
                f'[{{"level":"warning|info|critical","title":"...","message":"..."}}]\n'
                f"Language: {lang_name}\n"
                f"Data:\n{json.dumps(payload or {}, ensure_ascii=False, indent=2)}"
            ),
            temperature=0.2,
            timeout=30,
        )
        if result is not None:
            try:
                parsed = json.loads(result)
                if isinstance(parsed, list) and all(isinstance(a, dict) for a in parsed):
                    return parsed
            except json.JSONDecodeError:
                logger.debug("advisor: LLM alert response was not valid JSON")

    return _template_alerts(payload, lang)

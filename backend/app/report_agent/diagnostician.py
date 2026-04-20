import json

from .llm_client import call_llm


def _template_diagnosis(payload, tier, lang):
    metrics = (payload or {}).get("metrics") or {}
    max_drawdown = metrics.get("maxDrawdown", 0)
    total_trades = metrics.get("totalTrades", 0)
    if lang == "zh":
        return (
            f"{tier} 诊断：最大回撤为 {max_drawdown}，"
            f"已完成 {total_trades} 笔交易。请在实盘使用前验证策略稳健性。"
        )
    return (
        f"{tier} diagnosis: max drawdown is {max_drawdown}, "
        f"with {total_trades} closed trades. Validate robustness before live use."
    )


def generate_diagnosis(payload, tier, locale="en", user_id=None):
    lang = "zh" if locale == "zh" else "en"

    if user_id is not None:
        lang_name = "Chinese" if lang == "zh" else "English"
        result = call_llm(
            user_id,
            "You are a quantitative risk analyst.",
            (
                f"Given these backtest results, write a diagnosis paragraph covering risk profile, "
                f"robustness concerns, and key warnings.\n"
                f"Tier: {tier}\n"
                f"Language: {lang_name}\n"
                f"Data:\n{json.dumps(payload or {}, ensure_ascii=False, indent=2)}"
            ),
            temperature=0.3,
            timeout=30,
        )
        if result is not None:
            return result

    return _template_diagnosis(payload, tier, lang)

import json

from .llm_client import call_llm
from .tier_filter import normalize_report_plan_level


CHAT_ENABLED_TIERS = {"go", "plus", "pro", "ultra"}


def is_chat_available(plan_level):
    return normalize_report_plan_level(plan_level) in CHAT_ENABLED_TIERS


def _template_response(message, report, lang):
    metrics = report.metrics or {}
    total_return = metrics.get("totalReturn")
    max_drawdown = metrics.get("maxDrawdown")

    if total_return is None and max_drawdown is None:
        if lang == "zh":
            return (
                "报告指标尚未计算完成，暂时无法回答。"
                "请确认回测任务已成功完成，或稍后重试。"
            )
        return (
            "Report metrics are not yet available. "
            "Please verify the backtest completed successfully or try again later."
        )

    total_return = total_return if total_return is not None else "--"
    max_drawdown = max_drawdown if max_drawdown is not None else "--"
    summary = report.executive_summary or (
        "回测已完成。" if lang == "zh" else "Backtest completed."
    )
    if lang == "zh":
        return (
            f"{summary} 针对你的问题「{message}」，"
            f"重点关注总收益率 {total_return} 和最大回撤 {max_drawdown}。"
        )
    return (
        f"{summary} For your question '{message}', focus on total return "
        f"{total_return} and max drawdown {max_drawdown}."
    )


def route_chat_question(message, report, locale="en", user_id=None):
    lang = "zh" if locale == "zh" else "en"

    if user_id is not None:
        lang_name = "Chinese" if lang == "zh" else "English"
        metrics = report.metrics or {}
        summary = report.executive_summary or "N/A"
        diagnosis = report.diagnosis_narration or "N/A"
        advisor = report.advisor_narration or "N/A"

        result = call_llm(
            user_id,
            "You are an AI analyst for a quantitative trading platform.",
            (
                f"The user is asking about their backtest report.\n\n"
                f"Report context:\n"
                f"- Executive summary: {summary}\n"
                f"- Metrics: {json.dumps(metrics, ensure_ascii=False)}\n"
                f"- Diagnosis: {diagnosis}\n"
                f"- Advisor suggestions: {advisor}\n\n"
                f"Answer the user's question clearly and concisely.\n"
                f"Language: {lang_name}\n"
                f"User question: {message}"
            ),
            temperature=0.3,
            timeout=30,
        )
        if result is not None:
            return result

    return _template_response(message, report, lang)

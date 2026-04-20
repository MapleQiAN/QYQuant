from .tier_filter import normalize_report_plan_level


CHAT_ENABLED_TIERS = {"go", "plus", "pro", "ultra"}


def is_chat_available(plan_level):
    return normalize_report_plan_level(plan_level) in CHAT_ENABLED_TIERS


def route_chat_question(message, report, locale="en"):
    lang = "zh" if locale == "zh" else "en"
    metrics = report.metrics or {}
    total_return = metrics.get("totalReturn", "--")
    max_drawdown = metrics.get("maxDrawdown", "--")
    summary = report.executive_summary or (
        "尚未生成执行摘要。" if lang == "zh" else "No executive summary has been generated yet."
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

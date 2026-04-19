from .tier_filter import normalize_report_plan_level


CHAT_ENABLED_TIERS = {"go", "plus", "pro", "ultra"}


def is_chat_available(plan_level):
    return normalize_report_plan_level(plan_level) in CHAT_ENABLED_TIERS


def route_chat_question(message, report):
    metrics = report.metrics or {}
    total_return = metrics.get("totalReturn", "--")
    max_drawdown = metrics.get("maxDrawdown", "--")
    summary = report.executive_summary or "No executive summary has been generated yet."
    return (
        f"{summary} For your question '{message}', focus on total return "
        f"{total_return} and max drawdown {max_drawdown}."
    )

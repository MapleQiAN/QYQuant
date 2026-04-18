from ..quota import normalize_plan_level


CORE_METRIC_KEYS = (
    "totalReturn",
    "annualizedReturn",
    "maxDrawdown",
    "sharpeRatio",
    "volatility",
    "winRate",
    "totalTrades",
)

ADVANCED_METRIC_KEYS = (
    "sortinoRatio",
    "calmarRatio",
    "profitLossRatio",
    "maxConsecutiveLosses",
    "avgHoldingDays",
    "alpha",
    "beta",
)

TIER_CONFIG = {
    "free": {
        "metric_keys": CORE_METRIC_KEYS,
        "include_executive_summary": True,
        "include_metric_narrations": False,
        "include_diagnostics": False,
        "include_advisor": False,
    },
    "go": {
        "metric_keys": CORE_METRIC_KEYS + ADVANCED_METRIC_KEYS,
        "include_executive_summary": True,
        "include_metric_narrations": True,
        "include_diagnostics": False,
        "include_advisor": False,
    },
    "plus": {
        "metric_keys": CORE_METRIC_KEYS + ADVANCED_METRIC_KEYS,
        "include_executive_summary": True,
        "include_metric_narrations": True,
        "include_diagnostics": True,
        "include_advisor": False,
    },
    "pro": {
        "metric_keys": CORE_METRIC_KEYS + ADVANCED_METRIC_KEYS,
        "include_executive_summary": True,
        "include_metric_narrations": True,
        "include_diagnostics": True,
        "include_advisor": True,
    },
    "ultra": {
        "metric_keys": CORE_METRIC_KEYS + ADVANCED_METRIC_KEYS,
        "include_executive_summary": True,
        "include_metric_narrations": True,
        "include_diagnostics": True,
        "include_advisor": True,
    },
}


def normalize_report_plan_level(plan_level):
    normalized = normalize_plan_level(plan_level or "free")
    if normalized == "basic":
        return "free"
    if normalized not in TIER_CONFIG:
        return "free"
    return normalized


def allowed_metric_keys(plan_level):
    normalized = normalize_report_plan_level(plan_level)
    return TIER_CONFIG[normalized]["metric_keys"]


def filter_report_for_tier(report_dict, plan_level):
    report_dict = report_dict or {}
    normalized = normalize_report_plan_level(plan_level)
    config = TIER_CONFIG[normalized]

    filtered = {}

    if isinstance(report_dict.get("metrics"), dict):
        filtered_metrics = {}
        for key in config["metric_keys"]:
            if key in report_dict["metrics"]:
                filtered_metrics[key] = report_dict["metrics"][key]
        filtered["metrics"] = filtered_metrics

    for key in ("equity_curve", "drawdown_series", "monthly_returns", "trade_details"):
        if key in report_dict:
            filtered[key] = report_dict[key]

    if config["include_executive_summary"] and "executive_summary" in report_dict:
        filtered["executive_summary"] = report_dict["executive_summary"]

    if config["include_metric_narrations"] and "metric_narrations" in report_dict:
        filtered["metric_narrations"] = report_dict["metric_narrations"]

    if config["include_diagnostics"]:
        for key in ("anomalies", "parameter_sensitivity", "monte_carlo", "regime_analysis", "diagnosis_narration"):
            if key in report_dict:
                filtered[key] = report_dict[key]

    if config["include_advisor"]:
        if "advisor_narration" in report_dict:
            filtered["advisor_narration"] = report_dict["advisor_narration"]

    return filtered

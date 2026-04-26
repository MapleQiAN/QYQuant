import json
import logging
import os
from dataclasses import dataclass

from . import advisor, diagnostician, narrator

logger = logging.getLogger(__name__)

ENABLED_ENV = "QYQUANT_REPORT_AGENTS_SDK_ENABLED"


@dataclass
class ReportAgentResult:
    executive_summary: str
    metric_narrations: dict | None = None
    diagnosis_narration: str | None = None
    advisor_narration: str | None = None
    alerts: list[dict] | None = None


def is_enabled():
    return os.getenv(ENABLED_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def generate_report_narratives(payload, tier, *, locale="en", user_id=None):
    """Generate report narratives through OpenAI Agents SDK when explicitly enabled.

    The SDK path is deliberately opt-in and wraps the existing report-agent specialists,
    so production can fall back to the known implementation without changing report data.
    """
    if not is_enabled():
        return None

    try:
        from agents import Agent, Runner, function_tool, set_tracing_disabled
    except ImportError:
        logger.warning("OpenAI Agents SDK is enabled but the 'agents' package is not installed")
        return None

    set_tracing_disabled(os.getenv("OPENAI_AGENTS_DISABLE_TRACING", "1") != "0")

    @function_tool
    def write_executive_summary() -> str:
        return narrator.generate_summary(payload["metrics"], tier, locale=locale, user_id=user_id)

    @function_tool
    def annotate_key_metrics() -> str:
        if tier not in {"go", "plus", "pro", "ultra"}:
            return "{}"
        return json.dumps(
            narrator.annotate_metrics(payload["metrics"], locale=locale, user_id=user_id),
            ensure_ascii=False,
        )

    @function_tool
    def diagnose_report() -> str:
        if tier not in {"plus", "pro", "ultra"}:
            return ""
        return diagnostician.generate_diagnosis(payload, tier, locale=locale, user_id=user_id)

    @function_tool
    def suggest_improvements() -> str:
        if tier not in {"pro", "ultra"}:
            return ""
        return advisor.generate_suggestions(payload, tier, locale=locale, user_id=user_id)

    @function_tool
    def identify_alerts() -> str:
        if tier not in {"pro", "ultra"}:
            return "[]"
        return json.dumps(advisor.generate_alerts(payload, tier, locale=locale, user_id=user_id), ensure_ascii=False)

    agent = Agent(
        name="QYQuant Report Manager",
        instructions=(
            "Call the provided tools to produce every narrative section needed for this "
            "backtest report. Return only compact JSON with keys: executive_summary, "
            "metric_narrations, diagnosis_narration, advisor_narration, alerts."
        ),
        tools=[
            write_executive_summary,
            annotate_key_metrics,
            diagnose_report,
            suggest_improvements,
            identify_alerts,
        ],
    )

    prompt = {
        "tier": tier,
        "locale": locale,
        "metrics": payload.get("metrics", {}),
        "anomalies": payload.get("anomalies", []),
    }
    try:
        result = Runner.run_sync(agent, json.dumps(prompt, ensure_ascii=False))
    except Exception:
        logger.warning("OpenAI Agents SDK report generation failed; falling back", exc_info=True)
        return None

    parsed = _parse_agent_output(getattr(result, "final_output", ""))
    if parsed is None:
        return None
    return ReportAgentResult(**parsed)


def _parse_agent_output(output):
    try:
        parsed = json.loads(output)
    except (TypeError, json.JSONDecodeError):
        logger.warning("OpenAI Agents SDK report output was not valid JSON")
        return None

    if not isinstance(parsed, dict) or not parsed.get("executive_summary"):
        logger.warning("OpenAI Agents SDK report output missed executive_summary")
        return None

    metric_narrations = parsed.get("metric_narrations")
    if metric_narrations is None:
        metric_narrations = {}
    if not isinstance(metric_narrations, dict):
        logger.warning("OpenAI Agents SDK metric_narrations was not an object")
        return None

    alerts = parsed.get("alerts")
    if alerts is None:
        alerts = []
    if not isinstance(alerts, list):
        logger.warning("OpenAI Agents SDK alerts was not a list")
        return None

    return {
        "executive_summary": str(parsed["executive_summary"]),
        "metric_narrations": metric_narrations,
        "diagnosis_narration": parsed.get("diagnosis_narration"),
        "advisor_narration": parsed.get("advisor_narration"),
        "alerts": alerts,
    }

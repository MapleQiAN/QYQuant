from ..extensions import db
from ..models import BacktestJob, BacktestJobStatus, BacktestReport, ReportAlert, User
from ..utils.storage import build_backtest_storage_key, read_json
from . import advisor, diagnostician, narrator
from .agents_sdk import generate_report_narratives
from .quant_engine import build_report_payload
from .tier_filter import normalize_report_plan_level


def generate_report(backtest_job_id, user_id, force=False, locale="en"):
    job = db.session.get(BacktestJob, backtest_job_id)
    if job is None:
        raise ValueError(f"backtest job {backtest_job_id} not found")
    if job.status != BacktestJobStatus.COMPLETED.value:
        raise ValueError(f"backtest job {backtest_job_id} is not completed")

    report = BacktestReport.query.filter_by(backtest_job_id=backtest_job_id).one_or_none()
    if report is None:
        report = BacktestReport(
            backtest_job_id=backtest_job_id,
            user_id=user_id,
            status="pending",
        )
        db.session.add(report)
        db.session.flush()
    elif report.status == "ready" and not force:
        return report

    report.user_id = user_id
    report.status = "computing"
    report.failure_reason = None
    db.session.commit()

    try:
        storage_key = job.result_storage_key or build_backtest_storage_key(backtest_job_id)
        bars = read_json(f"{storage_key}/kline.json")
        trades = read_json(f"{storage_key}/trades.json")
        payload = build_report_payload(bars, trades)
        user = db.session.get(User, user_id)
        tier = normalize_report_plan_level(getattr(user, "plan_level", "free"))

        report.status = "narrating"
        report.metrics = payload["metrics"]
        report.equity_curve = payload["equity_curve"]
        report.drawdown_series = payload["drawdown_series"]
        report.monthly_returns = payload["monthly_returns"]
        report.trade_details = payload["trade_details"]
        report.anomalies = payload["anomalies"]
        report.parameter_sensitivity = payload["parameter_sensitivity"]
        report.monte_carlo = payload["monte_carlo"]
        report.regime_analysis = payload["regime_analysis"]
        report.metric_narrations = payload["metric_narrations"]
        agent_result = generate_report_narratives(payload, tier, locale=locale, user_id=user_id)
        if agent_result is not None:
            report.executive_summary = agent_result.executive_summary
            if tier in {"go", "plus", "pro", "ultra"}:
                report.metric_narrations = agent_result.metric_narrations or {}
            report.diagnosis_narration = agent_result.diagnosis_narration if tier in {"plus", "pro", "ultra"} else None
            report.advisor_narration = agent_result.advisor_narration if tier in {"pro", "ultra"} else None
            alert_specs = agent_result.alerts or []
        else:
            report.executive_summary = narrator.generate_summary(payload["metrics"], tier, locale=locale, user_id=user_id)
            if tier in {"go", "plus", "pro", "ultra"}:
                report.metric_narrations = narrator.annotate_metrics(payload["metrics"], locale=locale, user_id=user_id)
            if tier in {"plus", "pro", "ultra"}:
                report.diagnosis_narration = diagnostician.generate_diagnosis(payload, tier, locale=locale, user_id=user_id)
            else:
                report.diagnosis_narration = None
            if tier in {"pro", "ultra"}:
                report.advisor_narration = advisor.generate_suggestions(payload, tier, locale=locale, user_id=user_id)
                alert_specs = advisor.generate_alerts(payload, tier, locale=locale, user_id=user_id)
            else:
                report.advisor_narration = None
                alert_specs = []

        if tier in {"pro", "ultra"}:
            report.anomalies = alert_specs
            ReportAlert.query.filter_by(report_id=report.id).delete()
            for alert in alert_specs:
                db.session.add(
                    ReportAlert(
                        report_id=report.id,
                        user_id=user_id,
                        level=alert.get("level", "info"),
                        title=alert.get("title", "Report alert"),
                        message=alert.get("message", ""),
                        alert_metadata=alert.get("metadata", {}),
                    )
                )
        else:
            report.advisor_narration = None
        report.status = "ready"
        db.session.commit()
    except Exception as exc:
        report.status = "failed"
        report.failure_reason = str(exc)
        db.session.commit()
        raise

    return report

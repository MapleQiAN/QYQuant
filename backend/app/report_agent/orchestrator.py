from ..extensions import db
from ..models import BacktestJob, BacktestJobStatus, BacktestReport, User
from ..utils.storage import build_backtest_storage_key, read_json
from .quant_engine import build_report_payload


def generate_report(backtest_job_id, user_id, force=False):
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
        report.status = "ready"
        db.session.commit()
    except Exception as exc:
        report.status = "failed"
        report.failure_reason = str(exc)
        db.session.commit()
        raise

    return report

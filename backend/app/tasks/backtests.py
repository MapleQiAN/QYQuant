import json

from celery.exceptions import SoftTimeLimitExceeded
from flask import has_app_context

from ..backtest.engine import run_backtest
from ..celery_app import celery_app
from ..extensions import db
from ..models import BacktestJob, BacktestJobStatus
from ..quota import consume_backtest_quota, release_backtest_quota, reserve_backtest_quota
from ..services.error_parser import dump_execution_error
from ..services.metrics import build_backtest_report
from ..strategy_runtime import StrategyRuntimeError
from ..utils.storage import build_backtest_storage_key, write_json
from ..utils.time import now_utc


def _store_structured_error(job, raw_error):
    payload = dump_execution_error(raw_error)
    job.error_message = payload
    return json.loads(payload)


def _run_job(job_id):
    job = db.session.get(BacktestJob, job_id)
    if job is None:
        return {"status": "missing"}

    params = dict(job.params or {})
    if job.user_id and not reserve_backtest_quota(job.user_id, job.id):
        job.status = BacktestJobStatus.FAILED.value
        job.completed_at = now_utc()
        job.error_message = "quota_exceeded"
        db.session.commit()
        return {"status": job.status}

    job.status = BacktestJobStatus.RUNNING.value
    job.started_at = now_utc()
    job.completed_at = None
    job.error_message = None
    db.session.commit()

    try:
        result = run_backtest(
            params.get('symbol'),
            interval=params.get('interval'),
            limit=params.get('limit') if params.get('start_time') is None else None,
            start_time=params.get('start_time'),
            end_time=params.get('end_time'),
            strategy_id=params.get('strategy_id'),
            strategy_version=params.get('strategy_version'),
            strategy_params=params.get('strategy_params'),
            data_source=params.get('data_source'),
            user_id=job.user_id,
        )
    except SoftTimeLimitExceeded:
        job.status = BacktestJobStatus.TIMEOUT.value
        job.error_message = 'soft_time_limit_exceeded'
        job.completed_at = now_utc()
        release_backtest_quota(job.id)
        db.session.commit()
        return {"status": job.status}
    except StrategyRuntimeError as exc:
        if exc.message == 'strategy_timeout':
            job.status = BacktestJobStatus.TIMEOUT.value
            job.error_message = exc.message
        else:
            job.status = BacktestJobStatus.FAILED.value
            raw_error = (exc.details or {}).get("reason") or exc.message
            _store_structured_error(job, raw_error)
        job.completed_at = now_utc()
        release_backtest_quota(job.id)
        db.session.commit()
        return {"status": job.status}
    except Exception as exc:
        job.status = BacktestJobStatus.FAILED.value
        _store_structured_error(job, str(exc))
        job.completed_at = now_utc()
        release_backtest_quota(job.id)
        db.session.commit()
        return {"status": job.status}

    try:
        if result.get('kline') or result.get('trades'):
            report = build_backtest_report(result.get('kline') or [], result.get('trades') or [])
        else:
            report = {
                "result_summary": result.get('summary') or {},
                "equity_curve": [],
                "trades": result.get('trades') or [],
            }
        storage_key = build_backtest_storage_key(job.id)
        write_json(f"{storage_key}/equity_curve.json", report["equity_curve"])
        write_json(f"{storage_key}/trades.json", report["trades"])
        write_json(f"{storage_key}/kline.json", result.get('kline') or [])
    except Exception as exc:
        job.status = BacktestJobStatus.FAILED.value
        _store_structured_error(job, str(exc))
        job.completed_at = now_utc()
        release_backtest_quota(job.id)
        db.session.commit()
        return {"status": job.status}

    consume_backtest_quota(job.id)
    job.status = BacktestJobStatus.COMPLETED.value
    job.result_storage_key = storage_key
    job.result_summary = report["result_summary"]
    job.completed_at = now_utc()
    db.session.commit()

    if job.user_id and params.get("enable_ai", True):
        from .report_generation import generate_backtest_report

        generate_backtest_report.delay(job.id, job.user_id, locale=params.get("locale", "en"))

    result["summary"] = report["result_summary"]
    result["equity_curve"] = report["equity_curve"]
    result["trades"] = report["trades"]
    return result


@celery_app.task(bind=True, name='app.tasks.backtests.run_backtest_task')
def run_backtest_task(self, job_id):
    if has_app_context():
        return _run_job(job_id)

    from .. import create_app

    app = create_app()
    with app.app_context():
        return _run_job(job_id)

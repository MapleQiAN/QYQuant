from celery.exceptions import SoftTimeLimitExceeded
from flask import has_app_context

from ..backtest.engine import run_backtest
from ..celery_app import celery_app
from ..extensions import db
from ..models import BacktestJob, BacktestJobStatus
from ..utils.time import now_utc


def _run_job(job_id):
    job = db.session.get(BacktestJob, job_id)
    if job is None:
        return {"status": "missing"}

    params = dict(job.params or {})
    job.status = BacktestJobStatus.RUNNING.value
    job.started_at = now_utc()
    job.completed_at = None
    job.error_message = None
    db.session.commit()

    try:
        result = run_backtest(
            params.get('symbol'),
            interval=params.get('interval'),
            limit=params.get('limit', 120),
            start_time=params.get('start_time'),
            end_time=params.get('end_time'),
            strategy_id=params.get('strategy_id'),
            strategy_version=params.get('strategy_version'),
            strategy_params=params.get('strategy_params'),
            data_source=params.get('data_source'),
        )
    except SoftTimeLimitExceeded:
        job.status = BacktestJobStatus.TIMEOUT.value
        job.error_message = 'soft_time_limit_exceeded'
        job.completed_at = now_utc()
        db.session.commit()
        return {"status": job.status}
    except Exception as exc:
        job.status = BacktestJobStatus.FAILED.value
        job.error_message = str(exc)
        job.completed_at = now_utc()
        db.session.commit()
        return {"status": job.status}

    job.status = BacktestJobStatus.COMPLETED.value
    job.result_summary = result.get('summary')
    job.completed_at = now_utc()
    db.session.commit()
    return result


@celery_app.task(bind=True, name='app.tasks.backtests.run_backtest_task')
def run_backtest_task(self, job_id):
    if has_app_context():
        return _run_job(job_id)

    from .. import create_app

    app = create_app()
    with app.app_context():
        return _run_job(job_id)

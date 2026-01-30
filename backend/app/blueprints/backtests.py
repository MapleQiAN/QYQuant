from celery.result import AsyncResult
from flask import request
from flask_smorest import Blueprint

from ..celery_app import celery_app
from ..tasks.backtests import run_backtest_task
from ..utils.response import ok

bp = Blueprint('backtests', __name__, url_prefix='/api/backtests')


@bp.post('/run')
def run():
    payload = request.get_json() or {}
    job = run_backtest_task.delay(payload.get('symbol', 'BTCUSDT'))
    return ok({"job_id": job.id})


@bp.get('/job/<job_id>')
def job(job_id):
    result = AsyncResult(job_id, app=celery_app)
    status = result.status
    data = {"status": status}
    if status == 'SUCCESS':
        data['result'] = result.result
    return ok(data)


@bp.get('/latest')
def latest():
    return ok({"summary": {}, "kline": [], "trades": []})

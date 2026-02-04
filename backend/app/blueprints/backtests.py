from celery.result import AsyncResult
from flask import request
from flask_smorest import Blueprint

from ..backtest.engine import run_backtest
from ..celery_app import celery_app
from ..tasks.backtests import run_backtest_task
from ..utils.response import ok

bp = Blueprint('backtests', __name__, url_prefix='/api/backtests')


@bp.post('/run')
def run():
    payload = request.get_json() or {}
    symbol = payload.get('symbol', 'BTCUSDT')
    interval = payload.get('interval')
    limit = payload.get('limit', 120)
    start_time = payload.get('startTime', payload.get('start_time'))
    end_time = payload.get('endTime', payload.get('end_time'))

    try:
        limit = int(limit) if limit is not None else 120
    except (TypeError, ValueError):
        limit = 120

    job = run_backtest_task.delay(symbol, interval, limit, start_time, end_time)
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
    symbol = request.args.get('symbol', 'BTCUSDT')
    interval = request.args.get('interval')
    limit = request.args.get('limit', 120)
    start_time = request.args.get('startTime', request.args.get('start_time'))
    end_time = request.args.get('endTime', request.args.get('end_time'))

    try:
        limit = int(limit) if limit is not None else 120
    except (TypeError, ValueError):
        limit = 120

    result = run_backtest(
        symbol,
        interval=interval,
        limit=limit,
        start_time=start_time,
        end_time=end_time,
    )
    return ok(result)

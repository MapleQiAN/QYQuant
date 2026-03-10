from celery.result import AsyncResult
from flask import request
from flask_smorest import Blueprint

from ..backtest.engine import run_backtest
from ..celery_app import celery_app
from ..strategy_runtime import StrategyRuntimeError, as_response, preflight_strategy
from ..tasks.backtests import run_backtest_task
from ..utils.response import ok

bp = Blueprint('backtests', __name__, url_prefix='/api/backtests')


@bp.post('/run')
def run():
    payload = request.get_json() or {}
    symbol = payload.get('symbol', 'BTCUSDT')
    interval = payload.get('interval')
    data_source = payload.get('dataSource', payload.get('data_source', payload.get('provider')))
    limit = payload.get('limit', 120)
    start_time = payload.get('startTime', payload.get('start_time'))
    end_time = payload.get('endTime', payload.get('end_time'))
    strategy_id = payload.get('strategyId', payload.get('strategy_id'))
    strategy_version = payload.get('strategyVersion', payload.get('strategy_version'))
    strategy_params = payload.get('strategyParams', payload.get('strategy_params'))

    try:
        limit = int(limit) if limit is not None else 120
    except (TypeError, ValueError):
        limit = 120

    if strategy_id:
        try:
            preflight_strategy(strategy_id, strategy_version, strategy_params)
        except StrategyRuntimeError as exc:
            return as_response(exc), 400

    job = run_backtest_task.delay(
        symbol,
        interval,
        limit,
        start_time,
        end_time,
        strategy_id,
        strategy_version,
        strategy_params,
        data_source,
    )
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
    import json

    symbol = request.args.get('symbol', 'BTCUSDT')
    interval = request.args.get('interval')
    data_source = request.args.get('dataSource', request.args.get('data_source', request.args.get('provider')))
    limit = request.args.get('limit', 120)
    start_time = request.args.get('startTime', request.args.get('start_time'))
    end_time = request.args.get('endTime', request.args.get('end_time'))
    strategy_id = request.args.get('strategyId', request.args.get('strategy_id'))
    strategy_version = request.args.get('strategyVersion', request.args.get('strategy_version'))
    strategy_params = request.args.get('strategyParams', request.args.get('strategy_params'))

    try:
        limit = int(limit) if limit is not None else 120
    except (TypeError, ValueError):
        limit = 120

    if strategy_params:
        try:
            strategy_params = json.loads(strategy_params)
        except (TypeError, ValueError, json.JSONDecodeError):
            return {"code": 40000, "message": "invalid_strategy_params", "details": None}, 400

    try:
        result = run_backtest(
            symbol,
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            strategy_params=strategy_params,
            data_source=data_source,
        )
    except StrategyRuntimeError as exc:
        return as_response(exc), 400
    return ok(result)

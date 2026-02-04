from ..backtest.engine import run_backtest
from ..celery_app import celery_app


@celery_app.task
def run_backtest_task(symbol, interval=None, limit=120, start_time=None, end_time=None):
    return run_backtest(
        symbol,
        interval=interval,
        limit=limit,
        start_time=start_time,
        end_time=end_time,
    )

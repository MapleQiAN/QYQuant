from ..backtest.engine import run_backtest
from ..celery_app import celery_app


@celery_app.task
def run_backtest_task(symbol):
    return run_backtest(symbol)

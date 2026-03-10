from ..backtest.engine import run_backtest
from ..celery_app import celery_app


@celery_app.task
def run_backtest_task(
    symbol,
    interval=None,
    limit=120,
    start_time=None,
    end_time=None,
    strategy_id=None,
    strategy_version=None,
    strategy_params=None,
    data_source=None,
):
    return run_backtest(
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

from ..services import sandbox as sandbox_service
from .loader import load_strategy_package
from .params import validate_and_merge_params
from .sandbox import guard_strategy_source


def preflight_strategy(strategy_id, strategy_version, strategy_params, user_id=None):
    loaded = load_strategy_package(strategy_id, strategy_version, user_id=user_id)
    params = validate_and_merge_params((loaded.get('manifest') or {}).get('parameters'), strategy_params)
    guard_strategy_source(loaded.get('source') or '')
    return loaded, params


def execute_backtest_strategy(symbol, bars, loaded_strategy, params, timeout_seconds=300):
    outcome = sandbox_service.execute_strategy(
        code=loaded_strategy['source'],
        market_data={"symbol": symbol, "bars": bars},
        params=params,
        metadata={
            "callable_name": loaded_strategy['entrypoint_callable'],
            "strategy_id": loaded_strategy['strategy_id'],
            "strategy_version": loaded_strategy['version'],
            "symbol": symbol,
            "timeout_seconds": timeout_seconds,
        },
    )
    return {
        "trades": outcome.get('trades') or [],
        "runtime": {
            "strategyId": loaded_strategy['strategy_id'],
            "strategyVersion": loaded_strategy['version'],
            "params": params,
            "logs": outcome.get('logs') or [],
        },
    }

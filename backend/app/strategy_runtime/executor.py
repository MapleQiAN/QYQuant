from .loader import load_strategy_package
from .params import validate_and_merge_params
from .sandbox import guard_strategy_source, run_strategy_in_subprocess


def preflight_strategy(strategy_id, strategy_version, strategy_params):
    loaded = load_strategy_package(strategy_id, strategy_version)
    params = validate_and_merge_params((loaded.get('manifest') or {}).get('parameters'), strategy_params)
    guard_strategy_source(loaded.get('source') or '')
    return loaded, params


def execute_backtest_strategy(symbol, bars, loaded_strategy, params, timeout_seconds=10):
    outcome = run_strategy_in_subprocess(
        symbol=symbol,
        source=loaded_strategy['source'],
        callable_name=loaded_strategy['entrypoint_callable'],
        bars=bars,
        params=params,
        timeout_seconds=timeout_seconds,
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


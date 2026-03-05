import ast
import builtins
import multiprocessing
import traceback

from .errors import StrategyRuntimeError
from .events import StrategyContext

FORBIDDEN_IMPORTS = {
    'os',
    'sys',
    'subprocess',
    'socket',
    'ctypes',
    'importlib',
    'pathlib',
    'shutil',
    'multiprocessing',
}

FORBIDDEN_BUILTINS = {
    'eval',
    'exec',
    'compile',
    'open',
    'input',
    '__import__',
    'globals',
    'locals',
    'vars',
}


def guard_strategy_source(source):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        raise StrategyRuntimeError('strategy_load_error', {"reason": "syntax_error"})

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                root = (item.name or '').split('.')[0]
                if root in FORBIDDEN_IMPORTS:
                    raise StrategyRuntimeError('sandbox_rejected', {"reason": f"forbidden_import:{root}"})
        if isinstance(node, ast.ImportFrom):
            root = (node.module or '').split('.')[0]
            if root in FORBIDDEN_IMPORTS:
                raise StrategyRuntimeError('sandbox_rejected', {"reason": f"forbidden_import:{root}"})
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_BUILTINS:
                raise StrategyRuntimeError('sandbox_rejected', {"reason": f"forbidden_builtin:{node.func.id}"})


def _build_safe_builtins():
    allowed = {
        '__build_class__',
        'abs',
        'all',
        'any',
        'bool',
        'dict',
        'enumerate',
        'float',
        'int',
        'len',
        'list',
        'max',
        'min',
        'pow',
        'print',
        'range',
        'round',
        'set',
        'str',
        'sum',
        'tuple',
        'zip',
        'Exception',
    }
    return {name: getattr(builtins, name) for name in allowed}


def _invoke_optional(strategy, name, *args):
    handler = getattr(strategy, name, None)
    if callable(handler):
        return handler(*args)
    return None


def _create_strategy(target, ctx):
    if isinstance(target, type):
        try:
            return target(ctx)
        except TypeError:
            return target()
    if callable(target):
        class _FunctionAdapter:
            def __init__(self, func):
                self._func = func

            def on_bar(self, context, bar):
                return self._func(context, bar)

        return _FunctionAdapter(target)
    raise ValueError('entrypoint_not_callable')


def _worker(payload, queue):
    strategy = None
    try:
        safe_builtins = _build_safe_builtins()
        namespace = {'__builtins__': safe_builtins, '__name__': '__strategy__'}
        exec(payload['source'], namespace, namespace)

        target = namespace.get(payload['callable_name'])
        if target is None:
            raise ValueError('entrypoint_not_found')

        ctx = StrategyContext(payload['symbol'], payload.get('params') or {})
        strategy = _create_strategy(target, ctx)
        trades = []

        _invoke_optional(strategy, 'on_init', ctx)

        bars = payload.get('bars') or []
        for index, bar in enumerate(bars):
            _invoke_optional(strategy, 'on_bar', ctx, bar)

            orders = ctx.consume_orders()
            for order in orders:
                order_event = dict(order)
                order_event['index'] = index
                _invoke_optional(strategy, 'on_order', ctx, order_event)

                trade = {
                    "symbol": order_event['symbol'],
                    "side": order_event['side'],
                    "price": order_event['price'],
                    "quantity": order_event['quantity'],
                    "timestamp": bar.get('time'),
                    "pnl": None,
                }
                trades.append(trade)
                _invoke_optional(strategy, 'on_trade', ctx, trade)

            _invoke_optional(strategy, 'on_risk', ctx, {"index": index, "tradeCount": len(trades)})
            _invoke_optional(strategy, 'on_timer', ctx, {"index": index, "time": bar.get('time')})

        _invoke_optional(strategy, 'on_finish', ctx, {"tradeCount": len(trades)})
        queue.put({"ok": True, "trades": trades, "logs": ctx.logs})
    except Exception as exc:
        if strategy is not None:
            try:
                _invoke_optional(strategy, 'on_error', None, {"error": str(exc)})
            except Exception:
                pass
        queue.put({
            "ok": False,
            "error_code": 'strategy_runtime_error',
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })


def run_strategy_in_subprocess(symbol, source, callable_name, bars, params, timeout_seconds=10):
    guard_strategy_source(source)

    queue = multiprocessing.Queue()
    process = multiprocessing.Process(
        target=_worker,
        args=({
            "symbol": symbol,
            "source": source,
            "callable_name": callable_name,
            "bars": bars,
            "params": params,
        }, queue),
    )
    process.start()
    process.join(timeout_seconds)

    if process.is_alive():
        process.terminate()
        process.join()
        raise StrategyRuntimeError('strategy_timeout')

    if queue.empty():
        raise StrategyRuntimeError('strategy_runtime_error', {"reason": "no_result"})

    result = queue.get()
    if not result.get('ok'):
        raise StrategyRuntimeError(result.get('error_code') or 'strategy_runtime_error', {
            "reason": result.get('error'),
        })

    return result


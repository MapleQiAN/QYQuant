import ast
import builtins
import multiprocessing
import traceback

from .errors import StrategyRuntimeError
from .events import StrategyContext, make_bar, normalize_order, resolve_fill_price

FORBIDDEN_IMPORTS = {
    'os',
    'sys',
    'subprocess',
    'socket',
    'ctypes',
    'requests',
    'urllib',
    'http',
    'ftplib',
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

_REAL_IMPORT = builtins.__import__


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


def _restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    root = (name or '').split('.')[0]
    if root in FORBIDDEN_IMPORTS:
        raise ImportError(f'forbidden_import:{root}')
    return _REAL_IMPORT(name, globals, locals, fromlist, level)


def _build_safe_builtins():
    allowed = {
        '__build_class__',
        'abs',
        'all',
        'any',
        'bool',
        'callable',
        'dict',
        'enumerate',
        'float',
        'getattr',
        'hasattr',
        'int',
        'isinstance',
        'len',
        'list',
        'max',
        'min',
        'pow',
        'print',
        'range',
        'round',
        'set',
        'setattr',
        'str',
        'sum',
        'tuple',
        'zip',
        'Exception',
    }
    safe = {name: getattr(builtins, name) for name in allowed}
    safe['__import__'] = _restricted_import
    return safe


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
    queue.put(_execute_payload(payload))


def _collect_orders(ctx, returned_orders):
    normalized_orders = []

    if isinstance(returned_orders, (list, tuple)):
        for item in returned_orders:
            normalized = normalize_order(item, default_symbol=ctx.symbol)
            if normalized is not None:
                normalized_orders.append(normalized)

    normalized_orders.extend(ctx.consume_orders())
    return normalized_orders


def _execute_payload(payload):
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
        for index, raw_bar in enumerate(bars):
            bar = make_bar(payload['symbol'], raw_bar)
            ctx.sync_bar(bar)
            returned_orders = _invoke_optional(strategy, 'on_bar', ctx, bar)

            orders = _collect_orders(ctx, returned_orders)
            for order in orders:
                order_event = dict(order)
                order_event['price'] = resolve_fill_price(order_event, bar)
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
                ctx.apply_trade(trade)
                trades.append(trade)
                _invoke_optional(strategy, 'on_trade', ctx, trade)

            _invoke_optional(strategy, 'on_risk', ctx, {"index": index, "tradeCount": len(trades)})
            _invoke_optional(strategy, 'on_timer', ctx, {"index": index, "time": bar.get('time')})

        _invoke_optional(strategy, 'on_finish', ctx, {"tradeCount": len(trades)})
        return {"ok": True, "trades": trades, "logs": ctx.logs}
    except Exception as exc:
        if strategy is not None:
            try:
                _invoke_optional(strategy, 'on_error', None, {"error": str(exc)})
            except Exception:
                pass
        return {
            "ok": False,
            "error_code": 'strategy_runtime_error',
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }


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


def run_strategy_inline(symbol, source, callable_name, bars, params):
    guard_strategy_source(source)

    result = _execute_payload({
        "symbol": symbol,
        "source": source,
        "callable_name": callable_name,
        "bars": bars,
        "params": params,
    })
    if not result.get('ok'):
        raise StrategyRuntimeError(result.get('error_code') or 'strategy_runtime_error', {
            "reason": result.get('error'),
        })

    return result


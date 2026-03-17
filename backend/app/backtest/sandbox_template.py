import json


RESULT_PREFIX = "__QYQUANT_RESULT__="


def build_sandbox_script(code, market_data, params, metadata=None):
    payload = {
        "code": code,
        "market_data": market_data,
        "params": params,
        "metadata": metadata or {},
    }
    payload_json = json.dumps(payload, ensure_ascii=False)
    return f"""
import ast
import builtins
import json
import traceback

RESULT_PREFIX = {RESULT_PREFIX!r}
PAYLOAD = json.loads({payload_json!r})

FORBIDDEN_IMPORTS = {{
    'ctypes',
    'ftplib',
    'http',
    'importlib',
    'multiprocessing',
    'os',
    'pathlib',
    'requests',
    'shutil',
    'socket',
    'subprocess',
    'sys',
    'urllib',
}}

FORBIDDEN_BUILTINS = {{
    'compile',
    'eval',
    'exec',
    'globals',
    'input',
    'locals',
    'open',
    'vars',
}}

_REAL_IMPORT = builtins.__import__


def _restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    root = (name or '').split('.')[0]
    if root in FORBIDDEN_IMPORTS:
        raise ImportError(f'forbidden_import:{{root}}')
    return _REAL_IMPORT(name, globals, locals, fromlist, level)


def _build_safe_builtins():
    allowed = {{
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
    }}
    safe = {{name: getattr(builtins, name) for name in allowed}}
    safe['__import__'] = _restricted_import
    return safe


def _guard_strategy_source(source):
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                root = (item.name or '').split('.')[0]
                if root in FORBIDDEN_IMPORTS:
                    raise ImportError(f'forbidden_import:{{root}}')
        if isinstance(node, ast.ImportFrom):
            root = (node.module or '').split('.')[0]
            if root in FORBIDDEN_IMPORTS:
                raise ImportError(f'forbidden_import:{{root}}')
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_BUILTINS:
                raise PermissionError(f'forbidden_builtin:{{node.func.id}}')


class StrategyContext:
    def __init__(self, symbol, params):
        self.symbol = symbol
        self.params = dict(params or {{}})
        self.orders = []
        self.logs = []

    def emit_order(self, order):
        if not isinstance(order, dict):
            return
        side = (order.get('side') or '').lower()
        if side not in {{'buy', 'sell'}}:
            return
        try:
            price = float(order.get('price'))
            quantity = float(order.get('quantity', 1))
        except (TypeError, ValueError):
            return
        if quantity <= 0:
            return
        self.orders.append({{
            'symbol': order.get('symbol') or self.symbol,
            'side': side,
            'price': price,
            'quantity': quantity,
        }})

    def consume_orders(self):
        orders = list(self.orders)
        self.orders = []
        return orders

    def log(self, message):
        self.logs.append(str(message)[:500])


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


def _run():
    source = PAYLOAD['code']
    metadata = PAYLOAD.get('metadata') or {{}}
    bars = (PAYLOAD.get('market_data') or {{}}).get('bars') or []
    params = PAYLOAD.get('params') or {{}}
    symbol = (PAYLOAD.get('market_data') or {{}}).get('symbol') or metadata.get('symbol')
    callable_name = metadata.get('callable_name')

    _guard_strategy_source(source)
    namespace = {{'__builtins__': _build_safe_builtins(), '__name__': '__strategy__'}}
    exec(source, namespace, namespace)
    target = namespace.get(callable_name)
    if target is None:
        raise ValueError('entrypoint_not_found')

    ctx = StrategyContext(symbol, params)
    strategy = _create_strategy(target, ctx)
    trades = []

    _invoke_optional(strategy, 'on_init', ctx)

    for index, bar in enumerate(bars):
        _invoke_optional(strategy, 'on_bar', ctx, bar)
        orders = ctx.consume_orders()
        for order in orders:
            trade = {{
                'symbol': order['symbol'],
                'side': order['side'],
                'price': order['price'],
                'quantity': order['quantity'],
                'timestamp': bar.get('time'),
                'pnl': None,
            }}
            trades.append(trade)
            _invoke_optional(strategy, 'on_trade', ctx, trade)
        _invoke_optional(strategy, 'on_timer', ctx, {{'index': index, 'time': bar.get('time')}})

    _invoke_optional(strategy, 'on_finish', ctx, {{'tradeCount': len(trades)}})
    return {{'trades': trades, 'logs': ctx.logs}}


try:
    result = _run()
    print(RESULT_PREFIX + json.dumps({{'ok': True, 'result': result}}, ensure_ascii=False))
except Exception as exc:
    print(
        RESULT_PREFIX + json.dumps(
            {{
                'ok': False,
                'error': str(exc),
                'traceback': traceback.format_exc(),
            }},
            ensure_ascii=False,
        )
    )
"""

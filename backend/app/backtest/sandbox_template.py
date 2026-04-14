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
from datetime import datetime, timezone

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
    def __init__(self, symbol, params, initial_cash=100000.0):
        self.symbol = symbol
        self.params = dict(params or {{}})
        self.parameters = ParameterAccessor(self.params)
        self.orders = []
        self.logs = []
        self.account = Account(float(initial_cash))
        self.current_dt = None
        self._latest_bar = None

    def sync_bar(self, bar):
        self._latest_bar = bar
        self.symbol = bar.symbol or self.symbol
        self.current_dt = bar.datetime
        position = self.account.positions.get(self.symbol)
        if position is not None:
            position.current_price = float(bar.close)

    def emit_order(self, order):
        normalized = normalize_order(order, self.symbol)
        if normalized is None:
            return
        self.orders.append(normalized)

    def consume_orders(self):
        orders = list(self.orders)
        self.orders = []
        return orders

    def log(self, message):
        self.logs.append(str(message)[:500])

    def buy(self, symbol, quantity, order_type='market', limit_price=None):
        return Order(symbol, 'buy', quantity, order_type, limit_price)

    def sell(self, symbol, quantity, order_type='market', limit_price=None):
        return Order(symbol, 'sell', quantity, order_type, limit_price)

    def apply_trade(self, trade):
        symbol = trade['symbol']
        price = float(trade['price'])
        quantity = float(trade['quantity'])
        position = self.account.positions.get(symbol)

        if trade['side'] == 'buy':
            current_quantity = position.quantity if position is not None else 0.0
            current_cost = position.avg_cost * current_quantity if position is not None else 0.0
            new_quantity = current_quantity + quantity
            avg_cost = (current_cost + price * quantity) / new_quantity if new_quantity > 0 else price
            self.account.positions[symbol] = Position(symbol, new_quantity, avg_cost, price)
            self.account.cash -= price * quantity
            return

        self.account.cash += price * quantity
        if position is None:
            return

        remaining_quantity = position.quantity - quantity
        if remaining_quantity > 0:
            self.account.positions[symbol] = Position(symbol, remaining_quantity, position.avg_cost, price)
            return

        self.account.positions.pop(symbol, None)


class ParameterAccessor:
    def __init__(self, data=None):
        self._data = dict(data or {{}})

    def get(self, key, default=None):
        return self._data.get(key, default)


class Position:
    def __init__(self, symbol, quantity, avg_cost, current_price):
        self.symbol = symbol
        self.quantity = float(quantity)
        self.avg_cost = float(avg_cost)
        self.current_price = float(current_price)


class Account:
    def __init__(self, cash):
        self.cash = float(cash)
        self.positions = {{}}


class Order:
    def __init__(self, symbol, side, quantity, order_type='market', limit_price=None):
        self.symbol = symbol
        self.side = side
        self.quantity = float(quantity)
        self.order_type = order_type
        self.limit_price = limit_price


class BarData:
    def __init__(self, symbol, open, high, low, close, volume, datetime, time=None):
        self.symbol = symbol
        self.open = float(open)
        self.high = float(high)
        self.low = float(low)
        self.close = float(close)
        self.volume = int(volume)
        self.datetime = datetime
        self.time = time

    def get(self, key, default=None):
        if key == 'time':
            return self.time if self.time is not None else default
        return getattr(self, key, default)


def normalize_order(order, default_symbol):
    if order is None:
        return None

    if isinstance(order, dict):
        side = str(order.get('side') or '').lower()
        if side not in {{'buy', 'sell'}}:
            return None
        try:
            quantity = float(order.get('quantity', 1))
        except (TypeError, ValueError):
            return None
        if quantity <= 0:
            return None
        try:
            price = float(order['price']) if order.get('price') is not None else None
        except (TypeError, ValueError):
            price = None
        try:
            limit_price = float(order['limit_price']) if order.get('limit_price') is not None else None
        except (TypeError, ValueError):
            limit_price = None
        return {{
            'symbol': order.get('symbol') or default_symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'limit_price': limit_price,
            'order_type': str(order.get('order_type', 'market')).lower(),
        }}

    side = getattr(order, 'side', '')
    side = getattr(side, 'value', side)
    side = str(side or '').lower()
    if side not in {{'buy', 'sell'}}:
        return None

    try:
        quantity = float(getattr(order, 'quantity', 0))
    except (TypeError, ValueError):
        return None
    if quantity <= 0:
        return None

    limit_price = getattr(order, 'limit_price', None)
    try:
        limit_price = float(limit_price) if limit_price is not None else None
    except (TypeError, ValueError):
        limit_price = None

    order_type = getattr(order, 'order_type', 'market')
    order_type = getattr(order_type, 'value', order_type)

    return {{
        'symbol': getattr(order, 'symbol', None) or default_symbol,
        'side': side,
        'quantity': quantity,
        'price': None,
        'limit_price': limit_price,
        'order_type': str(order_type or 'market').lower(),
    }}


def make_bar(symbol, raw_bar):
    raw_time = raw_bar.get('time', raw_bar.get('datetime'))
    dt = _coerce_datetime(raw_time)
    return BarData(
        symbol=raw_bar.get('symbol') or symbol,
        open=raw_bar.get('open', 0.0),
        high=raw_bar.get('high', 0.0),
        low=raw_bar.get('low', 0.0),
        close=raw_bar.get('close', 0.0),
        volume=raw_bar.get('volume', 0),
        datetime=dt,
        time=int(raw_time) if raw_time is not None else None,
    )


def resolve_fill_price(order, bar):
    if order.get('price') is not None:
        return float(order['price'])
    if order.get('order_type') == 'limit' and order.get('limit_price') is not None:
        return float(order['limit_price'])
    return float(bar.close)


def collect_orders(ctx, returned_orders):
    normalized = []
    if isinstance(returned_orders, (list, tuple)):
        for item in returned_orders:
            order = normalize_order(item, ctx.symbol)
            if order is not None:
                normalized.append(order)
    normalized.extend(ctx.consume_orders())
    return normalized


def _coerce_datetime(value):
    if isinstance(value, datetime):
        return value
    if value is None:
        return datetime.now(timezone.utc)
    timestamp = float(value)
    if abs(timestamp) >= 10_000_000_000:
        timestamp /= 1000.0
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


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
        bar = make_bar(symbol, bar)
        ctx.sync_bar(bar)
        returned_orders = _invoke_optional(strategy, 'on_bar', ctx, bar)
        orders = collect_orders(ctx, returned_orders)
        for order in orders:
            order['price'] = resolve_fill_price(order, bar)
            trade = {{
                'symbol': order['symbol'],
                'side': order['side'],
                'price': order['price'],
                'quantity': order['quantity'],
                'timestamp': bar.get('time'),
                'pnl': None,
            }}
            ctx.apply_trade(trade)
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

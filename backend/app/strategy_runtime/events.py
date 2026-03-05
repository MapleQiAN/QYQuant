EVENT_NAMES = [
    'on_init',
    'on_bar',
    'on_order',
    'on_trade',
    'on_risk',
    'on_timer',
    'on_error',
    'on_finish',
]


class StrategyContext:
    def __init__(self, symbol, params):
        self.symbol = symbol
        self.params = dict(params or {})
        self.orders = []
        self.logs = []

    def emit_order(self, order):
        if not isinstance(order, dict):
            return
        side = (order.get('side') or '').lower()
        if side not in {'buy', 'sell'}:
            return
        try:
            price = float(order.get('price'))
            quantity = float(order.get('quantity', 1))
        except (TypeError, ValueError):
            return
        if quantity <= 0:
            return

        self.orders.append({
            "symbol": order.get('symbol') or self.symbol,
            "side": side,
            "price": price,
            "quantity": quantity,
        })

    def consume_orders(self):
        items = list(self.orders)
        self.orders = []
        return items

    def log(self, message):
        self.logs.append(str(message)[:500])


from pathlib import Path

from app.strategy_runtime.sandbox import run_strategy_inline


def test_gold_sma_cross_example_generates_trades():
    source = Path(
        r"E:\QYQuant\docs\strategy-format\examples\GoldSmaCross\src\strategy.py"
    ).read_text(encoding="utf-8")

    bars = [
        {"time": 1, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 0},
        {"time": 2, "open": 100, "high": 101, "low": 99, "close": 99, "volume": 0},
        {"time": 3, "open": 99, "high": 100, "low": 98, "close": 98, "volume": 0},
        {"time": 4, "open": 98, "high": 99, "low": 97, "close": 99, "volume": 0},
        {"time": 5, "open": 99, "high": 101, "low": 98, "close": 101, "volume": 0},
        {"time": 6, "open": 101, "high": 103, "low": 100, "close": 103, "volume": 0},
        {"time": 7, "open": 103, "high": 104, "low": 101, "close": 102, "volume": 0},
        {"time": 8, "open": 102, "high": 103, "low": 99, "close": 99, "volume": 0},
    ]

    result = run_strategy_inline(
        symbol="XAUUSD",
        source=source,
        callable_name="Strategy",
        bars=bars,
        params={
            "fast_period": 2,
            "slow_period": 3,
            "order_quantity": 2.0,
        },
    )

    assert [trade["side"] for trade in result["trades"]] == ["buy", "sell"]


def test_qysp_event_v1_strategy_supports_parameters_bardata_and_returned_orders():
    source = """
from qysp import BarData, Order, StrategyContext


def on_bar(ctx: StrategyContext, data: BarData) -> list[Order]:
    window = int(ctx.parameters.get("window", 20))
    if window == 5 and data.close > data.open:
        return [ctx.buy(data.symbol, quantity=2)]
    return []
"""

    result = run_strategy_inline(
        symbol="XAUUSD",
        source=source,
        callable_name="on_bar",
        bars=[
            {"time": 1, "open": 100, "high": 102, "low": 99, "close": 101, "volume": 10},
        ],
        params={"window": 5},
    )

    assert result["trades"] == [
        {
            "symbol": "XAUUSD",
            "side": "buy",
            "price": 101.0,
            "quantity": 2.0,
            "timestamp": 1,
            "pnl": None,
        }
    ]

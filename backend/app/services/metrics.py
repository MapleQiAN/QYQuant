from ..report_agent.quant_engine import INITIAL_CAPITAL, build_legacy_backtest_report


def build_backtest_report(bars, trades, initial_capital=INITIAL_CAPITAL):
    return build_legacy_backtest_report(bars, trades, initial_capital=initial_capital)

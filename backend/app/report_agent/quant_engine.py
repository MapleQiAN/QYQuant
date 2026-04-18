import math
from datetime import datetime, timezone


INITIAL_CAPITAL = 100_000.0
MS_PER_DAY = 86_400_000
SECONDS_PER_YEAR = 31_536_000
MAX_EXPONENT = 700


def compute_all_metrics(bars, trades, initial_capital=INITIAL_CAPITAL):
    normalized_bars = normalize_bars(bars)
    normalized_trades = normalize_trades(trades)
    equity_curve = build_equity_curve(normalized_bars, normalized_trades, initial_capital)
    return {
        "metrics": build_summary_metrics(equity_curve, normalized_trades),
        "equity_curve": equity_curve,
        "drawdown_series": build_drawdown_series(equity_curve),
        "monthly_returns": build_monthly_returns(equity_curve),
        "trade_details": normalized_trades,
    }


def build_report_payload(bars, trades, initial_capital=INITIAL_CAPITAL):
    computed = compute_all_metrics(bars, trades, initial_capital=initial_capital)
    return {
        "metrics": computed["metrics"],
        "equity_curve": computed["equity_curve"],
        "drawdown_series": computed["drawdown_series"],
        "monthly_returns": computed["monthly_returns"],
        "trade_details": computed["trade_details"],
        "anomalies": [],
        "parameter_sensitivity": [],
        "monte_carlo": {},
        "regime_analysis": [],
        "metric_narrations": {},
    }


def build_legacy_backtest_report(bars, trades, initial_capital=INITIAL_CAPITAL):
    computed = compute_all_metrics(bars, trades, initial_capital=initial_capital)
    return {
        "equity_curve": computed["equity_curve"],
        "trades": computed["trade_details"],
        "result_summary": computed["metrics"],
    }


def normalize_bars(bars):
    normalized = []
    for bar in bars or []:
        normalized.append(
            {
                "time": int(bar.get("time")),
                "open": float(bar.get("open", 0.0)),
                "high": float(bar.get("high", 0.0)),
                "low": float(bar.get("low", 0.0)),
                "close": float(bar.get("close", 0.0)),
                "volume": float(bar.get("volume", 0.0)),
            }
        )
    return sorted(normalized, key=lambda item: item["time"])


def normalize_trades(trades):
    normalized = []
    for index, trade in enumerate(trades or []):
        side = str(trade.get("side", "")).lower()
        if side not in {"buy", "sell"}:
            continue
        pnl = trade.get("pnl")
        normalized.append(
            {
                "symbol": trade.get("symbol"),
                "side": side,
                "price": float(trade.get("price", 0.0)),
                "quantity": float(trade.get("quantity", 0.0)),
                "timestamp": int(trade.get("timestamp")),
                "pnl": float(pnl) if pnl is not None else None,
                "_index": index,
            }
        )
    normalized.sort(key=lambda item: (item["timestamp"], item["_index"]))
    for trade in normalized:
        trade.pop("_index", None)
    return normalized


def build_equity_curve(bars, trades, initial_capital):
    if not bars:
        return []

    cash = float(initial_capital)
    position = 0.0
    benchmark_base = bars[0]["close"] or 1.0
    trade_index = 0
    equity_curve = []

    for bar in bars:
        while trade_index < len(trades) and trades[trade_index]["timestamp"] <= bar["time"]:
            trade = trades[trade_index]
            notional = trade["price"] * trade["quantity"]
            if trade["side"] == "buy":
                cash -= notional
                position += trade["quantity"]
            else:
                cash += notional
                position -= trade["quantity"]
            trade_index += 1

        benchmark_equity = float(initial_capital) * (bar["close"] / benchmark_base if benchmark_base else 1.0)
        equity = cash + position * bar["close"]
        equity_curve.append(
            {
                "timestamp": bar["time"],
                "equity": round(equity, 4),
                "benchmark_equity": round(benchmark_equity, 4),
            }
        )

    peak = equity_curve[0]["equity"]
    for point in equity_curve:
        peak = max(peak, point["equity"])
        drawdown = (point["equity"] / peak - 1.0) * 100.0 if peak > 0 else 0.0
        point["drawdown"] = round(drawdown, 4)
    return equity_curve


def build_drawdown_series(equity_curve):
    return [
        {
            "timestamp": point["timestamp"],
            "drawdown": point["drawdown"],
        }
        for point in equity_curve
    ]


def build_monthly_returns(equity_curve):
    if not equity_curve:
        return []

    buckets = {}
    for point in equity_curve:
        dt = datetime.fromtimestamp(point["timestamp"] / 1000.0, tz=timezone.utc)
        month_key = dt.strftime("%Y-%m")
        bucket = buckets.setdefault(
            month_key,
            {
                "start_equity": point["equity"],
                "end_equity": point["equity"],
            },
        )
        bucket["end_equity"] = point["equity"]

    monthly_returns = []
    for month_key in sorted(buckets.keys()):
        start_equity = buckets[month_key]["start_equity"] or 1.0
        end_equity = buckets[month_key]["end_equity"]
        monthly_returns.append(
            {
                "month": month_key,
                "return": round((end_equity / start_equity - 1.0) * 100.0 if start_equity else 0.0, 4),
            }
        )
    return monthly_returns


def build_summary_metrics(equity_curve, trades):
    if len(equity_curve) < 2:
        return empty_summary()

    equities = [point["equity"] for point in equity_curve]
    benchmarks = [point["benchmark_equity"] for point in equity_curve]
    initial_equity = equities[0] or 1.0
    final_equity = equities[-1]
    total_return_ratio = final_equity / initial_equity if initial_equity else 1.0
    total_return = (total_return_ratio - 1.0) * 100.0
    duration_days = max((equity_curve[-1]["timestamp"] - equity_curve[0]["timestamp"]) / MS_PER_DAY, 1 / 365)
    annualized_return = annualize_ratio(total_return_ratio, duration_days)

    strategy_returns = series_returns(equities)
    benchmark_returns = series_returns(benchmarks)
    periods_per_year = periods_per_year_from_curve(equity_curve)
    avg_return = average(strategy_returns)
    std_dev = stddev(strategy_returns)
    downside_std = stddev([item for item in strategy_returns if item < 0.0])
    max_drawdown = min(point["drawdown"] for point in equity_curve)
    volatility = std_dev * math.sqrt(periods_per_year) * 100.0 if std_dev > 0 else 0.0
    sharpe_ratio = avg_return / std_dev * math.sqrt(periods_per_year) if std_dev > 0 else 0.0
    sortino_ratio = avg_return / downside_std * math.sqrt(periods_per_year) if downside_std > 0 else 0.0
    calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown < 0 else 0.0

    closed_trades = match_closed_trades(trades)
    wins = [trade for trade in closed_trades if trade["pnl"] > 0]
    losses = [trade for trade in closed_trades if trade["pnl"] < 0]
    win_rate = len(wins) / len(closed_trades) * 100.0 if closed_trades else 0.0
    gross_profit = sum(trade["pnl"] for trade in wins)
    gross_loss = abs(sum(trade["pnl"] for trade in losses))
    profit_loss_ratio = gross_profit / gross_loss if gross_loss > 0 else 0.0
    max_consecutive_losses = max_consecutive_losses_count(closed_trades)
    avg_holding_days = average([trade["holding_days"] for trade in closed_trades])
    beta = beta_value(strategy_returns, benchmark_returns)
    benchmark_average = average(benchmark_returns)
    alpha = (avg_return - beta * benchmark_average) * periods_per_year * 100.0 if strategy_returns else 0.0

    return {
        "totalReturn": round(total_return, 4),
        "annualizedReturn": round(annualized_return, 4),
        "maxDrawdown": round(max_drawdown, 4),
        "sharpeRatio": round(sharpe_ratio, 4),
        "volatility": round(volatility, 4),
        "sortinoRatio": round(sortino_ratio, 4),
        "calmarRatio": round(calmar_ratio, 4),
        "winRate": round(win_rate, 4),
        "profitLossRatio": round(profit_loss_ratio, 4),
        "maxConsecutiveLosses": int(max_consecutive_losses),
        "avgHoldingDays": round(avg_holding_days, 4),
        "totalTrades": len(closed_trades),
        "alpha": round(alpha, 4),
        "beta": round(beta, 4),
    }


def empty_summary():
    return {
        "totalReturn": 0.0,
        "annualizedReturn": 0.0,
        "maxDrawdown": 0.0,
        "sharpeRatio": 0.0,
        "volatility": 0.0,
        "sortinoRatio": 0.0,
        "calmarRatio": 0.0,
        "winRate": 0.0,
        "profitLossRatio": 0.0,
        "maxConsecutiveLosses": 0,
        "avgHoldingDays": 0.0,
        "totalTrades": 0,
        "alpha": 0.0,
        "beta": 0.0,
    }


def annualize_ratio(total_return_ratio, duration_days):
    if total_return_ratio <= 0:
        return -100.0
    exponent = min((365.0 / duration_days) * math.log(total_return_ratio), MAX_EXPONENT)
    return (math.exp(exponent) - 1.0) * 100.0


def series_returns(values):
    returns = []
    for index in range(1, len(values)):
        previous = values[index - 1]
        current = values[index]
        returns.append(current / previous - 1.0 if previous else 0.0)
    return returns


def periods_per_year_from_curve(equity_curve):
    if len(equity_curve) < 2:
        return 365.0
    delta_ms = max(equity_curve[1]["timestamp"] - equity_curve[0]["timestamp"], 1)
    return max(SECONDS_PER_YEAR / max(delta_ms / 1000.0, 1.0), 1.0)


def average(values):
    if not values:
        return 0.0
    return sum(values) / len(values)


def stddev(values):
    if not values:
        return 0.0
    mean = average(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return math.sqrt(variance)


def match_closed_trades(trades):
    open_lots = []
    closed_trades = []

    for trade in trades:
        quantity = float(trade["quantity"])
        if quantity <= 0:
            continue
        if trade["side"] == "buy":
            open_lots.append(
                {
                    "price": float(trade["price"]),
                    "quantity": quantity,
                    "timestamp": int(trade["timestamp"]),
                }
            )
            continue

        remaining = quantity
        while remaining > 0 and open_lots:
            lot = open_lots[0]
            matched_quantity = min(remaining, lot["quantity"])
            closed_trades.append(
                {
                    "pnl": (float(trade["price"]) - lot["price"]) * matched_quantity,
                    "holding_days": max((int(trade["timestamp"]) - lot["timestamp"]) / MS_PER_DAY, 0.0),
                }
            )
            lot["quantity"] -= matched_quantity
            remaining -= matched_quantity
            if lot["quantity"] <= 0:
                open_lots.pop(0)
    return closed_trades


def max_consecutive_losses_count(closed_trades):
    longest = 0
    current = 0
    for trade in closed_trades:
        if trade["pnl"] < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def beta_value(strategy_returns, benchmark_returns):
    paired = list(zip(strategy_returns, benchmark_returns))
    if len(paired) < 2:
        return 0.0
    strategy_values = [pair[0] for pair in paired]
    benchmark_values = [pair[1] for pair in paired]
    strategy_mean = average(strategy_values)
    benchmark_mean = average(benchmark_values)
    variance = sum((value - benchmark_mean) ** 2 for value in benchmark_values) / len(benchmark_values)
    if variance == 0:
        return 0.0
    covariance = sum(
        (strategy_value - strategy_mean) * (benchmark_value - benchmark_mean)
        for strategy_value, benchmark_value in paired
    ) / len(paired)
    return covariance / variance

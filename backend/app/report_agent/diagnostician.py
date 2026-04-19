def generate_diagnosis(payload, tier):
    metrics = (payload or {}).get("metrics") or {}
    max_drawdown = metrics.get("maxDrawdown", 0)
    total_trades = metrics.get("totalTrades", 0)
    return (
        f"{tier} diagnosis: max drawdown is {max_drawdown}, "
        f"with {total_trades} closed trades. Validate robustness before live use."
    )

def generate_diagnosis(payload, tier, locale="en"):
    lang = "zh" if locale == "zh" else "en"
    metrics = (payload or {}).get("metrics") or {}
    max_drawdown = metrics.get("maxDrawdown", 0)
    total_trades = metrics.get("totalTrades", 0)
    if lang == "zh":
        return (
            f"{tier} 诊断：最大回撤为 {max_drawdown}，"
            f"已完成 {total_trades} 笔交易。请在实盘使用前验证策略稳健性。"
        )
    return (
        f"{tier} diagnosis: max drawdown is {max_drawdown}, "
        f"with {total_trades} closed trades. Validate robustness before live use."
    )

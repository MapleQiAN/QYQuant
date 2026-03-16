# 动量模板

策略逻辑：
- 使用 `ema_period` 和 `signal_period` 计算快慢 EMA。
- 快线金叉慢线且慢线向上时买入。
- 快线死叉慢线或慢线转弱时卖出。

可调参数：
- `ema_period`：快 EMA 周期（默认 12）
- `signal_period`：慢 EMA 周期（默认 26）

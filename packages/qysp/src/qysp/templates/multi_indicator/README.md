# 多指标模板

策略逻辑：
- 使用 `sma_period` 计算趋势方向。
- 使用 `bb_period`/`bb_std` 判断价格是否突破布林带。
- 使用 `atr_period` 判断波动率是否放大并作为确认信号。
- 三个信号中至少两个同向才下单。

可调参数：
- `sma_period`：SMA 周期（默认 20）
- `atr_period`：ATR 周期（默认 14）
- `bb_period`：布林带周期（默认 20）
- `bb_std`：布林带标准差倍数（默认 2.0）

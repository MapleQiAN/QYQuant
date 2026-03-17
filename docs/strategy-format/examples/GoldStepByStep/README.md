# 黄金阶梯突破策略

这个示例展示 QYSP `event_v1` 模式下的最小可用趋势跟踪策略。

## 策略逻辑

1. 使用 `breakout_lookback` 指定的历史窗口，计算最近一段时间的前高。
2. 当最新收盘价突破前高且当前空仓时，使用 `ctx.buy()` 发出全仓买单。
3. 持仓后持续监控两类退出条件：
   - 最新收盘价相对前一日收盘价的跌幅达到 `drop_one_day_pct`。
   - 最新收盘价相对持仓期最高价的回撤达到 `drop_from_peak_pct`。
4. 任一条件触发时，使用 `ctx.sell()` 一次性卖出全部持仓。

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `breakout_lookback` | integer | `20` | 突破判断使用的历史窗口长度 |
| `drop_one_day_pct` | number | `3.0` | 单日跌幅止损阈值（%） |
| `drop_from_peak_pct` | number | `6.0` | 持仓期最高点回撤止损阈值（%） |

## 示例特点

- 使用标准入口 `on_bar(ctx: StrategyContext, data: BarData) -> list[Order]`
- 所有可调参数都从 `ctx.parameters` 读取
- 使用 `ctx.account.positions` 判断持仓状态
- 通过上下文属性缓存有限历史数据，不依赖 `input()`、`print()` 或自定义账户模型

## 使用方式

```bash
qys validate docs/strategy-format/examples/GoldStepByStep/
qys build docs/strategy-format/examples/GoldStepByStep/ --output GoldStepByStep.qys
```

如果 `qys` 尚未在 PATH 中，也可以使用模块方式调用：

```bash
py -3.11 -m qysp.cli.main validate docs/strategy-format/examples/GoldStepByStep/
```

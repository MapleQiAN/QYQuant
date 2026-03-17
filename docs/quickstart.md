# QYSP 快速开始

这份指南面向第一次接触 QYSP 的开发者，目标是在 10 分钟内完成一次“创建 -> 编辑 -> 验证 -> 打包”的完整流程。

## 1. 准备环境

- Python 3.11 或更高版本
- 一个可写目录
- 如果你要直接调用 `sma`、`ema`、`atr` 等指标函数，建议安装带 `indicators` extra 的版本

在仓库根目录安装本地开发版：

```bash
py -3.11 -m pip install -e .\packages\qysp[indicators]
```

如果你已经把 `qys` 加入 PATH，可以直接使用 `qys`。否则把下文中的 `qys` 替换为：

```bash
py -3.11 -m qysp.cli.main
```

预期结果：

```text
Successfully installed qysp-0.1.0
```

## 2. 创建第一个策略

使用内置模板初始化一个趋势跟踪策略：

```bash
qys init my-first-strategy --template trend-following
```

预期结果：

```text
Strategy project 'my-first-strategy' created successfully (template: trend-following)
```

生成的目录结构如下：

```text
my-first-strategy/
├── README.md
├── strategy.json
└── src/
   └── strategy.py
```

## 3. 编辑策略逻辑

QYSP 的 `event_v1` 策略入口固定为 `on_bar(ctx, data)`。你只需要返回订单列表，宿主会负责执行。

```python
from qysp import BarData, Order, StrategyContext


def on_bar(ctx: StrategyContext, data: BarData) -> list[Order]:
    fast_period = int(ctx.parameters.get("fast_period", 5))
    slow_period = int(ctx.parameters.get("slow_period", 20))

    if fast_period >= slow_period:
        return []

    if data.close > data.open:
        return [ctx.buy(data.symbol, quantity=1)]

    return []
```

编辑时重点记住三件事：

1. 所有可调参数都放到 `strategy.json` 的 `parameters` 里，再通过 `ctx.parameters.get()` 读取。
2. 账户和持仓信息从 `ctx.account` 读取，不要自定义账户对象。
3. 下单使用 `ctx.buy()` / `ctx.sell()`，返回值是 `Order` 对象。

## 4. 验证策略

目录验证会检查 `strategy.json` 是否符合 QYSP Schema：

```bash
qys validate my-first-strategy
```

预期结果：

```text
Validation passed
```

如果失败，优先检查：

- 是否缺少 `schemaVersion`、`kind`、`id`、`name`、`version`
- `entrypoint.path` 是否指向 `src/strategy.py`
- `parameters` 中是否存在不合法的 `type` 或越界的默认值

## 5. 打包策略

打包会把目录构建成单文件 `.qys` 包，并自动写入 `integrity` 清单：

```bash
qys build my-first-strategy --output my-first-strategy.qys
```

预期结果：

```text
Package built: my-first-strategy.qys
```

产物可以继续用 `validate` 做完整性检查：

```bash
qys validate my-first-strategy.qys
```

## 6. 10 分钟通关清单

| 阶段 | 命令 | 预期耗时 |
| --- | --- | --- |
| 安装 | `py -3.11 -m pip install -e .\packages\qysp[indicators]` | 2 分钟 |
| 初始化 | `qys init my-first-strategy --template trend-following` | 1 分钟 |
| 修改代码 | 编辑 `src/strategy.py` 与 `strategy.json` | 3 分钟 |
| 验证 | `qys validate my-first-strategy` | 1 分钟 |
| 打包 | `qys build my-first-strategy --output my-first-strategy.qys` | 1 分钟 |
| 自检 | `qys validate my-first-strategy.qys` | 1 分钟 |

## 7. 下一步

- 想看完整示例：阅读 `docs/strategy-format/examples/GoldStepByStep/`
- 想查 SDK 签名：阅读 `docs/api-reference.md`
- 想查 CLI 参数：阅读 `docs/cli-reference.md`
- 想确认 `strategy.json` 可写哪些字段：阅读 `docs/strategy-format/README.md`

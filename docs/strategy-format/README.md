# QY Strategy Package (QYSP) v1

本文定义当前仓库使用的 QYSP 文件格式、`strategy.json` 字段含义以及 `event_v1` 策略接口约束。

## 1. 包格式

- 扩展名：`.qys`
- 实体格式：ZIP 压缩包
- 编码：UTF-8
- 必含文件：`strategy.json`

推荐目录结构：

```text
my-strategy/
├── strategy.json
├── src/
│  └── strategy.py
├── README.md
└── assets/
```

`qys build` 会把上面的目录打包成单文件 `.qys`，并在包内写入 `integrity` 校验信息。

## 2. `strategy.json` 顶层字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `schemaVersion` | string | 是 | 当前固定为 `1.0` |
| `kind` | string | 是 | 当前固定为 `QYStrategy` |
| `id` | string | 是 | UUID |
| `name` | string | 是 | 策略名称 |
| `version` | string | 是 | 版本号 |
| `description` | string | 否 | 策略简介 |
| `language` | string | 是 | 例如 `python` |
| `runtime` | object | 是 | 运行时声明 |
| `entrypoint` | object | 是 | 入口定义 |
| `parameters` | array | 否 | 参数定义列表 |
| `universe` | object | 否 | 标的与市场描述 |
| `data` | object | 否 | 数据需求 |
| `execution` | object | 否 | 执行模型假设 |
| `risk` | object | 否 | 风控约束 |
| `tags` | array | 否 | 标签 |
| `author` | object | 否 | 作者信息 |
| `license` | string | 否 | 许可证 |
| `createdAt` | string | 否 | 创建时间 |
| `updatedAt` | string | 否 | 更新时间 |
| `performance` | object | 否 | 回测摘要 |
| `dependencies` | object | 否 | 依赖声明 |
| `ui` | object | 否 | 前端展示信息 |
| `backtest` | object | 否 | 默认回测配置 |
| `integrity` | object | 否 | 构建产物文件清单 |

## 3. 必填对象

### `runtime`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `name` | string | 是 | 例如 `python` |
| `version` | string | 是 | 例如 `3.11` |

### `entrypoint`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `path` | string | 是 | 入口文件路径，例如 `src/strategy.py` |
| `callable` | string | 是 | 入口函数名，例如 `on_bar` |
| `interface` | string | 否 | 当前建议显式写为 `event_v1` |

## 4. `event_v1` 接口规范

当前仓库中的 `event_v1` 是一个单入口函数，不是多回调对象模型。

标准签名：

```python
from qysp import BarData, Order, StrategyContext


def on_bar(ctx: StrategyContext, data: BarData) -> list[Order]:
    ...
```

约束：

1. `ctx` 类型必须为 `StrategyContext`
2. `data` 类型必须为 `BarData`
3. 返回值必须是 `list[Order]`
4. 下单通过 `ctx.buy()` / `ctx.sell()` 创建 `Order`
5. 不要在策略里使用 `input()`、`print()` 或自定义账户/持仓模型

一个最小示例：

```python
from qysp import BarData, Order, StrategyContext


def on_bar(ctx: StrategyContext, data: BarData) -> list[Order]:
    threshold = float(ctx.parameters.get("threshold", 1.0))
    if data.close > threshold:
        return [ctx.buy(data.symbol, quantity=1)]
    return []
```

## 5. `parameters` 规范

每个参数对象支持以下字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `key` | string | 是 | 参数名 |
| `type` | string | 是 | `integer`、`number`、`string`、`boolean`、`enum`、`array`、`object` |
| `default` | any | 否 | 默认值 |
| `required` | boolean | 否 | 是否必填 |
| `min` | number | 否 | 数值下界 |
| `max` | number | 否 | 数值上界 |
| `step` | number | 否 | UI 步进 |
| `enum` | array | 否 | 枚举候选值 |
| `description` | string | 否 | 参数描述 |
| `ui` | object | 否 | UI 展示提示 |

运行时建议：

- 在策略中统一使用 `ctx.parameters.get("key", fallback)` 读取参数
- 如果宿主侧需要从 `strategy.json` 装载并校验参数，可以使用 `ParameterProvider.from_strategy_json()`

类型与校验规则：

- `integer`：会被转换为 `int`
- `number`：会被转换为 `float`
- `boolean`：支持 `true/false`、`1/0`、`yes/no`
- `string`：会被转换为字符串
- 存在 `min/max` 时，只对数值类型做范围校验
- 存在 `enum` 时，值必须落在枚举列表中

## 6. 常见可选字段

### `universe`

推荐字段：

- `symbols`
- `assetClass`
- `market`
- `currency`
- `timezone`

### `data`

推荐字段：

- `resolution`
- `fields`
- `lookback`

### `execution`

推荐字段：

- `orderTypes`
- `slippageBps`
- `commissionBps`
- `priceType`
- `maxOrdersPerDay`

### `risk`

推荐字段：

- `maxPositionPct`
- `maxDrawdownPct`
- `stopLossPct`
- `takeProfitPct`
- `cooldownDays`

### `ui`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `icon` | string | 图标标识符或 URL |
| `category` | string | `trend-following`、`mean-reversion`、`momentum`、`multi-indicator`、`other` |
| `difficulty` | string | `beginner`、`intermediate`、`advanced` |

### `backtest`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `defaultPeriod.start` | string | 默认开始日期，格式 `YYYY-MM-DD` |
| `defaultPeriod.end` | string | 默认结束日期，格式 `YYYY-MM-DD` |
| `initialCapital` | number | 默认初始资金 |

### `dependencies`

- `pip`：pip 依赖列表
- `conda`：conda 依赖列表

### `integrity`

`qys build` 会自动写入：

```json
{
  "integrity": {
    "files": [
      {
        "path": "src/strategy.py",
        "sha256": "...",
        "size": 1234
      }
    ]
  }
}
```

`qys validate package.qys` 会检查这些摘要是否与包内真实文件一致。

## 7. 最小完整示例

```json
{
  "schemaVersion": "1.0",
  "kind": "QYStrategy",
  "id": "00000000-0000-0000-0000-000000000000",
  "name": "my-strategy",
  "version": "0.1.0",
  "description": "示例策略",
  "language": "python",
  "runtime": {
    "name": "python",
    "version": "3.11"
  },
  "entrypoint": {
    "path": "src/strategy.py",
    "callable": "on_bar",
    "interface": "event_v1"
  },
  "parameters": [
    {
      "key": "lookback",
      "type": "integer",
      "default": 20,
      "min": 5,
      "description": "历史窗口长度"
    }
  ],
  "ui": {
    "category": "trend-following",
    "difficulty": "beginner"
  }
}
```

## 8. 参考示例

- `docs/strategy-format/examples/GoldStepByStep/`
- `docs/strategy-format/examples/GoldTrend/`

这两个目录分别展示了“纯突破 + 双止损”和“均线过滤 + 突破跟踪”两种 `event_v1` 写法。

# QYSP API 参考

本文记录当前公开 SDK 的核心类型、函数签名和使用方式。除特别说明外，下面的内容都与 `packages/qysp/src/qysp/` 中的源码保持一致。

## 1. 根命名空间导出

```python
from qysp import (
    Account,
    BarData,
    Order,
    OrderSide,
    OrderType,
    ParameterAccessor,
    ParameterProvider,
    Position,
    StrategyContext,
    ValidationError,
    atr,
    bollinger_bands,
    cross_over,
    cross_under,
    ema,
    sma,
    validate,
    validate_integrity,
    validate_schema,
)
```

`OnBarCallable` 定义在 `qysp.context` 中，当前没有从 `qysp` 根命名空间重新导出。

## 2. 核心数据类

### `BarData`

```python
@dataclass
class BarData:
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    datetime: datetime
```

- 用途：描述一根 K 线
- 校验：`open/high/low/close/volume` 不能为负数

### `OrderSide`

```python
class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"
```

### `OrderType`

```python
class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
```

### `Order`

```python
@dataclass
class Order:
    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType
    limit_price: float | None = None
```

- 用途：表达“想下什么单”，不包含撮合后的成交结果

### `Position`

```python
@dataclass
class Position:
    symbol: str
    quantity: float
    avg_cost: float
    current_price: float
```

属性：

```python
position.market_value -> float
position.unrealized_pnl -> float
position.unrealized_pnl_pct -> float
```

### `Account`

```python
@dataclass
class Account:
    cash: float
    positions: dict[str, Position] = field(default_factory=dict)
```

属性：

```python
account.total_value -> float
```

## 3. `StrategyContext`

构造函数：

```python
class StrategyContext:
    def __init__(
        self,
        account: Account,
        parameters: ParameterAccessor | None = None,
        current_dt: datetime | None = None,
    ) -> None: ...
```

核心属性：

```python
ctx.account: Account
ctx.parameters: ParameterAccessor
ctx.current_dt: datetime | None
```

下单辅助方法：

```python
def buy(
    self,
    symbol: str,
    quantity: float,
    order_type: OrderType = OrderType.MARKET,
    limit_price: float | None = None,
) -> Order: ...


def sell(
    self,
    symbol: str,
    quantity: float,
    order_type: OrderType = OrderType.MARKET,
    limit_price: float | None = None,
) -> Order: ...
```

使用示例：

```python
def on_bar(ctx: StrategyContext, data: BarData) -> list[Order]:
    position = ctx.account.positions.get(data.symbol)
    if position is None:
        return [ctx.buy(data.symbol, quantity=1)]
    return [ctx.sell(data.symbol, quantity=position.quantity)]
```

## 4. 参数访问与注入

### `ParameterAccessor`

定义位置：`qysp.context`

```python
class ParameterAccessor:
    def __init__(self, data: dict[str, Any] | None = None) -> None: ...
    def get(self, key: str, default: Any = None) -> Any: ...
```

- 用途：按 key 读取策略参数
- 特点：不做类型转换，只是简单字典包装

### `ParameterProvider`

定义位置：`qysp.parameters`

```python
class ParameterProvider(ParameterAccessor):
    @classmethod
    def from_strategy_json(
        cls,
        definitions: list[dict[str, Any]],
        overrides: dict[str, Any] | None = None,
    ) -> "ParameterProvider": ...
```

- 用途：从 `strategy.json.parameters` 构造一个带校验能力的参数访问器
- 支持：
  - `integer` / `number` / `boolean` / `string` 类型转换
  - `required`
  - `min` / `max`
  - `enum`

示例：

```python
definitions = [
    {"key": "lookback", "type": "integer", "default": 20, "min": 5},
    {"key": "threshold", "type": "number", "default": 3.0},
]

params = ParameterProvider.from_strategy_json(definitions, overrides={"lookback": 30})
assert params.get("lookback") == 30
```

### `ValidationError`

```python
class ValidationError(ValueError):
    ...
```

- 抛出位置：参数类型转换失败、范围校验失败、Schema/完整性校验失败等场景

## 5. event_v1 入口

定义位置：`qysp.context`

```python
OnBarCallable = Callable[[StrategyContext, BarData], list[Order]]
```

这就是当前 `event_v1` 的标准签名：

```python
def on_bar(ctx: StrategyContext, data: BarData) -> list[Order]:
    ...
```

当前 SDK 没有 `on_init`、`on_trade`、`ctx.emit_order()` 这类公开接口，策略应直接返回 `Order` 列表。

## 6. 指标函数

所有指标函数都定义在 `qysp.indicators` 中，输入输出使用 `pandas.Series`。如果你要直接调用这些函数，请安装 `qysp[indicators]`。

### `sma`

```python
def sma(series: pd.Series, period: int = 20) -> pd.Series: ...
```

- 作用：简单移动平均
- 失败条件：`series` 为空，或 `period <= 0`

示例：

```python
prices = pd.Series([1, 2, 3, 4, 5], dtype=float)
line = sma(prices, period=3)
```

### `ema`

```python
def ema(series: pd.Series, period: int = 20) -> pd.Series: ...
```

- 作用：指数移动平均

### `atr`

```python
def atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series: ...
```

- 作用：平均真实波幅
- 失败条件：任一序列为空、长度不一致、`period <= 0`

### `bollinger_bands`

```python
def bollinger_bands(
    series: pd.Series,
    period: int = 20,
    num_std: float = 2.0,
) -> tuple[pd.Series, pd.Series, pd.Series]: ...
```

- 返回：`(upper, middle, lower)`

### `cross_over`

```python
def cross_over(s1: pd.Series, s2: pd.Series) -> pd.Series: ...
```

- 返回：布尔序列。上一根 `s1 <= s2` 且当前根 `s1 > s2` 时为 `True`

### `cross_under`

```python
def cross_under(s1: pd.Series, s2: pd.Series) -> pd.Series: ...
```

- 返回：布尔序列。上一根 `s1 >= s2` 且当前根 `s1 < s2` 时为 `True`

## 7. 验证函数

### `validate_schema`

```python
def validate_schema(strategy_json: dict) -> list[str]: ...
```

- 输入：解析后的 `strategy.json`
- 返回：错误列表，空列表表示 Schema 合法

### `validate_integrity`

```python
def validate_integrity(qys_path: str | Path) -> bool: ...
```

- 输入：`.qys` 文件路径
- 作用：验证 `integrity.files[*].sha256` 与包内文件是否一致
- 成功返回：`True`
- 失败抛出：`ValidationError`

### `validate`

```python
def validate(path: str | Path) -> dict: ...
```

返回结构：

```python
{
    "valid": bool,
    "errors": list[str],
    "metadata": {"name": str, "version": str},
}
```

行为差异：

- 传入目录：只验证 `strategy.json` Schema
- 传入 `.qys`：验证 Schema + 完整性

## 8. 推荐导入方式

策略代码中优先使用：

```python
from qysp import BarData, Order, StrategyContext
```

当你需要使用进阶类型时再按模块导入：

```python
from qysp.context import OnBarCallable
from qysp.parameters import ParameterProvider
```

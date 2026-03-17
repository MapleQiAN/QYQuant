# Story 1.2: event_v1 接口规范与 StrategyContext 核心类

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

作为策略开发者，
我希望拥有完整的 SDK 类（StrategyContext、BarData、Order、Position、Account）和文档化的 event_v1 接口，
以便我能写出类型安全、结构正确的 on_bar 函数。

## Acceptance Criteria

1. `from qysp import StrategyContext, BarData, Order, Position, Account` 可成功导入，无报错
2. 所有 5 个数据类均有完整的 Python 3.11+ 类型注解（使用 `dataclass` 或等效机制）
3. `on_bar(ctx: StrategyContext, data: BarData) -> list[Order]` 为文档化的标准入口函数签名（event_v1 接口）
4. `ctx.account` 返回包含 `cash`、`total_value`、`positions` 属性的 Account 对象
5. `ctx.parameters` 返回一个支持 `.get(key, default)` 的参数访问器（为 Story 1.3 ParameterProvider 预留接口）
6. `packages/qysp/tests/test_context.py` 单元测试分支覆盖率 ≥80%

## Tasks / Subtasks

- [x] Task 1: 实现 BarData 数据类 (AC: 2)
  - [x] 1.1 在 `packages/qysp/src/qysp/context.py` 中创建 `BarData` dataclass，字段：`symbol: str`、`open: float`、`high: float`、`low: float`、`close: float`、`volume: int`、`datetime: datetime`
  - [x] 1.2 添加 `__post_init__` 验证（价格 ≥ 0、volume ≥ 0）

- [x] Task 2: 实现 Order 数据类 (AC: 2)
  - [x] 2.1 创建 `OrderSide` 枚举：`BUY`、`SELL`
  - [x] 2.2 创建 `OrderType` 枚举：`MARKET`、`LIMIT`
  - [x] 2.3 创建 `Order` dataclass，字段：`symbol: str`、`side: OrderSide`、`quantity: float`、`order_type: OrderType`、`limit_price: float | None = None`

- [x] Task 3: 实现 Position 数据类 (AC: 2)
  - [x] 3.1 创建 `Position` dataclass，字段：`symbol: str`、`quantity: float`、`avg_cost: float`、`current_price: float`
  - [x] 3.2 添加计算属性（`@property`）：`market_value -> float`、`unrealized_pnl -> float`、`unrealized_pnl_pct -> float`

- [x] Task 4: 实现 Account 数据类 (AC: 2, 4)
  - [x] 4.1 创建 `Account` dataclass，字段：`cash: float`、`positions: dict[str, Position]`
  - [x] 4.2 添加计算属性：`total_value -> float`（cash + 所有 positions 的 market_value 之和）

- [x] Task 5: 实现 StrategyContext 核心类 (AC: 1, 3, 4, 5)
  - [x] 5.1 创建 `StrategyContext` 类，属性：`account: Account`、`parameters: ParameterAccessor`、`current_dt: datetime | None`
  - [x] 5.2 实现 `ParameterAccessor` 类（简易版），支持 `.get(key, default=None)` 方法，内部存储 `dict[str, Any]`
  - [x] 5.3 实现 `buy(symbol, quantity, order_type, limit_price)` 便捷方法，返回 `Order`
  - [x] 5.4 实现 `sell(symbol, quantity, order_type, limit_price)` 便捷方法，返回 `Order`
  - [x] 5.5 定义 `OnBarCallable = Callable[[StrategyContext, BarData], list[Order]]` 类型别名（文档化 event_v1 签名）

- [x] Task 6: 更新 `__init__.py` 公共导出 (AC: 1)
  - [x] 6.1 在 `packages/qysp/src/qysp/__init__.py` 中添加 `from qysp.context import StrategyContext, BarData, Order, Position, Account, OrderSide, OrderType`

- [x] Task 7: 编写单元测试 (AC: 6)
  - [x] 7.1 创建 `packages/qysp/tests/test_context.py`
  - [x] 7.2 测试 BarData 创建和字段校验（含非法数据拒绝）
  - [x] 7.3 测试 Order 创建（市价单 / 限价单）
  - [x] 7.4 测试 Position 计算属性（market_value、unrealized_pnl、unrealized_pnl_pct）
  - [x] 7.5 测试 Account 计算属性（total_value = cash + positions market_value）
  - [x] 7.6 测试 StrategyContext 属性访问和 buy/sell 便捷方法
  - [x] 7.7 测试 ParameterAccessor.get() 方法（含 key 存在 / 不存在 / 默认值）
  - [x] 7.8 验证 `from qysp import StrategyContext, BarData, Order, Position, Account` 导入无报错

## Dev Notes

### 核心设计决策

**1. event_v1 接口设计 — 函数式 vs 类式**

架构文档和现有 GoldTrend 示例同时出现了两种风格：
- **函数式**（epics.md 验收标准）：`on_bar(ctx: StrategyContext, data: BarData) -> list[Order]`
- **类式**（GoldTrend/strategy.py 示例）：`Strategy` 类含 `__init__(self, context, params)` + `on_bar(self, bar)`

**本 Story 实现函数式接口作为 event_v1 的标准定义**，同时确保类的设计允许未来包装为类式适配器。定义 `OnBarCallable` 类型别名作为文档化签名。

**2. ParameterAccessor 预留接口**

本 Story 实现一个**简易版 ParameterAccessor**（内部仅包装 `dict`），为 Story 1.3 的完整 `ParameterProvider`（含类型转换、验证、JSON 加载）预留接口。关键约定：
- `.get(key, default=None)` 是唯一的公共读取方法
- Story 1.3 将扩展为支持从 strategy.json 自动加载、类型转换、必填参数校验

**3. 数据类选型：标准库 `dataclass`**

不使用 Pydantic（零依赖原则，SDK 不引入额外依赖）。使用标准库 `dataclasses` + `@property` 实现计算属性。验证逻辑放在 `__post_init__` 中。

**4. Account.positions 类型：`dict[str, Position]`**

使用 `dict` 而非 `list`，key 为 symbol，方便 O(1) 查找特定标的持仓。与架构文档中 `ctx.account.positions` 的使用场景一致。

**5. Order 不含 ID 和状态**

Order 是策略发出的**意图指令**，不含执行状态。执行结果（成交价、成交量、手续费）由回测引擎处理，不属于 SDK 核心类范围。

### 技术要求

**语言与运行时：**
- Python 3.11+（必须使用 3.11+ 语法特性：`X | Y` 联合类型、`dataclass` slots）
- 零外部依赖（仅使用标准库：`dataclasses`、`enum`、`datetime`、`typing`）

**类型注解要求：**
- 所有公共类、方法、属性必须有完整类型注解
- 使用 `from __future__ import annotations` 启用延迟求值
- `Order` 返回类型使用 `list[Order]`（小写 list，Python 3.9+ 原生泛型）

**代码风格：**
- 遵循 PEP 8，使用 ruff 格式化
- 类名 `PascalCase`，函数/变量 `snake_case`，常量 `UPPER_SNAKE_CASE`
- 私有方法 `_leading_underscore`

**测试要求：**
- 测试框架：pytest 9.x
- 运行命令：`uv run --directory packages/qysp pytest tests/test_context.py`
- 分支覆盖率 ≥80%：检查命令 `uv run --directory packages/qysp pytest tests/test_context.py --cov=qysp.context --cov-branch --cov-report=term-missing`
- 需额外安装 dev 依赖 `pytest-cov`（如尚未安装）

### 架构合规

**必须遵循的架构约束：**

| 约束 ID | 规则 | 来源 |
|---------|------|------|
| ARCH-1 | SDK 包位于 `packages/qysp/`，hatchling 构建，属于 uv workspace | architecture.md |
| ARCH-16 | datetime 相关操作使用 `qysp.utils.time` 中的工具函数 | architecture.md |
| QYSP-FR1 | event_v1 接口规范：`on_bar(ctx, data) -> list[Order]`，含类型注解 | prd-qystrategy-improvement.md |
| QYSP-FR4 | SDK 核心类：StrategyContext / BarData / Order / Position / Account | prd-qystrategy-improvement.md |

**命名规范合规检查：**
- ✅ 类名 PascalCase：`StrategyContext`、`BarData`、`Order`、`Position`、`Account`
- ✅ 枚举名 PascalCase：`OrderSide`、`OrderType`
- ✅ 模块名 snake_case：`context.py`
- ✅ 方法名 snake_case：`buy()`、`sell()`、`get()`

**禁止事项：**
- ❌ 不得引入 Pydantic 或其他第三方验证库（零依赖原则）
- ❌ 不得使用 `datetime.now()`（无时区），如需时间操作使用 `qysp.utils.time`
- ❌ 不得在 SDK 类中依赖全局状态或单例模式
- ❌ 不得在 `context.py` 中实现回测引擎逻辑（Order 只是意图，执行逻辑属于 sandbox.py）

### 库与框架要求

**本 Story 使用的标准库模块（无第三方依赖）：**

| 模块 | 用途 | 版本 |
|------|------|------|
| `dataclasses` | 数据类定义（BarData、Order、Position、Account） | Python 3.11+ 标准库 |
| `enum` | 枚举定义（OrderSide、OrderType） | Python 3.11+ 标准库 |
| `datetime` | BarData.datetime 字段类型 | Python 3.11+ 标准库 |
| `typing` | `Any`、`Callable` 类型别名 | Python 3.11+ 标准库 |

**测试依赖（已在根 pyproject.toml dev-dependencies 中）：**
- `pytest>=9.0` — 已安装
- `pytest-cov` — 如未安装需添加到 `dependency-groups.dev`

**明确不使用：**
- ❌ `pydantic`（零依赖原则）
- ❌ `attrs`（标准库 dataclass 足够）
- ❌ `numpy` / `pandas`（本 Story 不涉及数值计算，indicators.py 是 Story 1.4）

### 文件结构要求

**本 Story 新增/修改的文件：**

```
packages/qysp/
├── src/qysp/
│   ├── __init__.py          # 修改：添加核心类导出
│   └── context.py           # 新增：StrategyContext、BarData、Order、Position、Account
└── tests/
    └── test_context.py      # 新增：核心类单元测试
```

**文件职责边界：**
- `context.py`：**仅**包含 5 个数据类 + StrategyContext + ParameterAccessor + 类型别名
- 不得将验证逻辑（validator.py，Story 1.5）、技术指标（indicators.py，Story 1.4）、参数加载逻辑（Story 1.3）放入此文件

**不得修改的文件：**
- `packages/qysp/src/qysp/utils/time.py`（Story 1.1 已完成）
- `packages/qysp/src/qysp/cli/main.py`（本 Story 不涉及 CLI）
- `backend/` 下所有文件
- `frontend/` 下所有文件
- `docs/strategy-format/` 下的 schema 和示例文件（示例重写是 Story 1.8）

### 测试要求

**测试文件：** `packages/qysp/tests/test_context.py`

**必须覆盖的测试场景：**

```
test_bardata_creation_valid          — 正常创建 BarData，所有字段正确赋值
test_bardata_negative_price_rejected — 负价格触发 ValueError
test_bardata_negative_volume_rejected — 负成交量触发 ValueError
test_order_market_buy                — 创建市价买单，limit_price 为 None
test_order_limit_sell                — 创建限价卖单，limit_price 有值
test_position_market_value           — market_value = quantity * current_price
test_position_unrealized_pnl         — unrealized_pnl = (current_price - avg_cost) * quantity
test_position_unrealized_pnl_pct     — unrealized_pnl_pct = (current_price / avg_cost - 1) * 100
test_account_total_value_no_positions — 无持仓时 total_value = cash
test_account_total_value_with_positions — 有持仓时 total_value = cash + sum(market_value)
test_strategy_context_account_access — ctx.account 返回正确的 Account 对象
test_strategy_context_buy            — ctx.buy() 返回正确的 BUY Order
test_strategy_context_sell           — ctx.sell() 返回正确的 SELL Order
test_parameter_accessor_get_existing — 已有 key 返回对应值
test_parameter_accessor_get_missing_with_default — 缺失 key 返回 default
test_parameter_accessor_get_missing_no_default   — 缺失 key 且无 default 返回 None
test_public_imports                  — from qysp import StrategyContext, BarData, Order, Position, Account 无报错
```

**运行命令：**
```bash
uv run --directory packages/qysp pytest tests/test_context.py -v
uv run --directory packages/qysp pytest tests/test_context.py --cov=qysp.context --cov-branch --cov-report=term-missing
```

### 前一个 Story 经验（Story 1.1）

**关键学习与注意事项：**

1. **uv sync 需使用 `--all-packages` 标志** — 仅 `uv sync` 只安装 dev-dependencies，不会安装 workspace members。确保新模块可被正确导入需运行 `uv sync --all-packages`
2. **hatchling 构建需显式声明 packages** — `packages/qysp/pyproject.toml` 中必须有 `[tool.hatch.build.targets.wheel] packages = ["src/qysp"]`，否则 wheel 构建失败
3. **dev-dependencies 格式已迁移** — 根 `pyproject.toml` 使用 `[dependency-groups] dev = [...]` 而非已弃用的 `[tool.uv] dev-dependencies`。如需新增 `pytest-cov`，添加到此处
4. **测试运行命令** — 使用 `uv run --directory packages/qysp pytest tests/` 而非 `uv run pytest packages/qysp/tests/`
5. **已建立的文件模式** — 测试文件放在 `packages/qysp/tests/test_*.py`，源码放在 `packages/qysp/src/qysp/*.py`
6. **Story 1.1 已创建的文件**（不要重复创建或冲突修改）：
   - `packages/qysp/src/qysp/__init__.py` — 目前仅导出 `__version__ = "0.1.0"`
   - `packages/qysp/src/qysp/utils/time.py` — BEIJING_TZ、to_beijing、now_beijing
   - `packages/qysp/src/qysp/cli/main.py` — Click CLI 骨架
   - `packages/qysp/tests/conftest.py` — 空文件（预留）
   - `packages/qysp/tests/test_utils_time.py` — 8 个时区测试
   - `packages/qysp/tests/test_cli.py` — 3 个 CLI 回归测试

### Git 上下文

**最近 5 次提交：**
```
7b26978 feat: 添加 pytest-flask 依赖并更新相关配置；新增平台功能规划文档和 CLI 测试用例
cef9339 refactor: 重构代码结构，以提高可读性和可维护性
fb3c35a feat: 添加数据源切换功能及时间周期事件支持
043b5c6 feat: 增强回测功能并集成ECharts实现K线图
3e2ad3d feat: 更新 .gitignore，添加 .gitnexus 以支持 GitNexus 索引
```

**代码模式参考：**
- 提交消息格式：`feat: 中文描述`（Conventional Commits 风格，中文正文）
- Story 1.1 代码审查反馈：commit 消息类型要准确（`feat` 用于新功能、`fix` 用于修复）
- 已有 11 个测试全部通过（8 个时区测试 + 3 个 CLI 测试）

### Project Structure Notes

**与统一项目结构的对齐：**
- `context.py` 位置完全符合架构文档定义：`packages/qysp/src/qysp/context.py` [Source: architecture.md#完整项目目录结构]
- 测试文件位置符合规范：`packages/qysp/tests/test_context.py`（镜像 src 结构）[Source: architecture.md#结构规范]
- 公共导出通过 `__init__.py` 管理，符合 Python 包标准做法

**与现有策略示例的关系：**
- GoldTrend `strategy.json` 已声明 `"interface": "event_v1"`，但其 `strategy.py` 使用类式接口（`Strategy` 类）
- GoldStepByStep 使用旧式过程式代码，定义了自己的 `Account`、`Holding` 等 dataclass
- 本 Story 的 SDK 类将替代示例中的手写 dataclass，提供标准化、类型安全的实现
- 示例策略重写为 Story 1.8 范围，本 Story 不修改示例文件

### References

- event_v1 接口定义: [Source: epics.md#Story 1.2]
- SDK 核心类需求: [Source: prd-qystrategy-improvement.md#QYSP-FR1, QYSP-FR4]
- context.py 文件位置: [Source: architecture.md#完整项目目录结构]
- 命名规范（PascalCase 类名、snake_case 方法名）: [Source: architecture.md#命名规范]
- 零依赖 SDK 原则: [Source: architecture.md#决策 2: SDK 依赖策略]
- 测试文件位置规范: [Source: architecture.md#结构规范]
- ParameterProvider 设计预览: [Source: architecture.md#决策 1: 参数注入策略]
- 时区工具函数规范: [Source: architecture.md#时区统一规范（北京时间 UTC+8）]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

无调试问题，所有实现一次通过。

### Completion Notes List

- 实现了 5 个 SDK 核心数据类（BarData、Order、Position、Account、StrategyContext）+ 2 个枚举（OrderSide、OrderType）+ ParameterAccessor + OnBarCallable 类型别名
- 所有类使用标准库 `dataclasses`，零第三方依赖
- BarData 含 `__post_init__` 验证（价格/成交量非负）
- Position 含 3 个计算属性（market_value、unrealized_pnl、unrealized_pnl_pct）
- Account 含 total_value 计算属性（cash + 持仓市值之和）
- StrategyContext 含 buy/sell 便捷方法和 ParameterAccessor 参数访问
- OnBarCallable 类型别名文档化了 event_v1 标准签名
- 27 个单元测试全部通过，分支覆盖率 100%（远超 80% 要求）
- 全量回归 38 个测试通过（原有 11 个 + 新增 27 个），0 回归
- 添加了 pytest-cov 到 dev 依赖组

### File List

- `packages/qysp/src/qysp/context.py` — 新增：SDK 核心类（BarData、Order、Position、Account、StrategyContext、ParameterAccessor、OrderSide、OrderType、OnBarCallable）
- `packages/qysp/src/qysp/__init__.py` — 修改：添加核心类公共导出
- `packages/qysp/tests/test_context.py` — 新增：27 个单元测试
- `pyproject.toml` — 修改：添加 pytest-cov 到 dev 依赖组

### Change Log

- 2026-03-15: Story 创建，状态设为 ready-for-dev（由 create-story 工作流生成）
- 2026-03-15: 完成所有 7 个 Task 的实现，27 个测试通过，分支覆盖率 100%，状态更新为 review

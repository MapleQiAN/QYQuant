# Story 1.3: 参数注入机制（ParameterProvider）

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

作为策略开发者，
我希望 strategy.json 中定义的参数在运行时自动注入到 ctx.parameters，
以便策略代码无需硬编码即可读取可配置的参数值。

## Acceptance Criteria

1. `ctx.parameters.get("lookback", 20)` 返回 strategy.json 中定义的参数值（整数类型），当用户提供覆盖值时返回覆盖值，否则返回 default
2. 类型转换支持 int/float/bool/str 四种基本类型（从 JSON 字符串自动转换）
3. 必填参数（`"required": true`）缺失时抛出 `ValidationError`，错误信息明确指出缺失的参数名称
4. 不含 `parameters` 字段的旧 .qys 文件仍可正常加载（向后兼容），`ctx.parameters.get(key)` 返回 None
5. 参数值超出 `min`/`max` 范围时抛出 `ValidationError`，错误信息包含参数名、当前值和允许范围
6. `ParameterProvider.from_strategy_json(parameters_list, overrides)` 类方法可从 strategy.json 的 parameters 数组和可选覆盖字典创建实例

## Tasks / Subtasks

- [x] Task 1: 实现 ParameterProvider 核心类 (AC: 1, 2, 4, 6)
  - [x] 1.1 在 `packages/qysp/src/qysp/parameters.py` 中创建 `ParameterProvider` 类，继承 `ParameterAccessor` 的 `.get()` 接口
  - [x] 1.2 实现 `from_strategy_json(cls, definitions: list[dict], overrides: dict | None = None)` 类方法
  - [x] 1.3 实现参数解析逻辑：遍历 definitions 列表，提取每个参数的 key、type、default、required、min、max
  - [x] 1.4 实现覆盖值合并：overrides 中的值优先于 default
  - [x] 1.5 确保 `ParameterProvider()` 空构造函数仍然可用（向后兼容 ParameterAccessor）

- [x] Task 2: 实现类型转换引擎 (AC: 2)
  - [x] 2.1 实现 `_coerce_value(value, target_type: str) -> Any` 私有方法
  - [x] 2.2 类型映射：`"integer"` → `int()`、`"number"` → `float()`、`"boolean"` → 布尔解析（"true"/"false"/"1"/"0"）、`"string"` → `str()`
  - [x] 2.3 已经是目标类型的值直接返回（不做冗余转换）
  - [x] 2.4 转换失败时抛出 `ValidationError`，错误信息包含参数名、原始值和目标类型

- [x] Task 3: 实现参数验证 (AC: 3, 5)
  - [x] 3.1 创建 `ValidationError` 异常类（在 `parameters.py` 中定义，继承 `ValueError`）
  - [x] 3.2 实现必填参数检查：`required=True` 且无 default 且无 override 时抛出 `ValidationError`
  - [x] 3.3 实现范围验证：数值类型参数的 min/max 约束检查
  - [x] 3.4 实现 enum 类型验证：值必须在 `"enum"` 列表中

- [x] Task 4: 更新 StrategyContext 集成 (AC: 1, 4)
  - [x] 4.1 更新 `context.py` 中 `StrategyContext.__init__` 的 `parameters` 参数类型，同时接受 `ParameterAccessor | ParameterProvider`
  - [x] 4.2 保持 `ParameterAccessor` 不变（向后兼容），`ParameterProvider` 作为增强替代

- [x] Task 5: 更新 `__init__.py` 公共导出 (AC: 6)
  - [x] 5.1 在 `packages/qysp/src/qysp/__init__.py` 中添加 `from qysp.parameters import ParameterProvider, ValidationError`

- [x] Task 6: 编写单元测试 (AC: 全部)
  - [x] 6.1 创建 `packages/qysp/tests/test_parameters.py`
  - [x] 6.2 测试基本参数加载（从 definitions + defaults）
  - [x] 6.3 测试覆盖值合并（overrides 优先于 default）
  - [x] 6.4 测试 int/float/bool/str 四种类型转换
  - [x] 6.5 测试必填参数缺失报错
  - [x] 6.6 测试 min/max 范围验证
  - [x] 6.7 测试 enum 约束验证
  - [x] 6.8 测试向后兼容（空 parameters 列表 / 无 parameters 字段）
  - [x] 6.9 测试与 StrategyContext 集成（ctx.parameters.get() 工作正常）
  - [x] 6.10 测试 `from qysp import ParameterProvider, ValidationError` 导入无报错

## Dev Notes

### 核心设计决策

**1. ParameterProvider vs ParameterAccessor — 增量替代而非破坏性修改**

Story 1.2 创建了 `ParameterAccessor`（简易 dict 包装器）。本 Story 创建 `ParameterProvider` 作为**增强版替代**：
- `ParameterProvider` 继承或实现与 `ParameterAccessor` 相同的 `.get(key, default)` 接口
- `ParameterAccessor` 保留不变，确保 Story 1.2 的 27 个测试全部继续通过
- `StrategyContext` 同时接受两者（类型 `ParameterAccessor | ParameterProvider`）
- **关键约定：** `.get(key, default)` 仍是唯一公共读取方法，与 Story 1.2 一致

**2. 参数定义格式 — 遵循 qysp.schema.json**

strategy.json 中的 `parameters` 字段使用 `key`（非 `name`）作为参数标识符：
```json
{
  "parameters": [
    {"key": "lookback", "type": "integer", "default": 20, "min": 5, "max": 500},
    {"key": "threshold", "type": "number", "default": 0.05, "required": true}
  ]
}
```
类型枚举值：`"integer"` | `"number"` | `"string"` | `"boolean"` | `"enum"` | `"array"` | `"object"`
（注意：epics 中的伪代码用了 `"int"` 和 `name`，实际实现以 schema 为准）

**3. 类型转换策略 — 宽松输入、严格输出**

- JSON 反序列化后的值可能是字符串（来自 URL 参数、表单提交），需要转换为目标类型
- 已经是正确类型的值（如 JSON 解析出的 int）直接通过，不做冗余转换
- boolean 解析规则：`"true"/"1"/"yes"` → `True`，`"false"/"0"/"no"` → `False`（不区分大小写）

**4. ValidationError 异常设计**

- 继承 `ValueError`（保持与 BarData 验证一致的异常层次结构）
- 错误消息必须包含参数名称，帮助开发者快速定位问题
- 多个验证错误时，逐个抛出第一个（不批量收集），保持简单

**5. 文件拆分 — parameters.py 独立模块**

- 不在 `context.py` 中添加参数加载逻辑（遵循 Story 1.2 的文件职责边界）
- 新建 `packages/qysp/src/qysp/parameters.py` 专门处理参数注入
- `ParameterProvider` 导入 `ParameterAccessor` 并扩展其功能

### 技术要求

**语言与运行时：**
- Python 3.11+（使用 `X | Y` 联合类型语法）
- 零外部依赖（仅使用标准库：`json`、`typing`）
- 不依赖 Pydantic、jsonschema 或其他验证库

**类型注解要求：**
- 所有公共类、方法必须有完整类型注解
- 使用 `from __future__ import annotations` 启用延迟求值

**代码风格：**
- PEP 8 + ruff 格式化
- 类名 `PascalCase`，函数/变量 `snake_case`，常量 `UPPER_SNAKE_CASE`
- 私有方法 `_leading_underscore`

### 架构合规

**必须遵循的架构约束：**

| 约束 ID | 规则 | 来源 |
|---------|------|------|
| ARCH-1 | SDK 包位于 `packages/qysp/`，零外部依赖原则 | architecture.md |
| QYSP-FR2 | 参数注入机制：strategy.json 参数自动注入 ctx.parameters | prd-qystrategy-improvement.md |
| QYSP-FR4 | SDK 核心类的 ParameterAccessor 接口 | prd-qystrategy-improvement.md |
| Schema | parameters 数组中每项 `required: ["key", "type"]` | qysp.schema.json |

**禁止事项：**
- ❌ 不得引入 Pydantic、jsonschema 或其他第三方验证库
- ❌ 不得修改 `ParameterAccessor` 类的现有接口（保持向后兼容）
- ❌ 不得在 `parameters.py` 中实现文件 I/O（strategy.json 的读取由上层调用者完成）
- ❌ 不得使用全局状态或单例模式
- ❌ 不得修改 `context.py` 中 BarData/Order/Position/Account 的任何代码

### 库与框架要求

**本 Story 使用的标准库模块（无第三方依赖）：**

| 模块 | 用途 | 版本 |
|------|------|------|
| `typing` | `Any` 类型 | Python 3.11+ 标准库 |
| `json` | 仅在测试中用于构造测试数据 | Python 3.11+ 标准库 |

**测试依赖（已在根 pyproject.toml dev-dependencies 中）：**
- `pytest>=9.0` — 已安装
- `pytest-cov` — 已安装（Story 1.2 添加）

**明确不使用：**
- ❌ `pydantic`（零依赖原则）
- ❌ `jsonschema`（不在 SDK 中引入，schema 验证是 Story 1.5 的 validator.py 职责）
- ❌ `attrs`（标准库足够）

### 文件结构要求

**本 Story 新增/修改的文件：**

```
packages/qysp/
├── src/qysp/
│   ├── __init__.py          # 修改：添加 ParameterProvider, ValidationError 导出
│   ├── context.py           # 微调：StrategyContext 参数类型注释更新（可选）
│   └── parameters.py        # 新增：ParameterProvider、ValidationError
└── tests/
    └── test_parameters.py   # 新增：参数注入单元测试
```

**文件职责边界：**
- `parameters.py`：**仅**包含 ParameterProvider 类、ValidationError 异常、类型转换逻辑
- 不得将 JSON 文件读取（I/O）、schema 验证（Story 1.5）、技术指标（Story 1.4）放入此文件
- `context.py` 修改量最小化——仅更新 import 和类型注释（如有必要）

**不得修改的文件：**
- `packages/qysp/src/qysp/utils/time.py`（Story 1.1）
- `packages/qysp/src/qysp/cli/main.py`（不涉及 CLI）
- `backend/` 下所有文件
- `frontend/` 下所有文件
- `docs/strategy-format/` 下的 schema 和示例文件

### 测试要求

**测试文件：** `packages/qysp/tests/test_parameters.py`

**必须覆盖的测试场景：**

```
test_from_strategy_json_basic           — 从 definitions 创建 ParameterProvider，get 返回 default 值
test_from_strategy_json_with_overrides  — overrides 优先于 default
test_coerce_integer                     — "42" → int(42)，已是 int 的值直接返回
test_coerce_number                      — "3.14" → float(3.14)
test_coerce_boolean_true                — "true"/"1"/"yes" → True（不区分大小写）
test_coerce_boolean_false               — "false"/"0"/"no" → False
test_coerce_string                      — 任何值 → str()
test_coerce_invalid_type                — "abc" → int 抛出 ValidationError
test_required_param_missing             — required=True 且无 default 无 override → ValidationError
test_required_param_with_default        — required=True 有 default → 正常（不报错）
test_required_param_with_override       — required=True 无 default 有 override → 正常
test_min_max_within_range               — 值在 min/max 范围内 → 正常
test_min_violation                      — 值 < min → ValidationError 含参数名和范围
test_max_violation                      — 值 > max → ValidationError 含参数名和范围
test_enum_valid_value                   — 值在 enum 列表中 → 正常
test_enum_invalid_value                 — 值不在 enum 列表中 → ValidationError
test_backward_compat_empty_params       — 空 parameters 列表 → ParameterProvider 可用，get 返回 None/default
test_backward_compat_no_params          — from_strategy_json([], None) → 空实例
test_strategy_context_with_provider     — StrategyContext 使用 ParameterProvider，ctx.parameters.get() 正常
test_parameter_accessor_unchanged       — ParameterAccessor 原有行为不变（回归测试）
test_public_imports                     — from qysp import ParameterProvider, ValidationError 无报错
```

**运行命令：**
```bash
uv run --directory packages/qysp pytest tests/test_parameters.py -v
uv run --directory packages/qysp pytest tests/test_parameters.py --cov=qysp.parameters --cov-branch --cov-report=term-missing
```

**回归测试：**
```bash
uv run --directory packages/qysp pytest tests/ -v  # 全量测试，确保 38 个旧测试 + 新测试全部通过
```

### 前一个 Story 经验（Story 1.2）

**关键学习与注意事项：**

1. **ParameterAccessor 是占位符** — Story 1.2 的 `ParameterAccessor` 注释明确说"为 Story 1.3 预留接口"。本 Story 的 `ParameterProvider` 是其增强替代
2. **27 个 Story 1.2 测试必须全部通过** — 不得破坏 `ParameterAccessor` 的 `.get()` 行为
3. **分支覆盖率 100%** — Story 1.2 达到了 100% 分支覆盖率，本 Story 也应尽量高
4. **uv run 命令格式** — 使用 `uv run --directory packages/qysp pytest tests/` 而非 `uv run pytest packages/qysp/tests/`
5. **dev-dependencies 格式** — 根 `pyproject.toml` 使用 `[dependency-groups] dev = [...]`
6. **pytest-cov 已安装** — Story 1.2 已添加，无需再次安装
7. **零外部依赖** — SDK 只使用标准库（标准 dataclasses + enum），本 Story 继续遵循

### Git 上下文

**最近 5 次提交：**
```
d2765c9 Refactor code structure for improved readability and maintainability
7b26978 feat: 添加 pytest-flask 依赖并更新相关配置；新增平台功能规划文档和 CLI 测试用例
cef9339 refactor: 重构代码结构，以提高可读性和可维护性
fb3c35a feat: 添加数据源切换功能及时间周期事件支持
043b5c6 feat: 增强回测功能并集成ECharts实现K线图
```

**代码模式参考：**
- 提交消息格式：`feat: 中文描述`（Conventional Commits 风格）
- Story 1.2 完成模式：实现 → 测试 → 全量回归 → 标记 review
- 已有 38 个测试全部通过（8 时区 + 3 CLI + 27 context）

### Project Structure Notes

**与统一项目结构的对齐：**
- `parameters.py` 位置符合架构文档定义：`packages/qysp/src/qysp/parameters.py` [Source: architecture.md#完整项目目录结构]
- 测试文件位置符合规范：`packages/qysp/tests/test_parameters.py`
- 模块拆分原则：context.py 管理执行上下文，parameters.py 管理参数注入——职责分离

**与 strategy.json schema 的关系：**
- `qysp.schema.json` 定义了参数的 JSON 结构（`key`、`type`、`default`、`min`、`max`、`enum` 等）
- 本 Story 的 `ParameterProvider.from_strategy_json()` 解析此结构
- GoldTrend 示例已有 3 个真实参数定义（breakoutLookback/integer、dropOneDayPct/number、dropFromPeakPct/number），可作为集成测试参考

**与后续 Story 的关系：**
- Story 1.4（技术指标函数库）：独立于参数注入，无依赖
- Story 1.5（JSON Schema 验证）：`validator.py` 使用 `parameters.py` 的 ValidationError
- Story 1.6（CLI 工具）：`qys validate` 子命令将调用参数验证
- Story 1.8（示例策略重写）：重写后的策略将使用 `ctx.parameters.get()` 读取参数

### References

- 参数注入需求: [Source: epics.md#Story 1.3]
- QYSP-FR2 参数注入机制: [Source: prd-qystrategy-improvement.md#QYSP-FR2]
- 参数 schema 定义: [Source: docs/strategy-format/qysp.schema.json#definitions/parameter]
- GoldTrend 参数示例: [Source: docs/strategy-format/examples/GoldTrend/strategy.json#parameters]
- ParameterAccessor 预留接口: [Source: packages/qysp/src/qysp/context.py#L104-L112]
- 参数注入架构决策: [Source: architecture.md#决策 1: 参数注入策略]
- 多层参数系统设计: [Source: architecture.md#参数系统跨层关注点]

## Change Log

- 2026-03-16: 完成 Story 1.3 全部实现 — ParameterProvider 核心类、类型转换引擎、参数验证、StrategyContext 集成、公共导出更新、37 个单元测试

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

无调试问题。

### Completion Notes List

- ParameterProvider 继承 ParameterAccessor，通过 `.get(key, default)` 提供参数访问
- `from_strategy_json()` 类方法解析 strategy.json 的 parameters 数组，支持 overrides 覆盖
- 类型转换引擎支持 integer/number/boolean/string，宽松输入严格输出
- ValidationError 继承 ValueError，错误信息包含参数名用于快速定位
- 必填参数、min/max 范围、enum 约束三层验证
- 向后兼容：ParameterAccessor 不变，空构造函数可用，旧测试全部通过
- 全量测试 75/75 通过（38 旧 + 37 新），参数模块分支覆盖率 91%
- 零外部依赖，仅使用标准库

### File List

- packages/qysp/src/qysp/parameters.py (新增)
- packages/qysp/src/qysp/__init__.py (修改)
- packages/qysp/src/qysp/context.py (修改 — 仅注释)
- packages/qysp/tests/test_parameters.py (新增)

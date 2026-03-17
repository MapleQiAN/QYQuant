# Story 1.5: QYSP 元数据增强与 JSON Schema 验证

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

作为策略开发者，
我希望 strategy.json 支持可选的 ui 和 backtest 元数据字段，并且验证器能检查 .qys 包完整性，
以便策略携带展示元数据，且发布前可被校验。

## Acceptance Criteria

1. 包含新增可选字段 `ui`（icon、category、difficulty）和 `backtest`（defaultPeriod、initialCapital）的 strategy.json 正确解析；旧版不含这些字段的 strategy.json 仍可正常加载（完全向后兼容）
2. 调用 `qysp.validator.validate(path)` 时，SHA256 校验和与 manifest 一致时验证通过（返回成功）
3. 校验和不匹配时抛出包含 "checksum mismatch" 的 `ValidationError`
4. strategy.json 不符合 schema 时错误信息指明具体的无效字段名
5. `tests/test_validator.py` 单元测试分支覆盖率 ≥ 80%

## Tasks / Subtasks

- [x] Task 1: 扩展 JSON Schema — 添加 ui 和 backtest 可选字段 (AC: 1)
  - [x] 1.1 在 `docs/strategy-format/qysp.schema.json` 中添加 `ui` 对象定义（icon: string, category: enum, difficulty: enum）
  - [x] 1.2 添加 `backtest` 对象定义（defaultPeriod: object{start,end}, initialCapital: number）
  - [x] 1.3 所有新字段均为可选（不加入 required），确保向后兼容
  - [x] 1.4 验证现有 GoldTrend/strategy.json 和 GoldStepByStep/strategy.json 仍通过 schema 校验

- [x] Task 2: 创建 validator.py 模块 — JSON Schema 验证 (AC: 4)
  - [x] 2.1 在 `packages/qysp/src/qysp/validator.py` 中创建模块
  - [x] 2.2 实现 `validate_schema(strategy_json: dict) -> list[str]`：使用 jsonschema 库验证 strategy.json 内容
  - [x] 2.3 错误信息必须包含无效字段名（通过 jsonschema.ValidationError.path 提取）
  - [x] 2.4 schema 从 `docs/strategy-format/qysp.schema.json` 加载（使用 `importlib.resources` 或打包到 SDK 中）

- [x] Task 3: 实现 .qys 包完整性验证 (AC: 2, 3)
  - [x] 3.1 实现 `validate_integrity(qys_path: str | Path) -> bool`：读取 .qys 包（ZIP 格式）
  - [x] 3.2 从包内 strategy.json 读取 `integrity.files` 数组
  - [x] 3.3 对每个文件计算 SHA256，与 manifest 中记录的 sha256 对比
  - [x] 3.4 校验通过返回 True；校验失败抛出 `ValidationError("checksum mismatch: {filename}")`
  - [x] 3.5 处理边缘情况：包内缺少 strategy.json、integrity 字段缺失、文件不存在

- [x] Task 4: 实现统一的 validate() 入口函数 (AC: 2, 3, 4)
  - [x] 4.1 实现 `validate(path: str | Path) -> dict`：统一入口
  - [x] 4.2 自动检测输入类型：.qys 文件 → 完整性 + schema 验证；目录 → 仅 schema 验证
  - [x] 4.3 返回验证结果 dict：`{"valid": bool, "errors": list[str], "metadata": dict}`

- [x] Task 5: 定义 ValidationError 异常类 (AC: 3, 4)
  - [x] 5.1 复用 `parameters.py` 已有的 `ValidationError(ValueError)`（方案 A）
  - [x] 5.2 validator.py 通过 `from qysp.parameters import ValidationError` 导入，保持 SDK 异常统一
  - [x] 5.3 `__init__.py` 中 ValidationError 来源不变（parameters.py），validator 函数额外导出

- [x] Task 6: 添加 jsonschema 依赖 (AC: 全部)
  - [x] 6.1 在 `packages/qysp/pyproject.toml` 的 dependencies 中添加 `jsonschema>=4.0`
  - [x] 6.2 运行 `uv sync` 更新 lock 文件

- [x] Task 7: 将 schema 文件打包到 SDK (AC: 4)
  - [x] 7.1 将 `qysp.schema.json` 复制到 `packages/qysp/src/qysp/schema/` 目录
  - [x] 7.2 使用 `importlib.resources` 在运行时加载 schema（确保打包后可用）
  - [x] 7.3 添加 `schema/__init__.py` 使其成为包

- [x] Task 8: 更新 `__init__.py` 公共导出 (AC: 全部)
  - [x] 8.1 添加 `from qysp.validator import validate, validate_schema, validate_integrity`
  - [x] 8.2 ValidationError 继续从 parameters.py 导出，无命名冲突

- [x] Task 9: 编写单元测试 (AC: 5)
  - [x] 9.1 创建 `packages/qysp/tests/test_validator.py`
  - [x] 9.2 覆盖所有验收标准的正常/异常路径（28 个测试用例）
  - [x] 9.3 分支覆盖率 95%（≥ 80% 要求）

## Dev Notes

### 核心设计决策

**1. JSON Schema 扩展策略 — 向后兼容**

现有 `qysp.schema.json` 已定义完整的策略包结构。Story 1.5 需新增两个可选顶级字段：

```json
"ui": {
  "type": "object",
  "properties": {
    "icon": { "type": "string", "description": "策略图标标识符或 URL" },
    "category": {
      "type": "string",
      "enum": ["trend-following", "mean-reversion", "momentum", "multi-indicator", "other"],
      "description": "策略分类（与架构文档 strategies.category 字段对齐）"
    },
    "difficulty": {
      "type": "string",
      "enum": ["beginner", "intermediate", "advanced"],
      "description": "适合的用户水平"
    }
  }
},
"backtest": {
  "type": "object",
  "properties": {
    "defaultPeriod": {
      "type": "object",
      "properties": {
        "start": { "type": "string", "description": "默认回测开始日期 YYYY-MM-DD" },
        "end": { "type": "string", "description": "默认回测结束日期 YYYY-MM-DD" }
      }
    },
    "initialCapital": {
      "type": "number",
      "minimum": 0,
      "description": "默认初始资金"
    }
  }
}
```

**关键约束：** 这些字段必须是可选的（不加入顶级 `required` 数组），现有的 GoldTrend 和 GoldStepByStep 策略不含这些字段也必须通过校验。

[Source: epics.md#Story 1.5 验收标准第 1 条]
[Source: architecture.md#FR-3 策略元数据增强]

**2. .qys 包结构与完整性验证**

.qys 文件是 ZIP 格式压缩包，内部包含：
- `strategy.json` — 策略清单（含 `integrity.files` 数组）
- `src/strategy.py` — 策略代码
- 其他文件

`integrity.files` 数组中每个条目包含 `path`、`sha256`、`size`。验证器需：
1. 解压 .qys（ZIP）
2. 读取 strategy.json → 提取 integrity.files
3. 对每个列出的文件计算 SHA256，与 manifest 值对比
4. 全部匹配 → 通过；任何不匹配 → 抛出 ValidationError("checksum mismatch: {filename}")

[Source: docs/strategy-format/qysp.schema.json#integrity 定义]

**3. jsonschema 库选择**

使用 `jsonschema` 标准库（PyPI 包），理由：
- JSON Schema Draft-07 验证（与现有 schema 的 `$schema` 声明对齐）
- 错误信息包含 `path` 属性，可提取具体的无效字段名
- Python 生态标准验证库，维护活跃

```python
from jsonschema import validate as jschema_validate, ValidationError as JSchemaValidationError

try:
    jschema_validate(instance=strategy_data, schema=schema)
except JSchemaValidationError as e:
    field_path = ".".join(str(p) for p in e.absolute_path)
    raise ValidationError(f"Invalid field '{field_path}': {e.message}")
```

**4. ValidationError 命名冲突处理**

当前 `parameters.py` 已导出 `ValidationError`。有两个方案：
- **方案 A（推荐）：** validator.py 定义独立的 `SchemaValidationError` 或直接复用 parameters.py 的 `ValidationError`
- **方案 B：** 在 validator.py 中定义 `ValidationError` 并通过模块限定名区分

**推荐方案 A**：复用 `parameters.py` 的 `ValidationError`（通过 import），保持 SDK 内异常类型统一。如果 `parameters.py` 的 `ValidationError` 太过简单，可扩展它。

**5. Schema 打包策略**

将 `qysp.schema.json` 复制到 `packages/qysp/src/qysp/schema/qysp.schema.json`，使用 `importlib.resources` 加载：

```python
import importlib.resources as pkg_resources
import json

def _load_schema() -> dict:
    schema_text = pkg_resources.files("qysp.schema").joinpath("qysp.schema.json").read_text()
    return json.loads(schema_text)
```

需确保 `hatchling` 构建时包含此文件（在 `packages/qysp/src/qysp/schema/` 下添加 `__init__.py`）。

### 技术要求

**语言与运行时：**
- Python 3.11+
- jsonschema >= 4.0（新增依赖）

**类型注解要求：**
- 所有公共函数必须有完整类型注解
- 使用 `from __future__ import annotations` 启用延迟求值
- Path 类型用 `pathlib.Path`

**代码风格：**
- PEP 8 + ruff 格式化
- 函数名 `snake_case`
- 每个公共函数必须有 docstring

### 架构合规

**必须遵循的架构约束：**

| 约束 ID | 规则 | 来源 |
|---------|------|------|
| ARCH-1 | SDK 包位于 `packages/qysp/` | architecture.md#项目结构 |
| QYSP-FR3 | 新增 ui 和 backtest 元数据字段，完全向后兼容 | epics.md#Story 1.5 / prd-qystrategy-improvement.md#FR-3 |
| QYSP-FR7 | SHA256 完整性验证（为后续 Web 导入页面提供基础） | prd-qystrategy-improvement.md#FR-7 |
| Schema | 使用 JSON Schema Draft-07 验证 | docs/strategy-format/qysp.schema.json |
| AC-4 | 验证错误信息必须包含具体的无效字段名 | epics.md#Story 1.5 验收标准 |

**禁止事项：**
- ❌ 不得修改 `context.py`（Story 1.2 核心类）
- ❌ 不得修改 `indicators.py`（Story 1.4 指标函数）
- ❌ 不得修改 `parameters.py`（Story 1.3 参数注入）的行为逻辑
- ❌ 不得将新字段添加到 schema 的 `required` 数组（破坏向后兼容）
- ❌ 不得使用 eval/exec 处理 JSON 数据

### 库与框架要求

**本 Story 使用的库：**

| 模块 | 用途 | 版本 |
|------|------|------|
| `jsonschema` | JSON Schema Draft-07 验证 | >= 4.0 |
| `hashlib` | SHA256 计算 | 标准库 |
| `zipfile` | .qys 包解压 | 标准库 |
| `importlib.resources` | 加载打包的 schema 文件 | 标准库 |
| `json` | JSON 解析 | 标准库 |
| `pathlib` | 路径操作 | 标准库 |

**测试依赖（已有）：**
- `pytest >= 9.0`
- `pytest-cov`

**明确不使用：**
- ❌ `pydantic`（过重，jsonschema 足够）
- ❌ `cerberus`（不支持 JSON Schema 标准格式）

### 文件结构要求

**本 Story 新增/修改的文件：**

```
packages/qysp/
├── src/qysp/
│   ├── __init__.py              # 修改：添加 validator 导出
│   ├── validator.py             # 新增：JSON Schema 验证 + .qys 完整性校验
│   └── schema/
│       ├── __init__.py          # 新增：使 schema 成为包（importlib.resources）
│       └── qysp.schema.json     # 新增：从 docs/strategy-format/ 复制
└── tests/
    └── test_validator.py        # 新增：验证器单元测试

docs/strategy-format/
└── qysp.schema.json             # 修改：添加 ui 和 backtest 可选字段

packages/qysp/pyproject.toml     # 修改：添加 jsonschema 依赖
uv.lock                          # 自动更新
```

**文件职责边界：**
- `validator.py`：JSON Schema 验证 + .qys 包完整性校验，不含策略执行逻辑
- `schema/`：存放 JSON Schema 文件，运行时通过 importlib.resources 加载
- 不得在 validator.py 中引用 StrategyContext、ParameterProvider 或 indicators

**不得修改的文件：**
- `packages/qysp/src/qysp/context.py`
- `packages/qysp/src/qysp/indicators.py`
- `packages/qysp/src/qysp/parameters.py`
- `backend/` 下所有文件
- `frontend/` 下所有文件

### 测试要求

**测试文件：** `packages/qysp/tests/test_validator.py`

**必须覆盖的测试场景：**

```
# Schema 验证测试
test_validate_schema_valid_minimal       — 仅含 required 字段的 strategy.json 通过验证
test_validate_schema_valid_with_ui       — 包含 ui 字段的 strategy.json 通过验证
test_validate_schema_valid_with_backtest — 包含 backtest 字段的 strategy.json 通过验证
test_validate_schema_valid_full          — 包含所有字段的 strategy.json 通过验证
test_validate_schema_missing_required    — 缺少 required 字段时报错并指明字段名
test_validate_schema_invalid_type        — 字段类型错误时报错并指明字段名
test_validate_schema_invalid_enum        — category/difficulty 枚举值无效时报错
test_validate_schema_backward_compat     — 现有 GoldTrend 示例 strategy.json 通过验证

# .qys 完整性验证测试
test_validate_integrity_valid            — SHA256 匹配的 .qys 包验证通过
test_validate_integrity_checksum_mismatch — SHA256 不匹配时抛出 ValidationError("checksum mismatch")
test_validate_integrity_missing_file     — manifest 中列出但包内不存在的文件报错
test_validate_integrity_no_strategy_json — .qys 包缺少 strategy.json 时报错
test_validate_integrity_no_integrity     — strategy.json 无 integrity 字段时的行为（应跳过或警告）

# 统一入口测试
test_validate_qys_file                   — .qys 文件路径输入，执行完整验证
test_validate_directory                  — 目录路径输入，仅执行 schema 验证
test_validate_nonexistent_path           — 不存在的路径抛出 FileNotFoundError

# ValidationError 测试
test_validation_error_message_contains_field — 验证错误消息包含具体字段名
test_validation_error_is_exception       — ValidationError 是 Exception 子类

# 公共导入测试
test_public_imports                      — from qysp.validator import validate, ValidationError 无报错
```

**运行命令：**
```bash
uv run --directory packages/qysp pytest tests/test_validator.py -v
uv run --directory packages/qysp pytest tests/test_validator.py --cov=qysp.validator --cov-branch --cov-report=term-missing
```

**回归测试：**
```bash
uv run --directory packages/qysp pytest tests/ -v  # 全量测试，确保所有旧测试 + 新测试全部通过
```

### 前一个 Story 经验（Story 1.4）

**关键学习与注意事项：**

1. **pytest-cov + Windows 冲突** — Story 1.4 发现 `--cov=qysp.indicators` 在 Windows 上可能因 numpy 多次加载报错，改用 `--cov=qysp` 全包覆盖可绕过。本 Story 也应注意此问题。
2. **测试模式** — 使用 `uv run --directory packages/qysp pytest tests/` 格式运行测试
3. **分支覆盖率 ≥ 80%** — 使用 `--cov-branch` 检查
4. **dev-dependencies** — 根 `pyproject.toml` 使用 `[dependency-groups] dev = [...]`
5. **Code Review 经验** — Story 1.4 code review 发现需添加输入验证和类型检查，validator 模块应从一开始就做好参数验证
6. **ruff 格式化** — 注意 E712 等规则，布尔比较用 `is` 而非 `==`
7. **hatchling 构建** — 如果添加 schema/ 子包，需确保 hatchling 正确包含非 .py 文件（通过 `[tool.hatch.build.targets.wheel]` 配置）

### Git 上下文

**最近提交模式：**
```
bdf17c9 Refactor code structure for improved readability and maintainability
1cdcb26 feat: 添加技术指标函数和参数注入机制的单元测试
d2765c9 Refactor code structure for improved readability and maintainability
```

**代码约定：**
- 提交消息格式：`feat: 中文描述`（Conventional Commits）
- 已有测试文件：test_context.py, test_indicators.py, test_parameters.py, test_cli.py
- Python 代码风格：ruff 格式化，PEP 8

### Project Structure Notes

**与统一项目结构的对齐：**
- `validator.py` 位置符合架构文档定义：`packages/qysp/src/qysp/validator.py` [Source: architecture.md#完整项目目录结构]
- 测试文件位置符合规范：`packages/qysp/tests/test_validator.py`
- Schema 文件需在两个位置保持同步：
  - `docs/strategy-format/qysp.schema.json` — 规范文档（权威源）
  - `packages/qysp/src/qysp/schema/qysp.schema.json` — SDK 打包副本

**与后续 Story 的关系：**
- Story 1.6（CLI 工具）：`qys validate` 子命令将直接调用 `qysp.validator.validate()`
- Story 1.7（策略模板库）：模板生成的策略必须通过 `qys validate`
- Story 3.x（回测引擎）：策略上传时使用 validator 进行完整性校验（FR-7: Web UI SHA256 验证）
- Epic 5（策略广场）：策略发布前强制校验

### References

- 元数据增强需求: [Source: epics.md#Story 1.5]
- FR-3 策略元数据: [Source: prd-qystrategy-improvement.md#FR-3]
- FR-7 Web UI SHA256 验证: [Source: prd-qystrategy-improvement.md#FR-7]
- JSON Schema 定义: [Source: docs/strategy-format/qysp.schema.json]
- 完整性校验结构: [Source: docs/strategy-format/qysp.schema.json#integrity]
- 项目目录结构: [Source: architecture.md#完整项目目录结构]
- 策略分类枚举值: [Source: architecture.md#领域 4 strategies 表扩展]
- SDK 依赖策略: [Source: architecture.md#决策 2]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

- schema 文件含 UTF-8 BOM，`_load_schema()` 使用 `utf-8-sig` 编码读取解决
- pytest-cov + Windows numpy 冲突（已知问题），使用 `--cov=qysp` 全包覆盖绕过

### Completion Notes List

- 所有 9 个 Task（含全部子任务）已完成
- 35 个单元测试全部通过，validator.py 分支覆盖率 91%
- 142 个全量测试通过，无任何回归
- ValidationError 复用 parameters.py 已有定义（方案 A），保持 SDK 异常类型统一
- schema 通过 `importlib.resources` 从 `qysp.schema` 子包加载，支持打包分发
- 现有 GoldTrend 和 GoldStepByStep 示例均通过 schema 向后兼容验证

### Change Log

- 2026-03-16: 实现 QYSP 元数据增强与 JSON Schema 验证（Story 1.5 全部任务）
- 2026-03-16: Code Review 修复 — 移除死代码、添加异常处理（BadZipFile/JSONDecodeError/KeyError）、schema 缓存、日期格式验证、integrity.files 类型校验；新增 7 个测试用例

### File List

**新增文件：**
- `packages/qysp/src/qysp/validator.py` — JSON Schema 验证 + .qys 完整性校验模块
- `packages/qysp/src/qysp/schema/__init__.py` — schema 子包初始化
- `packages/qysp/src/qysp/schema/qysp.schema.json` — SDK 打包的 schema 副本
- `packages/qysp/tests/test_validator.py` — 验证器单元测试（35 个用例）

**修改文件：**
- `docs/strategy-format/qysp.schema.json` — 添加 ui 和 backtest 可选字段，backtest 日期字段添加 pattern 约束
- `packages/qysp/src/qysp/__init__.py` — 添加 validator 公共导出
- `packages/qysp/pyproject.toml` — 添加 jsonschema>=4.0 依赖
- `uv.lock` — 自动更新（jsonschema 依赖）

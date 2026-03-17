# Story 1.6: qys CLI 命令行工具（6 个子命令）

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

作为策略开发者，
我希望使用 qys CLI 工具的 init、validate、build、backtest、import、migrate 子命令，
以便从终端管理策略开发的完整生命周期。

## Acceptance Criteria

1. 运行 `qys --help` 时，6 个子命令（init、validate、build、backtest、import、migrate）全部列出，每个附有一行中文说明
2. 运行 `qys init my-strategy --template trend-following` 时，创建包含 strategy.json、src/strategy.py、README.md 的目录结构
3. 运行 `qys validate my-strategy.qys` 时，有效包返回退出码 0；无效包返回非零退出码并输出具体字段级错误信息
4. 运行 `qys build my-strategy/` 时，生成 my-strategy.qys 压缩包，manifest 中包含正确的 SHA256
5. 运行 `qys migrate my-strategy.qys` 时，包升级至最新 schema 版本（或输出"已是最新版本"）
6. `qys backtest` 和 `qys import` 为桩实现，打印说明信息并返回退出码 0（将在 Epic 3/Epic 5 中完整集成）
7. 所有命令在 Windows 10+、macOS 12+、Ubuntu 20.04+ 上正常工作
8. `tests/test_cli.py` 单元测试分支覆盖率 ≥ 80%

## Tasks / Subtasks

- [x] Task 1: 实现 `qys init` 子命令 (AC: 2)
  - [x] 1.1 创建 `init` Click 命令，接受 `name` 参数和 `--template` 选项（默认值 `trend-following`）
  - [x] 1.2 创建目标目录 `{name}/`，内含 `strategy.json`（从内置模板生成）、`src/strategy.py`（最小策略骨架）、`README.md`
  - [x] 1.3 `strategy.json` 中 `name` 字段填充用户输入，`event_interface` 设为 `event_v1`，`parameters` 预设一个示例参数
  - [x] 1.4 `--template` 选项目前仅影响 strategy.json 中的 `ui.category` 字段值（模板文件本身在 Story 1.7 实现）
  - [x] 1.5 目标目录已存在时报错退出（非零退出码），提示 "Directory '{name}' already exists"

- [x] Task 2: 实现 `qys validate` 子命令 (AC: 3)
  - [x] 2.1 创建 `validate` Click 命令，接受 `path` 参数（.qys 文件或目录）
  - [x] 2.2 直接调用 `qysp.validator.validate(path)` 获取验证结果
  - [x] 2.3 验证通过时打印成功消息并退出码 0
  - [x] 2.4 验证失败时逐条打印错误信息（含字段名）并退出码 1
  - [x] 2.5 文件/目录不存在时打印错误并退出码 2

- [x] Task 3: 实现 `qys build` 子命令 (AC: 4)
  - [x] 3.1 创建 `build` Click 命令，接受 `source_dir` 参数和可选 `--output` 选项
  - [x] 3.2 检查 source_dir 包含 `strategy.json` 和 `src/strategy.py`
  - [x] 3.3 计算所有文件的 SHA256 哈希，写入 strategy.json 的 `integrity.files` 数组
  - [x] 3.4 将目录内容打包为 ZIP 格式 .qys 文件
  - [x] 3.5 输出文件默认名为 `{strategy_name}.qys`，可通过 `--output` 覆盖
  - [x] 3.6 打包完成后自动运行 `validate` 验证产出包的完整性

- [x] Task 4: 实现 `qys migrate` 子命令 (AC: 5)
  - [x] 4.1 创建 `migrate` Click 命令，接受 `path` 参数（.qys 文件或策略目录）
  - [x] 4.2 读取 strategy.json 的 `schema_version` 字段
  - [x] 4.3 如果已是最新版本（当前 `1.0.0`），输出"已是最新版本"并退出码 0
  - [x] 4.4 如果需要迁移，执行字段转换并更新 `schema_version`（预留迁移函数结构，当前无实际迁移逻辑）
  - [x] 4.5 迁移后输出变更摘要

- [x] Task 5: 实现 `qys backtest` 桩命令 (AC: 6)
  - [x] 5.1 创建 `backtest` Click 命令，接受 `path` 参数
  - [x] 5.2 打印说明信息："本地回测功能将在后续版本集成（Epic 3）。请使用 Web 平台提交回测任务。"
  - [x] 5.3 退出码 0

- [x] Task 6: 实现 `qys import` 桩命令 (AC: 6)
  - [x] 6.1 创建 `import_cmd` Click 命令（避免与 Python 关键字冲突），CLI 名称为 `import`
  - [x] 6.2 打印说明信息："策略导入功能将在后续版本集成（Epic 5）。请使用 Web 平台导入策略。"
  - [x] 6.3 退出码 0

- [x] Task 7: 更新 CLI 主入口并注册所有子命令 (AC: 1)
  - [x] 7.1 在 `cli/main.py` 中将 6 个子命令注册到 `cli` Click group
  - [x] 7.2 每个命令附带中文帮助说明（Click `help` 参数）
  - [x] 7.3 验证 `qys --help` 输出包含全部 6 个子命令

- [x] Task 8: 编写单元测试 (AC: 8)
  - [x] 8.1 使用 Click 的 `CliRunner` 进行测试（不依赖真实文件系统时用 `tmp_path` fixture）
  - [x] 8.2 覆盖所有 6 个子命令的正常和异常路径
  - [x] 8.3 分支覆盖率 ≥ 80%
  - [x] 8.4 全量回归测试通过

## Dev Notes

### 核心设计决策

**1. CLI 架构 — Click Group + 子命令模块化**

现有 `cli/main.py` 已定义 Click group 骨架。6 个子命令全部在同一文件中实现（文件不大，无需拆分），注册到 `cli` group：

```python
# packages/qysp/src/qysp/cli/main.py
import click
from qysp import __version__

@click.group()
@click.version_option(__version__, prog_name="qys")
def cli():
    """QYS 策略包命令行工具"""
    pass

@cli.command()
@click.argument("name")
@click.option("--template", default="trend-following",
              type=click.Choice(["trend-following", "mean-reversion", "momentum", "multi-indicator"]),
              help="策略模板类型")
def init(name, template):
    """从模板创建新策略项目"""
    ...

@cli.command()
@click.argument("path", type=click.Path(exists=True))
def validate(path):
    """验证策略包或策略目录"""
    ...

# ... 其余子命令类似
```

[Source: architecture.md#CLI 框架：Click 8.3.1]
[Source: epics.md#Story 1.6 验收标准]

**2. init 命令 — 内置最小模板**

`qys init` 不依赖 Story 1.7 的模板库，而是使用硬编码的最小模板：

- `strategy.json`：包含 name、version、schema_version、event_interface、parameters（一个示例参数）、ui.category（对应 --template 选项值）
- `src/strategy.py`：最小 event_v1 策略骨架（`def on_bar(ctx, data)` 函数签名）
- `README.md`：策略名称 + 基本说明

当 Story 1.7 实现后，`--template` 选项将从 `packages/qysp/src/qysp/templates/` 目录加载完整模板。当前阶段，所有模板类型生成相同的骨架代码，仅 `ui.category` 字段值不同。

**3. build 命令 — SHA256 完整性保证**

`qys build` 的核心流程：
1. 读取源目录下的 `strategy.json`
2. 遍历所有文件，计算 SHA256 哈希
3. 将哈希写入 `strategy.json` 的 `integrity.files` 数组
4. 将整个目录打包为 ZIP 格式（.qys 扩展名）
5. 构建完成后自动调用 `qysp.validator.validate()` 验证产出包

文件路径在 ZIP 内使用正斜杠（`src/strategy.py`），确保跨平台一致。

[Source: docs/strategy-format/qysp.schema.json#integrity]

**4. validate 命令 — 直接复用 validator 模块**

`qys validate` 是 `qysp.validator.validate()` 的 CLI 包装：
- `.qys` 文件 → 执行 schema 验证 + 完整性验证
- 目录 → 仅执行 schema 验证
- 错误信息格式化后输出到 stderr，逐条显示字段级错误

[Source: Story 1.5 已实现 validator.py — validate(), validate_schema(), validate_integrity()]

**5. migrate 命令 — 预留迁移框架**

当前 schema_version 仅有 `1.0.0`，无实际迁移逻辑。但需搭建迁移框架：
- 版本比较逻辑
- 迁移函数注册表（`MIGRATIONS = {"0.9.0->1.0.0": migrate_0_9_to_1_0}`）
- 已是最新版本时输出提示

[Source: architecture.md#版本兼容性策略 — 语义化版本控制 + 迁移工具]

**6. import 命令名称冲突处理**

Python 的 `import` 是关键字，Click 命令函数名不能用 `import`。使用 `import_cmd` 作为函数名，通过 `@cli.command("import")` 指定 CLI 名称：

```python
@cli.command("import")
@click.argument("path")
def import_cmd(path):
    """将策略包导入到平台策略库"""
    ...
```

### 技术要求

**语言与运行时：**
- Python 3.11+
- Click >= 8.3.1（已安装）

**类型注解要求：**
- 所有内部辅助函数必须有完整类型注解
- Click 命令函数参数由装饰器推断，无需额外注解
- 使用 `from __future__ import annotations` 启用延迟求值

**代码风格：**
- PEP 8 + ruff 格式化
- 函数名 `snake_case`
- Click 命令 help 字符串使用中文

**跨平台注意事项：**
- 文件路径使用 `pathlib.Path`（自动处理路径分隔符）
- ZIP 内部路径统一用正斜杠（`zipfile.write(arcname=...)` 时替换反斜杠）
- 终端输出使用 `click.echo()` 和 `click.secho()`（处理编码）
- 不依赖任何 Unix 特有命令（如 `chmod`）

### 架构合规

**必须遵循的架构约束：**

| 约束 ID | 规则 | 来源 |
|---------|------|------|
| ARCH-1 | SDK + CLI 包位于 `packages/qysp/`，使用 Click 8.3.1 | architecture.md#起点模板 |
| QYSP-FR5 | 6 个子命令：init/validate/build/backtest/import/migrate | prd-qystrategy-improvement.md#FR-5 |
| entry_point | `qys = "qysp.cli.main:cli"` | packages/qysp/pyproject.toml |
| validator | `qys validate` 直接调用 `qysp.validator.validate()` | Story 1.5 实现 |
| stubs | backtest 和 import 为桩实现 | epics.md#Story 1.6 注释 |

**禁止事项：**
- ❌ 不得修改 `context.py`（Story 1.2 核心类）
- ❌ 不得修改 `indicators.py`（Story 1.4 指标函数）
- ❌ 不得修改 `parameters.py`（Story 1.3 参数注入）
- ❌ 不得修改 `validator.py` 的公共 API 签名（Story 1.5 已稳定）
- ❌ 不得引入新的 Python 依赖（Click 和 jsonschema 已足够）
- ❌ 不得使用 `os.system()` 或 `subprocess` 调用外部命令
- ❌ 不得使用 `eval()`/`exec()` 生成策略代码

### 库与框架要求

**本 Story 使用的库：**

| 模块 | 用途 | 版本 |
|------|------|------|
| `click` | CLI 框架（group、command、argument、option） | >= 8.3.1（已安装） |
| `qysp.validator` | validate 子命令复用 | 内部模块（Story 1.5 实现） |
| `zipfile` | build 命令打包 .qys | 标准库 |
| `hashlib` | build 命令计算 SHA256 | 标准库 |
| `json` | strategy.json 读写 | 标准库 |
| `pathlib` | 路径操作 | 标准库 |
| `shutil` | init 命令复制模板文件 | 标准库 |
| `textwrap` | 内联模板文本格式化 | 标准库 |

**测试依赖：**
- `pytest >= 9.0`（已安装）
- `click.testing.CliRunner`（Click 内置测试工具）
- `pytest-cov`（已安装）

**明确不使用：**
- ❌ `argparse`（使用 Click）
- ❌ `typer`（Click 已够用，不增加依赖）
- ❌ `cookiecutter`（init 模板过于简单，不需要模板引擎）

### 文件结构要求

**本 Story 新增/修改的文件：**

```
packages/qysp/
├── src/qysp/
│   └── cli/
│       ├── __init__.py        # 无需修改（空包标记）
│       └── main.py            # 修改：添加 6 个子命令实现
└── tests/
    └── test_cli.py            # 修改：扩展为完整子命令测试
```

**文件职责边界：**
- `cli/main.py`：所有 CLI 命令定义和实现（文件估计 250-350 行，不需拆分）
- CLI 命令只做参数解析和输出格式化，业务逻辑调用 SDK 模块（validator、未来的 builder 等）
- 内联模板（init 命令用的 strategy.json/strategy.py/README.md 模板）直接在 main.py 中作为多行字符串

**不得修改的文件：**
- `packages/qysp/src/qysp/context.py`
- `packages/qysp/src/qysp/indicators.py`
- `packages/qysp/src/qysp/parameters.py`
- `packages/qysp/src/qysp/validator.py`（可调用但不修改）
- `packages/qysp/src/qysp/__init__.py`（无需添加新导出）
- `packages/qysp/pyproject.toml`（CLI 入口点已配置，无需改动）
- `backend/` 下所有文件
- `frontend/` 下所有文件

### 测试要求

**测试文件：** `packages/qysp/tests/test_cli.py`

**必须覆盖的测试场景：**

```
# 现有测试（保留）
test_help_exits_zero                — qys --help 退出码 0
test_help_contains_description      — help 包含 "QYS"
test_version_option                 — qys --version 显示 "0.1.0"

# init 子命令
test_init_creates_directory         — 创建包含 strategy.json + src/strategy.py + README.md 的目录
test_init_strategy_json_valid       — 生成的 strategy.json 通过 schema 验证
test_init_with_template_option      — --template 选项影响 ui.category 值
test_init_existing_directory_fails  — 目标目录已存在时退出码非零
test_init_default_template          — 不指定 --template 时默认使用 trend-following

# validate 子命令
test_validate_valid_directory       — 有效策略目录返回退出码 0
test_validate_invalid_directory     — 无效目录返回退出码 1 + 错误信息
test_validate_valid_qys_file        — 有效 .qys 文件返回退出码 0
test_validate_invalid_qys_file      — 无效 .qys 文件返回退出码 1

# build 子命令
test_build_creates_qys_file         — 生成 .qys 文件
test_build_integrity_valid          — 生成的 .qys 通过完整性验证
test_build_custom_output            — --output 选项指定输出路径
test_build_missing_strategy_json    — 缺少 strategy.json 时报错
test_build_missing_strategy_py      — 缺少 src/strategy.py 时报错

# migrate 子命令
test_migrate_already_latest         — 已是最新版本时输出提示
test_migrate_nonexistent_path       — 路径不存在时报错

# backtest 桩命令
test_backtest_stub_exits_zero       — 退出码 0
test_backtest_stub_shows_message    — 输出说明信息

# import 桩命令
test_import_stub_exits_zero         — 退出码 0
test_import_stub_shows_message      — 输出说明信息

# help 子命令列表
test_help_lists_all_commands        — --help 输出包含全部 6 个子命令名
```

**运行命令：**
```bash
uv run --directory packages/qysp pytest tests/test_cli.py -v
uv run --directory packages/qysp pytest tests/test_cli.py --cov=qysp.cli --cov-branch --cov-report=term-missing
```

**回归测试：**
```bash
uv run --directory packages/qysp pytest tests/ -v  # 全量测试，确保所有旧测试 + 新测试全部通过
```

### 前一个 Story 经验（Story 1.5）

**关键学习与注意事项：**

1. **pytest-cov + Windows 冲突** — Story 1.4/1.5 发现 `--cov=qysp.xxx` 在 Windows 上可能因模块多次加载报错，改用 `--cov=qysp` 全包覆盖可绕过
2. **测试运行格式** — 使用 `uv run --directory packages/qysp pytest tests/` 格式
3. **分支覆盖率 ≥ 80%** — 使用 `--cov-branch` 检查
4. **ruff 格式化** — E712 等规则，布尔比较用 `is` 而非 `==`
5. **Code Review 经验** — Story 1.4/1.5 都在 code review 中发现需添加输入验证和异常处理，CLI 命令应从一开始就做好错误处理（无效输入、文件不存在、权限不足）
6. **schema 文件加载** — schema 通过 `importlib.resources` 从 `qysp.schema` 子包加载，validator 使用 `utf-8-sig` 编码处理 BOM
7. **ValidationError 复用** — Story 1.5 确认使用 `parameters.py` 的 `ValidationError`，CLI 中捕获此异常并格式化输出

### Git 上下文

**最近提交模式：**
```
dd78c54 feat: 添加 QYSP 策略包验证器，包括 JSON Schema 验证和 .qys 完整性校验功能
8acb60d Refactor code structure for improved readability and maintainability
1cdcb26 feat: 添加技术指标函数和参数注入机制的单元测试
```

**代码约定：**
- 提交消息格式：`feat: 中文描述`（Conventional Commits）
- 已有测试文件：test_context.py, test_indicators.py, test_parameters.py, test_validator.py, test_cli.py, test_utils_time.py
- Python 代码风格：ruff 格式化，PEP 8

### Project Structure Notes

**与统一项目结构的对齐：**
- CLI 代码位置符合架构文档定义：`packages/qysp/src/qysp/cli/main.py` [Source: architecture.md#完整项目目录结构]
- 测试文件位置符合规范：`packages/qysp/tests/test_cli.py`
- pyproject.toml 入口点已配置：`qys = "qysp.cli.main:cli"` [Source: packages/qysp/pyproject.toml]

**与后续 Story 的关系：**
- Story 1.7（策略模板库）：`qys init --template` 将从 `templates/` 目录加载完整模板，当前使用内置最小模板
- Story 1.8（示例策略重写）：重写后的示例应可通过 `qys validate` 和 `qys build` 工作流
- Epic 3（回测引擎）：`qys backtest` 桩命令将被替换为真实回测逻辑
- Epic 5（策略广场）：`qys import` 桩命令将被替换为平台策略导入逻辑

### References

- CLI 工具需求: [Source: epics.md#Story 1.6]
- QYSP-FR5 CLI 6 子命令: [Source: prd-qystrategy-improvement.md#FR-5]
- CLI 框架选型: [Source: architecture.md#起点模板 — Click 8.3.1]
- 验证器模块: [Source: packages/qysp/src/qysp/validator.py — Story 1.5 实现]
- Schema 版本控制: [Source: architecture.md#版本兼容性策略]
- 项目目录结构: [Source: architecture.md#完整项目目录结构]
- CLI 入口点: [Source: packages/qysp/pyproject.toml#project.scripts]
- .qys 包格式: [Source: docs/strategy-format/qysp.schema.json#integrity]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

无调试问题。

### Completion Notes List

- 实现了全部 6 个 CLI 子命令：init、validate、build、migrate、backtest（桩）、import（桩）
- init 命令生成符合 QYSP JSON Schema 的 strategy.json，含 event_v1 接口和示例参数
- build 命令计算 SHA256 哈希写入 integrity.files，自动验证产出包
- validate 命令复用 qysp.validator.validate() 统一入口
- migrate 命令搭建迁移框架（版本比较 + 迁移注册表），当前仅 1.0 版本
- 所有命令使用 pathlib.Path 和正斜杠 ZIP 路径确保跨平台兼容
- 25 个 CLI 测试全部通过，分支覆盖率 86%（> 80% 要求）
- 全量 164 个测试回归通过，无新增依赖

### Senior Developer Review (AI)

**审查日期:** 2026-03-16
**审查者:** Claude Opus 4.6 (Adversarial Code Review)

**发现问题:** 2 High, 4 Medium, 2 Low — 全部 HIGH/MEDIUM 已自动修复

**已修复问题:**
1. **[H1] AC 5 部分未实现** — `migrate` 命令原本拒绝 .qys 文件输入，现已实现就地迁移（解包→更新 schemaVersion→重新打包）
2. **[H2] `build` rglob 包含垃圾文件** — 新增过滤逻辑，排除 `__pycache__/`、`.pyc`、`.git/`、`.DS_Store` 等
3. **[M1] 缺少 migrate 迁移路径测试** — 新增 `test_migrate_older_version_dir`，覆盖实际迁移分支
4. **[M2] 缺少 migrate .qys 文件测试** — 新增 `test_migrate_qys_already_latest` 和 `test_migrate_qys_older_version`
5. **[M3] `init` 无策略名称验证** — 新增正则验证，拒绝路径遍历和特殊字符，含 2 个新测试
6. **[M4] 脆弱的测试断言** — 简化 `test_build_missing_strategy_json` 断言逻辑

**未修复 (LOW):**
- L1: `MIGRATIONS` 类型已改为 `dict[str, Callable]`（顺手修复）
- L2: build 自动验证重复打开 ZIP — 性能微损可忽略

**测试结果:** 30 CLI 测试通过（+5 新增），169 全量测试回归通过

### Change Log

- 2026-03-16: 实现 Story 1.6 全部 8 个 Task — qys CLI 6 个子命令 + 主入口注册 + 完整单元测试
- 2026-03-16: Code Review 修复 — migrate 支持 .qys、build 过滤垃圾文件、init 名称验证、新增 5 个测试

### File List

- `packages/qysp/src/qysp/cli/main.py` — 修改：添加 6 个子命令实现 + Code Review 修复（migrate .qys 支持、build 文件过滤、init 名称验证）
- `packages/qysp/tests/test_cli.py` — 修改：扩展为 30 个测试覆盖全部子命令正常和异常路径

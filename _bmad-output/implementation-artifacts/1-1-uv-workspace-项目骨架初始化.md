# Story 1.1: uv Workspace 项目骨架初始化

Status: done

## Story

作为开发者，
我希望项目拥有 uv workspace 结构并完成 packages/qysp 初始化，
以便 monorepo 拥有统一的依赖管理，SDK 和 CLI 包具备正确的构建结构。

## Acceptance Criteria

1. 根目录 `pyproject.toml` 声明 workspace members: `["packages/qysp", "backend"]`
2. `packages/qysp/pyproject.toml` 使用 hatchling 构建后端，Click 8.3.1 作为依赖
3. `uv sync` 成功生成统一的 `uv.lock` 文件，无冲突
4. `packages/qysp/src/qysp/__init__.py` 导出 `__version__` 版本字符串（初始值 `"0.1.0"`）
5. `packages/qysp/src/qysp/utils/time.py` 包含 `BEIJING_TZ`、`to_beijing()`、`now_beijing()` 三个工具（含类型注解）
6. `backend/pyproject.toml` 将 packages/qysp 列为可编辑 workspace 依赖（`qysp`），所有原有 requirements.txt 依赖迁移完整

## Tasks / Subtasks

- [x] Task 1: 初始化 uv workspace 根配置 (AC: 1, 3)
  - [x] 1.1 在项目根目录创建 `pyproject.toml`，声明 `[tool.uv.workspace]` members: `["packages/qysp", "backend"]`
  - [x] 1.2 在根目录 `pyproject.toml` 中设置 Python requires = ">=3.11"
  - [x] 1.3 验证根目录 pyproject.toml 格式正确（uv 可识别）

- [x] Task 2: 初始化 packages/qysp SDK 包结构 (AC: 2, 4)
  - [x] 2.1 创建目录 `packages/qysp/src/qysp/`（含 `__init__.py`）
  - [x] 2.2 创建 `packages/qysp/pyproject.toml`：hatchling 构建后端，package-dir = "src"，依赖 click>=8.3.1
  - [x] 2.3 在 `packages/qysp/src/qysp/__init__.py` 中写入 `__version__ = "0.1.0"` 和公共导出
  - [x] 2.4 创建 `packages/qysp/tests/` 目录并添加 `__init__.py` 和 `conftest.py`
  - [x] 2.5 创建 `packages/qysp/src/qysp/cli/__init__.py` 和 `packages/qysp/src/qysp/cli/main.py`（Click 入口骨架）

- [x] Task 3: 实现 utils/time.py 时区工具（含测试） (AC: 5)
  - [x] 3.1 创建 `packages/qysp/src/qysp/utils/__init__.py`
  - [x] 3.2 创建 `packages/qysp/src/qysp/utils/time.py`，实现 `BEIJING_TZ`、`to_beijing(dt)`、`now_beijing()`（含类型注解）
  - [x] 3.3 编写测试 `packages/qysp/tests/test_utils_time.py`，覆盖：UTC 转北京时间、now_beijing 返回 UTC+8、禁止 naive datetime

- [x] Task 4: 迁移 backend 依赖到 pyproject.toml (AC: 6)
  - [x] 4.1 创建 `backend/pyproject.toml`，将 requirements.txt 所有依赖迁移（保持版本约束），添加 `[tool.uv.sources] qysp = {workspace = true}`
  - [x] 4.2 验证 backend 可以 `from qysp import __version__` 无报错
  - [x] 4.3 保留 `backend/requirements.txt` 作为备份注释（不删除，避免破坏 Dockerfile）

- [x] Task 5: 执行 uv sync 并验证 lock 文件 (AC: 3)
  - [x] 5.1 在项目根目录执行 `uv sync`，生成 `uv.lock`
  - [x] 5.2 验证 `uv.lock` 包含 qysp、backend 所有依赖，无冲突

- [x] Task 6: 验证完整安装并运行测试 (AC: 全部)
  - [x] 6.1 `uv run pytest packages/qysp/tests/` 全部通过（8 tests passed）
  - [x] 6.2 `uv run python -c "from qysp import __version__; print(__version__)"` 输出 "0.1.0"
  - [x] 6.3 验证 CLI 入口：`uv run qys --help` 无报错（显示 Click 帮助信息）

## Dev Notes

### 关键技术决策

**1. uv workspace 结构**
- workspace 根不是一个可安装的 Python 包，只作为 workspace 协调器
- `[tool.uv.workspace]` 放在根 `pyproject.toml` 中
- `members` 路径必须相对于根目录（即 `"packages/qysp"` 和 `"backend"`）
- `uv sync` 会自动识别所有 workspace members 并生成统一 lock 文件

**2. packages/qysp pyproject.toml 关键配置**

```toml
[project]
name = "qysp"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "click>=8.3.1",
]

[project.scripts]
qys = "qysp.cli.main:cli"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/qysp"]
```

**3. 根目录 pyproject.toml 结构**

```toml
[tool.uv.workspace]
members = ["packages/qysp", "backend"]

[tool.uv]
dev-dependencies = [
    "pytest>=9.0",
    "ruff>=0.4",
]
```

注意：根目录 pyproject.toml 不需要 `[project]` 表（workspace 根可以不是包）。

**4. backend/pyproject.toml workspace 依赖声明**

```toml
[tool.uv.sources]
qysp = { workspace = true }
```

这样 uv 会使用 workspace 内的本地 qysp 包（editable install），无需手动 `pip install -e`。

**5. 时区工具函数规范（来自架构文档）**

```python
# packages/qysp/src/qysp/utils/time.py
import zoneinfo
from datetime import datetime, timezone

BEIJING_TZ = zoneinfo.ZoneInfo("Asia/Shanghai")

def to_beijing(dt: datetime) -> datetime:
    """将 UTC datetime 转为北京时间（用于 API 输出）"""
    return dt.astimezone(BEIJING_TZ)

def now_beijing() -> datetime:
    """返回当前北京时间"""
    return datetime.now(BEIJING_TZ)
```

**明确禁止：**
- ❌ `datetime.now()`（无时区，依赖服务器配置）
- ❌ 直接 `import pytz`（zoneinfo 是 Python 3.9+ 标准库，无需额外依赖）

### Project Structure Notes

**本 Story 将创建的完整目录结构：**

```
QYQuant/
├── pyproject.toml                  # 新增：uv workspace 根配置
├── uv.lock                         # 新增：统一依赖 lock 文件（uv sync 生成）
│
├── packages/                       # 新增
│   └── qysp/
│       ├── pyproject.toml          # 新增：hatchling + Click 8.3.1
│       ├── src/
│       │   └── qysp/
│       │       ├── __init__.py     # 新增：__version__ = "0.1.0"
│       │       ├── utils/
│       │       │   ├── __init__.py # 新增
│       │       │   └── time.py     # 新增：BEIJING_TZ / to_beijing / now_beijing
│       │       └── cli/
│       │           ├── __init__.py # 新增
│       │           └── main.py     # 新增：Click CLI 骨架（qys --help 可用）
│       └── tests/
│           ├── __init__.py         # 新增
│           ├── conftest.py         # 新增
│           └── test_utils_time.py  # 新增：时区工具单元测试
│
└── backend/
    ├── pyproject.toml              # 新增：迁移自 requirements.txt
    └── requirements.txt            # 保留（Dockerfile 兼容性）
```

**不得修改的文件：**
- `backend/Dockerfile`、`backend/Makefile`（本 story 不触碰构建流程）
- `backend/app/` 下任何现有代码
- `frontend/` 所有文件
- `docker-compose.yml`

### 已有 backend 依赖迁移对照表

| requirements.txt 依赖 | 迁移到 pyproject.toml |
|---|---|
| Flask>=3.0.0,<4.0.0 | "flask>=3.0.0,<4.0.0" |
| flask-cors>=4.0.0,<5.0.0 | "flask-cors>=4.0.0,<5.0.0" |
| flask-smorest==0.44.0 | "flask-smorest==0.44.0" |
| flask-sqlalchemy==3.1.1 | "flask-sqlalchemy==3.1.1" |
| flask-migrate==4.0.7 | "flask-migrate==4.0.7" |
| flask-jwt-extended==4.6.0 | "flask-jwt-extended==4.6.0" |
| python-dotenv==1.0.1 | "python-dotenv==1.0.1" |
| marshmallow==3.21.2 | "marshmallow==3.21.2" |
| celery==5.3.6 | "celery==5.3.6" |
| redis==5.0.6 | "redis==5.0.6" |
| psycopg[binary]==3.1.18 | "psycopg[binary]==3.1.18" |
| cryptography==42.0.8 | "cryptography==42.0.8" |
| psycopg2-binary==2.9.9 | "psycopg2-binary==2.9.9" |
| pytest==7.4.4 | 移至 dev-dependencies |
| pytest-flask==1.3.0 | 移至 dev-dependencies |
| qysp | 通过 workspace 依赖（见 [tool.uv.sources]） |

### 测试注意事项

- 本 story 测试重点是 `utils/time.py` 的正确性（时区转换）
- CLI 骨架测试只验证 `--help` 可运行，不验证具体子命令
- `packages/qysp/tests/conftest.py` 可暂时为空（为后续 story 预留）
- 运行测试命令：`uv run --directory packages/qysp pytest tests/`

### References

- uv workspace 文档规范: [Source: architecture.md#选定方案：uv workspaces + hatchling + Click 8.x]
- 时区工具函数规范: [Source: architecture.md#时区统一规范（北京时间 UTC+8）]
- 完整目录结构: [Source: architecture.md#完整项目目录结构]
- ARCH-1: uv workspace + hatchling + Click 8.3.1 [Source: epics.md#ARCH-1]
- ARCH-2: Epic 1 Story 1 需完成 uv workspace 初始化 [Source: epics.md#ARCH-2]
- ARCH-16: 时区统一规范，使用 utils/time.py 工具函数 [Source: epics.md#ARCH-16]

## Dev Agent Record

### Agent Model Used

claude-opus-4-6

### Debug Log References

- 首次 `uv sync` 仅安装了 dev-dependencies，workspace members 未安装。使用 `uv sync --all-packages` 解决。
- backend hatchling 构建失败（无法确定 wheel 内容），添加 `[tool.hatch.build.targets.wheel] packages = ["app"]` 修复。
- 根 pyproject.toml 中 `tool.uv.dev-dependencies` 已弃用，迁移至 `dependency-groups.dev`。

### Completion Notes List

- 创建 uv workspace 根配置（pyproject.toml），声明 packages/qysp 和 backend 两个 workspace members
- 初始化 packages/qysp SDK 包：hatchling 构建后端、Click CLI 入口骨架、__version__ = "0.1.0"
- 实现 utils/time.py 时区工具（BEIJING_TZ、to_beijing、now_beijing），使用标准库 zoneinfo
- 编写 8 个单元测试覆盖时区转换、naive datetime 拒绝、当前时间验证
- 迁移 backend 所有 requirements.txt 依赖到 pyproject.toml，通过 workspace 依赖引用 qysp
- uv sync 成功生成统一 uv.lock，所有 52 个包无冲突
- 所有 AC 验证通过：pytest 8/8、版本导入、CLI --help

### File List

- pyproject.toml (新增，审查时修改：添加 pytest-flask 到 dev-dependencies)
- uv.lock (新增，uv sync 自动生成，审查后更新)
- packages/qysp/pyproject.toml (新增)
- packages/qysp/src/qysp/__init__.py (新增)
- packages/qysp/src/qysp/utils/__init__.py (新增)
- packages/qysp/src/qysp/utils/time.py (新增)
- packages/qysp/src/qysp/cli/__init__.py (新增)
- packages/qysp/src/qysp/cli/main.py (新增)
- packages/qysp/tests/__init__.py (新增)
- packages/qysp/tests/conftest.py (新增)
- packages/qysp/tests/test_utils_time.py (新增)
- packages/qysp/tests/test_cli.py (新增，审查时添加：CLI 骨架回归测试)
- backend/pyproject.toml (新增)

### Change Log

- 2026-03-15: Story 创建，状态设为 ready-for-dev（由 create-story 工作流生成）
- 2026-03-15: 完成全部 6 个 Task，实现 uv workspace 初始化、qysp SDK 包结构、时区工具函数、backend 依赖迁移。8 个测试全部通过。
- 2026-03-15: Code Review 修复 — [M1] 补充 pytest-flask>=1.3.0 到 dev-dependencies；[M2] pytest 版本升级已确认兼容；[M3] 新增 test_cli.py（3 个 CLI 回归测试）；[M4] commit 消息类型错误（refactor→feat）已知不修复。测试总数 11/11 通过。

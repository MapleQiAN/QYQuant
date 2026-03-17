---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
lastStep: 8
status: 'complete'
completedAt: '2026-03-14'
expandedAt: '2026-03-15'
expandScope: 'full-platform aligned with prd.md (65 FRs)'
inputDocuments:
  - _bmad-output/planning-artifacts/prd-qystrategy-improvement.md
  - docs/strategy-format/README.md
  - docs/strategy-format/qysp.schema.json
  - docs/strategy-format/examples/GoldTrend/strategy.json
  - docs/strategy-format/examples/GoldStepByStep/strategy.json
  - docs/strategy-format/examples/GoldStepByStep/src/strategy.py
workflowType: 'architecture'
project_name: 'QYQuant'
user_name: 'Serendy'
date: '2026-02-05'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

---

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**

从 PRD 分析中识别出 **11 个功能需求**，分为 4 个优先级层次：

**P0 - 核心格式改进（阻塞问题）**：
- FR-1: 定义清晰的策略接口规范（`event_v1`）
- FR-2: 实现参数注入机制，让 JSON 定义的参数在代码中可用
- FR-3: 增强策略元数据，支持 UI 展示和回测默认值

**P1 - 开发者体验（降低门槛）**：
- FR-4: Python SDK（核心类 + 技术指标函数库）
- FR-5: 命令行工具 `qys`（init、validate、build、backtest、import）
- FR-6: 策略模板库（trend-following、mean-reversion、momentum 等）
- FR-10: 重写示例策略，展示最佳实践
- FR-11: 完整文档（快速开始、API 参考、CLI 文档）

**P2 - 用户界面（扩展受众）**：
- FR-7: Web 策略导入页面（拖拽上传、解析、验证）
- FR-8: 参数配置器（动态表单、实时验证）
- FR-9: 策略浏览器（筛选、搜索、性能摘要）

**架构含义**：
- 需要设计一个灵活的参数系统，贯穿 CLI、SDK 和 Web UI
- SDK 必须是零依赖的（降低安装门槛）
- Web UI 需要分阶段交付，优先核心用户场景

**Non-Functional Requirements:**

**性能要求**：
- 参数注入开销 < 10ms（运行时几乎无感知）
- 策略验证时间 < 1s（快速反馈）
- Web 页面加载 < 2s（良好用户体验）

**兼容性要求**：
- **严格的向后兼容**：现有 .qys 文件必须继续工作
- **向前兼容（降级）**：新版本策略在旧系统上应有警告但可用
- **跨平台**：SDK 和 CLI 支持 Windows 10+、macOS 12+、Ubuntu 20.04+

**可维护性**：
- SDK 代码遵循 PEP 8 规范
- 公共 API 变更需要 deprecation 流程
- 文档与代码同步更新

**安全性**：
- 策略包在沙箱环境中执行
- 禁止文件系统访问（只读白名单）
- 参数注入经过验证和清洗

**可扩展性**：
- 支持自定义参数类型（插件机制）
- 支持多语言策略（Python 优先，预留扩展接口）
- 支持自定义策略接口版本

**架构含义**：
- 需要设计版本控制策略和迁移工具
- 沙箱执行环境需要仔细设计
- 插件机制需要在 SDK 层面预留扩展点

**Scale & Complexity:**

**项目复杂度评估**：中等

**复杂度指标分析**：
- ✅ **实时功能**：无（回测是异步的，无 WebSocket 需求）
- ✅ **多租户**：无（单用户系统）
- ❌ **监管合规**：无特定金融监管要求
- 🟡 **集成复杂度**：中等（需集成到现有 Vue 3 + Flask 系统）
- 🟡 **用户交互复杂度**：中等（从 CLI 到 Web UI，多层次体验）
- 🟢 **数据复杂度**：低（策略包是小型文件，无大数据处理）

**主要技术领域**：全栈
- 前端：Vue 3 + TypeScript
- 后端：Python 3.11 + Flask
- SDK：Python 库
- CLI：命令行工具

**预计架构组件数**：8-10 个
- Python SDK（核心类、工具函数）
- CLI 工具（5+ 子命令）
- Flask API（参数、策略、回测端点）
- Vue 3 组件（导入、配置器、浏览器）
- 策略接口层（event_v1 实现）
- 参数注入系统（抽象层）
- 验证系统（JSON Schema + 文件完整性）
- 沙箱执行环境

### Technical Constraints & Dependencies

**现有技术栈约束**：
- **前端**：Vue 3 + TypeScript + Vite（已在使用）
- **后端**：Python 3.11 + Flask（已在使用）
- **数据库**：PostgreSQL（已存在 strategies 表）

**依赖约束**：
- SDK 必须兼容 Python 3.11+
- 不能引入新的数据库（使用现有 PostgreSQL）
- Web UI 必须集成到现有 Dashboard
- 回测结果必须显示在现有 BacktestCard 组件
- 策略列表必须使用现有 RecentList 组件

**集成点**：
- 策略导入 → Dashboard 导航
- 参数配置 → 策略详情页
- 回测结果 → BacktestCard 集成
- 策略浏览 → RecentList 扩展

### Cross-Cutting Concerns Identified

**1. 参数系统（贯穿所有层次）**
- **定义层**：strategy.json 中的 parameters 字段
- **验证层**：JSON Schema 验证 + 运行时类型检查
- **注入层**：StrategyContext 参数注入机制
- **UI 层**：动态表单生成器（根据参数类型渲染控件）
- **持久化层**：参数预设保存和加载

**关键挑战**：如何设计参数抽象层，让它对 CLI、SDK 和 Web UI 都透明？

**2. 向后兼容性（核心约束）**
- Schema 版本控制（语义化版本）
- 字段变更策略（新增可选字段）
- 迁移工具（`qys migrate` 命令）
- 降级支持（新策略在旧系统上的行为）

**关键挑战**：如何在保持稳定性的同时允许重大改进？

**3. 验证机制（多层次防护）**
- **结构验证**：JSON Schema 检查必需字段
- **完整性验证**：SHA256 校验文件内容
- **参数验证**：运行时检查参数范围和类型
- **沙箱验证**：隔离执行环境，防止恶意操作

**关键挑战**：如何在不破坏用户体验的前提下提供足够的安全防护？

**4. 文档一致性（知识同步）**
- 接口规范文档
- SDK API 文档（自动生成）
- 示例代码（必须与文档一致）
- CLI 帮助文档（自动从代码生成）

**关键挑战**：如何确保文档更新与代码变更同步？

---

### Architecture Trade-offs Analysis (Cross-Functional War Room)

通过跨职能协作讨论，识别出以下关键架构权衡：

#### 决策 1: 参数注入策略

**选项对比**：

| 选项 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| **A. 打包时生成配置** | 实现简单，代码直接读取文件 | 每次改参数需重新打包 | Phase 1 快速交付 |
| **B. 运行时动态注入** | 灵活，参数可实时修改 | 需要设计 StrategyContext 接口 | Phase 2 完整体验 |

**最终决策**：**两阶段方案 + 参数抽象层**

- **Phase 1**：实现选项 A，快速验证概念
- **Phase 2**：实现选项 B，提供完整体验
- **关键技术**：设计参数抽象层 `ParameterProvider`，让策略代码不感知参数来源

**权衡**：增加短期工作量（两套实现）但降低长期风险（平滑演进）

#### 决策 2: SDK 依赖策略

**选项对比**：

| 选项 | 优点 | 缺点 | 风险 |
|------|------|------|------|
| **A. 零依赖** | 安装简单，无编译失败 | 维护成本高，性能可能差 | 测试负担重 |
| **B. 包装 ta-lib** | 成熟稳定，性能好 | 依赖 C 库，安装可能失败 | 用户流失 |
| **C. 混合方案** | 平衡依赖和功能 | API 不一致 | 维护复杂 |

**最终决策**：**零依赖 + 核心函数自实现**

- 提供 5-10 个最常用的技术指标函数（SMA、EMA、ATR、布林带等）
- 预留扩展点，允许用户选择安装 ta-lib 获得更多函数
- API 设计与业界标准保持一致，方便未来迁移

**权衡**：开发团队承担维护成本，但大幅降低用户安装门槛

#### 决策 3: Web UI 交付策略

**重新定义的用户旅程**：

经过讨论发现，用户群体需要不同的功能：
- **个人投资者（Frank）**：需要浏览和配置策略，不需要自己导入
- **策略开发者（David）**：需要导入和测试自己开发的策略

**最终决策**：**分阶段交付**

- **Phase 3A**：策略浏览 + 参数配置器（面向所有用户）
- **Phase 3B**：策略导入上传（面向高级用户）

**权衡**：延迟交付高级功能，但优先满足 80% 用户需求

#### 决策 4: 版本兼容性策略

**选项对比**：

| 选项 | 优点 | 缺点 | 适用范围 |
|------|------|------|---------|
| **A. 严格向后兼容** | 用户信任度高 | 技术债务累积 | Minor 版本 |
| **B. 破坏性变更** | 技术债务可控 | 用户需手动迁移 | Major 版本 |

**最终决策**：**语义化版本控制 + 迁移工具**

- **v1.x → v1.y**：必须向后兼容，新字段都是可选的
- **v1.x → v2.0**：允许破坏性变更，提供 `qys migrate` 工具
- 迁移工具必须提供清晰的反馈：迁移了什么？有数据丢失吗？怎么回滚？

**权衡**：长期稳定与短期进步的平衡，通过明确的版本约定管理用户预期

### New Risks Identified

通过 War Room 讨论，识别出新的风险：

1. **参数抽象层的设计复杂性**
   - 需要仔细定义 StrategyContext 接口
   - 缓解措施：创建接口设计文档，提供多个示例

2. **SDK 维护负担**
   - 自实现技术指标函数需要持续测试和优化
   - 缓解措施：建立自动化测试，定期性能基准测试

3. **Web UI 的用户旅程不清晰**
   - 不同用户群体需要不同功能
   - 缓解措施：绘制详细的用户旅程图，明确 Phase 边界

### Action Items

- [ ] 在架构文档中明确参数抽象层的接口设计
- [ ] 定义 SDK 的最小功能集（MVP）：核心类 + 5-10 个技术指标函数
- [ ] 绘制用户旅程图，明确 Phase 3A 和 3B 的功能边界
- [ ] 制定版本兼容性测试策略和迁移流程

---

## 起点模板评估

### 主要技术领域

在现有 Flask + Vue 3 monorepo 中新增 Python SDK + CLI 工具包。
非绿地项目，不使用外部脚手架，采用标准 Python 包结构。

Python 是本项目 SDK 和 CLI 的最优选择：策略执行环境决定了技术选型——策略代码本身是 Python，SDK 必须提供运行时支持（StrategyContext、技术指标），CLI 需直接调用 SDK，使用其他语言会引入不必要的跨语言桥接复杂度。

### 选项对比

| 选项 | 优点 | 缺点 |
|------|------|------|
| **A. uv workspaces** | 统一依赖管理，速度快，官方推荐 | 团队需学习 uv |
| **B. pip + 各自 pyproject.toml** | 简单，无新工具依赖 | 依赖版本不统一，editable install 需手动管理 |
| **C. Poetry** | 成熟稳定 | 比 uv 慢，配置复杂 |

### 选定方案：uv workspaces + hatchling + Click 8.x

**选定理由**：uv 是 2025/2026 年 Python 官方推荐工具链，统一 lock 文件管理所有包依赖；hatchling 构建后端对纯 Python 包最友好，零配置；Click 8.3.1 是简单直接的 CLI 框架首选，与策略执行代码同包，无需跨语言桥接。

**初始化命令**：

```bash
# 工作区根目录
uv init --workspace

# SDK 包
uv init packages/qysp --lib

# backend 注册为 workspace 成员并依赖本地 SDK
uv add --workspace qysp
```

**新增目录结构**：

```
QYQuant/
├── pyproject.toml              # workspace 根配置
├── uv.lock                     # 统一 lock 文件
├── backend/
│   └── pyproject.toml          # 迁移自 requirements.txt
├── frontend/                   # 不变
└── packages/
    └── qysp/
        ├── pyproject.toml      # SDK + CLI 配置
        ├── src/
        │   └── qysp/
        │       ├── __init__.py
        │       ├── context.py       # StrategyContext + ParameterProvider
        │       ├── indicators.py    # 技术指标函数（SMA、EMA、ATR 等）
        │       ├── validator.py     # JSON Schema 验证
        │       └── cli/
        │           ├── __init__.py
        │           └── main.py      # Click CLI 入口（qys 命令）
        └── tests/
```

### 起点模板确立的架构决策

**语言运行时**：Python 3.11+，pyproject.toml (PEP 621)

**构建后端**：hatchling（纯 Python 包，零配置，PEP 621 合规）

**包管理**：uv workspaces（统一 lock 文件，backend 可通过 workspace 依赖本地 qysp 包）

**CLI 框架**：Click 8.3.1（与 SDK 同包，直接调用，无跨语言开销）

**代码风格**：ruff（linter + formatter，替代 black + flake8，统一工具链）

**测试框架**：pytest 9.x

**包安装模式**：editable install（开发时 `uv pip install -e packages/qysp`，修改立即生效）

**说明**：项目初始化（创建目录结构、配置 pyproject.toml、uv workspace 设置）应作为实现阶段的第一个 story。

---

## 核心架构决策

### 决策优先级分析

**阻塞型决策（实现前必须确定）：**
- 沙箱执行方案：Firecracker microVM（分阶段）
- API 版本策略：/api/v1/ 前缀
- 参数预设存储：独立表结构

**重要决策（显著影响架构）：**
- 数据库扩展：新增 strategy_parameter_presets 表
- 安全边界：明确排除 RestrictedPython 和纯 Docker

**推迟决策（MVP 后）：**
- 自建 Firecracker 编排层（Phase 2）
- API 限流策略（商用上线前）

### 数据架构

**策略参数预设存储**
- 决策：新增 `strategy_parameter_presets` 表
- 理由：支持单策略多套预设（如"保守"/"激进"），商用多用户场景下结构更清晰，迁移成本低
- 表结构要点：`id`, `strategy_id`（FK）, `name`, `parameters`（JSONB）, `created_at`, `user_id`
- 影响组件：Flask API、参数配置器 Vue 组件、PostgreSQL

**数据库迁移方案**
- 使用 Flask-Migrate（已有 migrations/ 目录）
- 新增字段均为可选，保持向后兼容

### 安全与沙箱执行

**策略代码执行隔离**
- 决策：Firecracker microVM（分阶段演进）
- Phase 1（MVP）：E2B Cloud SDK（托管 Firecracker，80ms 启动）
- Phase 2（规模化）：自建 Firecracker 编排层
- 明确排除：
  - ~~RestrictedPython~~（CVE-2025-22153 等多个高危漏洞）
  - ~~Docker 单独~~（共享内核，不足以隔离多租户恶意代码）
- 理由：商用 SaaS 多租户唯一达标的安全边界，AWS Lambda / Google Cloud Run 均采用同等方案
- 影响组件：回测执行服务、Flask API、沙箱管理层

### API 与通信模式

**API 设计风格**
- 决策：RESTful 资源风格，统一 `/api/v1/` 前缀
- 示例端点：
  - `GET  /api/v1/strategies`
  - `GET  /api/v1/strategies/:id/parameters`
  - `POST /api/v1/strategies/:id/backtest`
  - `GET  /api/v1/strategies/:id/presets`
  - `POST /api/v1/strategies/:id/presets`
- 理由：版本前缀为未来 API 开放和破坏性变更预留空间
- Flask 组织方式：按资源分蓝图（`strategies_bp`, `backtest_bp`, `presets_bp`）

**错误处理标准**
- 统一错误响应格式：`{"error": {"code": "...", "message": "...", "details": {...}}}`
- HTTP 状态码语义化（400/401/403/404/422/500）

### 前端架构

**状态管理**（沿用现有）
- Pinia stores（已有，不引入新方案）
- 新增：`useStrategyStore`、`useBacktestStore`、`usePresetsStore`

**组件策略**
- 新增组件集成到现有 Dashboard 导航
- 回测结果复用现有 BacktestCard 组件
- 策略列表复用现有 RecentList 组件

### 决策影响分析

**实现顺序建议：**
1. uv workspace + packages/qysp 初始化
2. strategy_parameter_presets 表 migration
3. Flask 蓝图结构搭建（/api/v1/）
4. E2B Cloud SDK 集成（沙箱执行）
5. SDK 核心类（StrategyContext、ParameterProvider）
6. CLI 工具（Click，qys 命令）
7. Vue 组件（参数配置器、策略浏览器）

**跨组件依赖：**
- ParameterProvider → Flask API → Vue 动态表单（三层联动）
- E2B 沙箱 → 回测 API → BacktestCard（执行链路）
- qysp SDK → CLI → Flask（本地开发到云端的一致性）

---

## 实现模式与一致性规则

### 识别出的潜在冲突点：8 个领域

### 命名规范

**数据库命名（PostgreSQL）：**
- 表名：`snake_case` 复数（`strategies`, `strategy_parameter_presets`）
- 列名：`snake_case`（`strategy_id`, `created_at`, `user_id`）
- 外键：`{referenced_table_singular}_id`（`strategy_id`）
- 索引：`idx_{table}_{column}`（`idx_strategies_user_id`）

**API JSON 字段：**
- 后端返回：`snake_case`（`strategy_id`, `created_at`）
- 前端接收后映射为 `camelCase`（`strategyId`, `createdAt`）

**Python 代码（Flask + SDK）：**
- 函数/变量/模块：`snake_case`（`get_strategy`, `strategy_id`）
- 类名：`PascalCase`（`StrategyContext`, `ParameterProvider`）
- 常量：`UPPER_SNAKE_CASE`（`BEIJING_TZ`, `MAX_BACKTEST_DAYS`）
- 私有方法：`_leading_underscore`

**Vue 前端代码：**
- 组件文件：`PascalCase.vue`（`StrategyCard.vue`, `BacktestResult.vue`）
- 组件内变量/函数：`camelCase`（`strategyId`, `isLoading`）
- Pinia store：`use{Name}Store`（`useStrategyStore`）
- CSS 类名：`kebab-case`（`strategy-card`, `param-input`）

### 格式规范

**API 成功响应：**
```json
{
  "data": { ... },
  "meta": { "total": 100, "page": 1 }
}
```

**API 错误响应：**
```json
{
  "error": {
    "code": "STRATEGY_NOT_FOUND",
    "message": "策略不存在",
    "details": {}
  }
}
```

**时区统一规范（北京时间 UTC+8）：**

| 层次 | 规则 |
|------|------|
| 数据库 | `TIMESTAMP WITH TIME ZONE`，存储 UTC |
| Flask 内部 | 全程 UTC，使用 `datetime.now(timezone.utc)` |
| API 响应 | ISO 8601 带偏移：`"2026-03-14T18:00:00+08:00"` |
| Vue 前端 | 直接展示 API 返回的北京时间 |
| CLI 输出 | 统一转为北京时间显示 |

**必须使用的工具函数（`packages/qysp/src/qysp/utils/time.py` 及 `backend/app/utils/time.py`）：**
```python
import zoneinfo
from datetime import datetime, timezone

BEIJING_TZ = zoneinfo.ZoneInfo("Asia/Shanghai")

def to_beijing(dt: datetime) -> datetime:
    """将 UTC datetime 转为北京时间（用于 API 输出）"""
    return dt.astimezone(BEIJING_TZ)

def now_beijing() -> datetime:
    """当前北京时间"""
    return datetime.now(BEIJING_TZ)
```

**明确禁止：**
- ❌ `datetime.now()`（无时区，行为依赖服务器配置）
- ❌ 数据库使用 `TIMESTAMP`（不带时区）
- ❌ 前端使用 `new Date().toLocaleDateString()`（依赖浏览器本地时区）
- ❌ API 返回纯时间戳整数（不含时区信息）

### 结构规范

**测试文件位置：**
- Python（SDK/Flask）：`tests/` 目录，镜像 src 结构
  （`src/qysp/context.py` → `tests/test_context.py`）
- Vue：组件同目录 co-located（`StrategyCard.vue` + `StrategyCard.test.ts`）

**Flask 蓝图组织：**
```
backend/app/
├── blueprints/
│   ├── strategies.py   # /api/v1/strategies
│   ├── backtest.py     # /api/v1/strategies/:id/backtest
│   └── presets.py      # /api/v1/strategies/:id/presets
└── utils/
    └── time.py         # 时区工具函数
```

### 流程规范

**加载状态（Vue）：**
- 使用 `isLoading: boolean` / `isSubmitting: boolean`
- 禁止用字符串枚举（`loading: 'idle' | 'loading'`）
- 全局加载用 Pinia store，组件级加载用 `ref(false)`

**错误处理（Flask）：**
- 统一在 `app/__init__.py` 注册 `@app.errorhandler`
- 禁止在每个路由内各自 try/catch 返回不同格式

**参数验证时机：**
- 前端：用户输入时实时验证（提示友好）
- 后端：API 入口处强制验证（安全兜底）
- SDK：运行时执行前验证（防止策略崩溃）

### 强制执行指南

**所有 AI 代理必须：**
- 数据库时间列使用 `TIMESTAMP WITH TIME ZONE`
- Python 时间操作通过 `qysp.utils.time` / `app.utils.time` 模块
- API 响应遵循统一的 `data` / `error` wrapper 格式
- 新增路由遵循 `/api/v1/` 前缀和蓝图结构
- 命名遵循各层 `snake_case` / `camelCase` / `PascalCase` 规则

**反模式（Anti-patterns）：**
- ❌ 路由内直接返回裸 dict，不包 `{"data": ...}`
- ❌ 数据库存字符串时间（`"2026-03-14"`）或时间戳整数
- ❌ Vue 组件直接调用 `fetch()`，绕过 Pinia store
- ❌ SDK 函数依赖全局状态或单例

---

## 项目结构与边界

### 完整项目目录结构

```
QYQuant/
├── pyproject.toml                  # uv workspace 根配置
├── uv.lock                         # 统一依赖 lock 文件
├── docker-compose.yml              # 已有，保留
├── deploy.sh / deploy.ps1          # 已有，保留
├── .github/
│   └── workflows/
│       └── ci.yml                  # CI：lint + test（ruff + pytest）
│
├── packages/                       # 新增：Python 包工作区
│   └── qysp/                       # SDK + CLI 包
│       ├── pyproject.toml          # hatchling 构建，Click CLI 入口
│       ├── src/
│       │   └── qysp/
│       │       ├── __init__.py     # 版本号、公共导出
│       │       ├── context.py      # StrategyContext、ParameterProvider
│       │       ├── indicators.py   # SMA、EMA、ATR、布林带等
│       │       ├── validator.py    # JSON Schema 验证、SHA256 校验
│       │       ├── sandbox.py      # E2B Cloud SDK 封装（沙箱执行）
│       │       ├── utils/
│       │       │   └── time.py     # BEIJING_TZ、to_beijing()、now_beijing()
│       │       └── cli/
│       │           ├── __init__.py
│       │           └── main.py     # Click 入口：qys init/validate/build/backtest
│       └── tests/
│           ├── test_context.py
│           ├── test_indicators.py
│           ├── test_validator.py
│           └── test_cli.py
│
├── backend/                        # 已有，扩展
│   ├── pyproject.toml              # 迁移自 requirements.txt，依赖 workspace qysp
│   ├── Dockerfile / Makefile       # 已有，保留
│   ├── migrations/                 # 已有，新增 strategy_parameter_presets
│   ├── app/
│   │   ├── __init__.py             # Flask app factory，注册蓝图和 errorhandler
│   │   ├── blueprints/             # 新增：按资源分蓝图
│   │   │   ├── strategies.py       # GET/POST /api/v1/strategies
│   │   │   ├── backtest.py         # POST /api/v1/strategies/:id/backtest
│   │   │   └── presets.py          # GET/POST /api/v1/strategies/:id/presets
│   │   ├── models/
│   │   │   ├── strategy.py         # 已有，保留
│   │   │   └── preset.py           # 新增：StrategyParameterPreset 模型
│   │   └── utils/
│   │       └── time.py             # 时区工具（与 qysp/utils/time.py 同源）
│   └── tests/
│       ├── test_strategies_api.py
│       ├── test_backtest_api.py
│       └── test_presets_api.py
│
└── frontend/                       # 已有，扩展
    └── src/
        ├── stores/                 # 已有
        │   ├── useStrategyStore.ts # 新增
        │   ├── useBacktestStore.ts # 新增
        │   └── usePresetsStore.ts  # 新增
        ├── views/                  # 已有
        │   ├── StrategyBrowser.vue     # 新增（FR-9）
        │   └── StrategyDetail.vue      # 新增（FR-8 参数配置器）
        └── components/             # 已有
            ├── strategy/
            │   ├── StrategyCard.vue        # 新增
            │   ├── StrategyCard.test.ts
            │   ├── ParameterForm.vue       # 新增（FR-8 动态表单）
            │   ├── ParameterForm.test.ts
            │   └── StrategyImport.vue      # 新增（FR-7，Phase 3B）
            └── backtest/
                ├── BacktestResult.vue      # 扩展现有 BacktestCard
                └── BacktestResult.test.ts

# 验证阶段补充（FR-5 / FR-6 / FR-11 缺口修复）
# packages/qysp/src/qysp/ 补充：
#   ├── templates/
#   │   ├── trend_following/    # FR-6 策略模板
#   │   ├── mean_reversion/
#   │   └── momentum/
#   └── cli/main.py 包含完整 5 个命令：init / validate / build / backtest / import / migrate

# docs/ 补充（FR-11）：
#   ├── quickstart.md
#   ├── api-reference.md
#   ├── cli-reference.md        # 由 Click 自动生成
#   └── strategy-format/        # 已有
```

### 架构边界

**API 边界（Flask → 外部）：**
- 入口：所有请求经 `/api/v1/` 前缀路由到对应蓝图
- 认证边界：现有认证机制，本期不变
- 沙箱边界：回测请求经 `sandbox.py` 转发至 E2B Cloud，结果异步返回

**组件边界（Vue）：**
- Pinia store 是唯一数据源，组件不直接调用 API
- `ParameterForm` 从 `useStrategyStore` 读取参数定义，写入 `usePresetsStore`
- `BacktestResult` 订阅 `useBacktestStore`，只读

**数据边界（PostgreSQL）：**
- `strategies` 表：已有，不修改结构
- `strategy_parameter_presets` 表：新增，关联 `strategies.id`
- 所有时间列：`TIMESTAMP WITH TIME ZONE`

### 需求到结构的映射

| 需求 | 实现位置 |
|------|---------|
| FR-1 event_v1 接口规范 | `packages/qysp/src/qysp/context.py` |
| FR-2 参数注入 | `qysp/context.py` → `ParameterProvider` |
| FR-3 策略元数据 | `qysp/validator.py` + `backend/models/strategy.py` |
| FR-4 Python SDK | `packages/qysp/` 整体 |
| FR-5 CLI 工具 | `packages/qysp/src/qysp/cli/main.py` |
| FR-6 策略模板库 | `packages/qysp/src/qysp/templates/`（后续添加） |
| FR-7 策略导入页面 | `frontend/components/strategy/StrategyImport.vue` |
| FR-8 参数配置器 | `frontend/components/strategy/ParameterForm.vue` |
| FR-9 策略浏览器 | `frontend/views/StrategyBrowser.vue` |
| FR-10 示例策略 | `docs/strategy-format/examples/`（更新） |
| 沙箱执行 | `packages/qysp/src/qysp/sandbox.py` + E2B Cloud |
| 时区统一 | `qysp/utils/time.py` + `backend/app/utils/time.py` |

### 数据流

```
用户（浏览器）
  → Vue 组件 → Pinia Store → fetch(/api/v1/...)
  → Flask 蓝图 → 业务逻辑
  → [回测] qysp.sandbox → E2B Cloud → Firecracker microVM
                                      → strategy.py 执行
                                      → 返回结果
  → PostgreSQL（策略/预设持久化）
```

---

## 架构验证结果

### 一致性验证 ✅

**技术决策兼容性：**
- uv workspaces + Python 3.11 + hatchling + Click 8.3.1 — 完全兼容
- Flask 蓝图 + PostgreSQL JSONB + Flask-Migrate — 标准组合，无冲突
- Vue 3 + Pinia + Vite — 已验证的现有组合
- E2B Cloud（Firecracker）通过 HTTP API 调用，与 Flask 无耦合冲突
- 时区链路：DB 存 UTC → Flask 转北京时间 → API 输出 ISO 8601+08:00 → Vue 直展示，链路完整

**模式一致性：** 全部 8 个命名/格式/流程规范均与技术栈对齐 ✅

**结构对齐：** 项目结构完整支持所有架构决策，边界清晰 ✅

### 需求覆盖验证 ✅

**功能需求覆盖（11/11）：**

| 需求 | 覆盖位置 | 状态 |
|------|---------|------|
| FR-1 event_v1 接口规范 | `qysp/context.py` | ✅ |
| FR-2 参数注入机制 | `qysp/context.py` ParameterProvider | ✅ |
| FR-3 策略元数据增强 | `qysp/validator.py` + `models/strategy.py` | ✅ |
| FR-4 Python SDK | `packages/qysp/` 整体 | ✅ |
| FR-5 CLI 工具（6 命令） | `qysp/cli/main.py`：init/validate/build/backtest/import/migrate | ✅ |
| FR-6 策略模板库 | `qysp/templates/trend_following/` 等 | ✅ |
| FR-7 Web 策略导入 | `StrategyImport.vue`（Phase 3B） | ✅ |
| FR-8 参数配置器 | `ParameterForm.vue` + `/api/v1/strategies/:id/parameters` | ✅ |
| FR-9 策略浏览器 | `StrategyBrowser.vue` + `/api/v1/strategies` | ✅ |
| FR-10 示例策略重写 | `docs/strategy-format/examples/`（更新） | ✅ |
| FR-11 完整文档 | `docs/quickstart.md` + `api-reference.md` + `cli-reference.md` | ✅ |

**非功能需求覆盖：**
- 性能：参数注入在进程内（< 1ms），验证走 JSON Schema（< 100ms） ✅
- 安全：E2B Firecracker 硬件级隔离，明确排除 RestrictedPython ✅
- 向后兼容：语义化版本 + `qys migrate` 迁移工具 ✅
- 跨平台：uv + Python 支持 Windows/macOS/Linux ✅
- 时区：统一北京时间方案，工具函数强制使用 ✅

### 实现就绪性验证 ✅

**决策完整性：** 所有关键决策均有版本号和理由，技术栈完整指定 ✅

**结构完整性：** 目录树具体到文件级别，所有 FR 有明确映射位置 ✅

**模式完整性：** 8 个冲突领域全部定义，含正例和反模式 ✅

### 缺口分析（验证阶段已修复）

验证过程识别并修复了 3 个缺口：

1. **FR-5 CLI 缺少 `import` 和 `migrate` 命令** → 已补充至 `cli/main.py` 命令列表
2. **FR-6 模板库目录未定义** → 已补充 `qysp/templates/` 子结构
3. **FR-11 文档目录缺失** → 已补充 `docs/` 文档规划

### 架构完整性清单

**✅ 需求分析**
- [x] 项目上下文深度分析（11 个 FR，4 个 NFR 类别）
- [x] 规模与复杂度评估（中等，全栈）
- [x] 技术约束与集成点识别
- [x] 横切关注点映射（参数系统、兼容性、验证、文档）

**✅ 架构决策**
- [x] 技术栈完整指定（含版本号）
- [x] 沙箱执行方案（Firecracker 分阶段）
- [x] 数据架构（PostgreSQL + JSONB 预设表）
- [x] API 设计（RESTful /api/v1/）
- [x] 时区统一方案（UTC 存储，北京时间输出）

**✅ 实现模式**
- [x] 命名规范（DB/API/Python/Vue 四层）
- [x] 格式规范（响应 wrapper、时区、日期）
- [x] 结构规范（测试位置、蓝图组织）
- [x] 流程规范（加载状态、错误处理、验证时机）

**✅ 项目结构**
- [x] 完整目录树（含新增和已有文件）
- [x] 边界定义（API、组件、数据）
- [x] 需求到结构映射表（11 个 FR 全覆盖）
- [x] 数据流图

### 架构就绪性评估

**总体状态：可进入实现阶段**

**置信度：高** — 所有需求有明确架构支撑，技术决策经过调研验证，模式规则覆盖主要冲突点

**核心优势：**
- 在现有 monorepo 上平滑扩展，无破坏性变更
- 商用级安全方案（Firecracker）为规模化预留空间
- 时区统一方案从架构层面消除隐患
- 参数抽象层（ParameterProvider）支持 CLI/SDK/Web 三层一致性

**未来可增强方向：**
- Phase 2 自建 Firecracker 编排层
- API 限流与认证增强（商用上线前）
- 多语言策略支持（预留扩展点）

### 实现交接指南

**AI 代理首要任务：**
```bash
# 第一步：初始化 uv workspace
uv init --workspace
uv init packages/qysp --lib
```

**实现优先级：**
1. uv workspace + packages/qysp 目录结构
2. `strategy_parameter_presets` 表 migration
3. Flask 蓝图结构（/api/v1/）
4. E2B Cloud SDK 集成
5. SDK 核心类（StrategyContext、ParameterProvider）
6. CLI 工具（6 个子命令）
7. Vue 组件（ParameterForm、StrategyBrowser）

---

## 平台级架构扩展（与 prd.md 全量 65 FRs 对齐）

> 本章节于 2026-03-15 补充，将架构范围从 QYSP 格式改进扩展至完整 QYQuant 平台。

### 领域 1：用户认证系统（FR1-6）

**认证方案：JWT + Refresh Token 双令牌**
- Access Token：有效期 15 分钟，存储于内存（不存 localStorage，防 XSS）
- Refresh Token：有效期 30 天，存储于 HttpOnly Cookie
- 手机号登录：短信验证码（阿里云 SMS / 腾讯云 SMS），验证码存 Redis，TTL 5 分钟，60 秒内同号不可重发
- 密码存储：bcrypt，cost factor ≥ 12（NFR12 已确定）
- Token 吊销：Refresh Token 黑名单存 Redis（用户主动登出或修改密码时写入）

**新增数据表：**
```sql
users (
  id, phone, password_hash, nickname, avatar_url,
  role ENUM('user', 'admin'),
  plan_level ENUM('free', 'lite', 'pro', 'expert') DEFAULT 'free',
  created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ
)

refresh_tokens (
  id, user_id, token_hash, expires_at, revoked_at, created_at TIMESTAMPTZ
)
```

**新增蓝图：** `backend/app/blueprints/auth.py` → `/api/v1/auth/`
- `POST /api/v1/auth/send-code` — 发送短信验证码
- `POST /api/v1/auth/login` — 验证码登录，返回 Access Token + 设置 Refresh Cookie
- `POST /api/v1/auth/refresh` — 刷新 Access Token
- `POST /api/v1/auth/logout` — 吊销 Refresh Token

### 领域 2：回测引擎架构（FR10-24）

**任务队列：Celery + Redis**
- Broker：Redis（与 Refresh Token 黑名单共用同一 Redis 实例，不同 DB 编号）
- Worker：独立进程，可水平扩展（NFR16：15 分钟内扩容至 2 倍）
- 监控：Flower（Celery 可视化监控），管理后台集成任务状态查询
- 并发限制：MVP 最多 10 个任务同时执行（`CELERYD_CONCURRENCY=10`，可配置）

**回测执行流程：**
```
用户提交 → Flask API 验证额度 → 创建 backtest_jobs 记录（pending）
→ Celery 任务入队 → Worker 拉取任务
→ 从 PostgreSQL 解密策略代码 → 传入 E2B Cloud 沙箱
→ E2B 执行 → 返回结果 → Worker 存储结果
→ 更新 backtest_jobs（completed/failed）→ 前端轮询获取结果
```

**额度扣减时机：** 任务**开始执行**时扣减（Worker 侧），避免队列积压虚耗

**新增数据表：**
```sql
backtest_jobs (
  id, user_id, strategy_id, status ENUM('pending','running','completed','failed','timeout'),
  params JSONB,               -- 回测参数（标的、时间区间）
  result_summary JSONB,       -- 11 项摘要指标
  result_storage_key TEXT,    -- 对象存储路径（完整 Equity Curve）
  error_message TEXT,
  started_at TIMESTAMPTZ, completed_at TIMESTAMPTZ, created_at TIMESTAMPTZ
)

user_quota (
  user_id, plan_level, used_count INT DEFAULT 0,
  reset_at TIMESTAMPTZ        -- 每月1日重置
)
```

**结果存储（混合方案）：**
- `backtest_jobs.result_summary`（JSONB）：11 项摘要指标，供列表页直接查询
- 对象存储（MinIO 自托管 / 阿里云 OSS）：完整 Equity Curve 时序数据，按 `job_id` 存 JSON 文件
- 理由：摘要数据 < 10KB 直接存 PG，Equity Curve 序列可达数百 KB 存对象存储

**新增蓝图：** `backend/app/blueprints/backtest.py` → `/api/v1/backtest/`

### 领域 3：历史数据缓存层（FR15-16，NFR7）

**方案：PostgreSQL 时序缓存表**
```sql
market_data_cache (
  symbol VARCHAR(20),
  trade_date DATE,
  open NUMERIC, high NUMERIC, low NUMERIC, close NUMERIC, volume BIGINT,
  source VARCHAR(20) DEFAULT 'joinquant',
  cached_at TIMESTAMPTZ,
  PRIMARY KEY (symbol, trade_date)
)
```
- 查询时先检查缓存，命中直接返回（目标 ≥ 90%，NFR7）
- 缓存未命中：调用聚宽 JQData API → 存入缓存 → 返回数据
- 聚宽 API 不可用时：返回已缓存数据 + 展示"数据范围提示"（≤3秒响应，NFR9）
- 不使用 Redis 缓存行情（体积大，冷数据多，PG 已足够）

### 领域 4：策略代码加密存储（NFR10-11）

**方案：AES-256-GCM + 密钥分离**
- 密文存 PostgreSQL `strategies.code_encrypted BYTEA`
- 加密密钥存环境变量 `STRATEGY_ENCRYPT_KEY`，生产环境用阿里云 KMS
- 执行流程：Flask 解密 → 明文传入 E2B 沙箱 → 执行完毕沙箱销毁，明文不落盘
- `.qys` 原始包：存对象存储，路径做 UUID 混淆，不暴露原始文件名
- `strategies.code_hash`：SHA256 存 DB，用于完整性校验（FR7 上传验证）

**strategies 表扩展：**
```sql
ALTER TABLE strategies ADD COLUMN
  title VARCHAR(200),
  description TEXT,
  tags TEXT[],
  category ENUM('trend-following','mean-reversion','momentum','multi-indicator','other'),
  is_public BOOLEAN DEFAULT false,
  is_verified BOOLEAN DEFAULT false,       -- 平台验证徽章（FR27）
  review_status ENUM('pending','approved','rejected') DEFAULT 'pending',
  display_metrics JSONB,                   -- 展示用指标（FR32）
  code_encrypted BYTEA,
  code_hash VARCHAR(64),
  storage_key TEXT,                        -- 对象存储路径
  author_id INTEGER REFERENCES users(id)
```

### 领域 5：策略广场 & 社区（FR25-39）

**新增数据表：**
```sql
posts (
  id, user_id, strategy_id NULLABLE,
  content TEXT, likes_count INT DEFAULT 0,
  comments_count INT DEFAULT 0,
  created_at TIMESTAMPTZ
)

post_interactions (
  user_id, post_id,
  type ENUM('like','collect'),
  created_at TIMESTAMPTZ,
  UNIQUE (user_id, post_id, type)
)

comments (
  id, post_id, user_id, content TEXT, created_at TIMESTAMPTZ
)
```

**搜索 & 筛选（FR61-62）：**
- 关键词搜索：PostgreSQL `tsvector` + `zhparser` 扩展（中文分词）
- 筛选：标准 SQL WHERE（category / tags / is_verified），加复合索引
- 理由：MVP 数据量 < 1000 策略，PG 全文搜索完全够用，不引入 Elasticsearch

**新增蓝图：**
- `backend/app/blueprints/marketplace.py` → `/api/v1/marketplace/`
- `backend/app/blueprints/community.py` → `/api/v1/posts/`

### 领域 6：模拟托管 & 实时推送（FR40-48）

**机器人调度：Celery Beat**
- Celery Beat 定时任务：每个交易日收盘后（16:00 北京时间）触发所有 `status=active` 机器人执行
- 每个机器人：读取最新行情 → 执行策略逻辑（通过 E2B） → 更新持仓和收益记录

**实时推送：Server-Sent Events (SSE)**
- 选择理由：模拟托管为准实时（非高频），SSE 单向推送足够，零新依赖
- 端点：`GET /api/v1/simulation/:bot_id/stream`（SSE 长连接）
- 触发时机：机器人执行完毕后推送最新持仓/收益数据

**新增数据表：**
```sql
simulation_bots (
  id, user_id, strategy_id,
  initial_capital NUMERIC,
  status ENUM('active','paused','stopped'),
  created_at TIMESTAMPTZ
)

simulation_positions (
  bot_id, symbol VARCHAR(20),
  quantity NUMERIC, avg_cost NUMERIC,
  updated_at TIMESTAMPTZ,
  PRIMARY KEY (bot_id, symbol)
)

simulation_records (
  id, bot_id, trade_date DATE,
  equity NUMERIC, cash NUMERIC, daily_return NUMERIC,
  created_at TIMESTAMPTZ
)
```

**槽位限制：** 查询 `COUNT(*) WHERE user_id=? AND status='active'`，对比套餐限额
**免责提示（FR46）：** `users.sim_disclaimer_accepted BOOLEAN`，首次进入检查

**新增蓝图：** `backend/app/blueprints/simulation.py` → `/api/v1/simulation/`

### 领域 7：支付 & 订阅系统（FR4-5，FR22-23）

**支付集成：**
- 微信支付官方 SDK（`wechatpayv3`）+ 支付宝官方 SDK（`alipay-sdk-python`）
- Webhook 端点：`POST /api/v1/payments/webhook/wechat` 和 `/alipay`
- 支付回调 → 更新 `subscriptions` 表 → 更新 `user_quota` → 发站内通知

**新增数据表：**
```sql
subscriptions (
  id, user_id,
  plan_level ENUM('free','lite','pro','expert'),
  starts_at TIMESTAMPTZ, ends_at TIMESTAMPTZ,
  status ENUM('active','expired','cancelled'),
  payment_provider ENUM('wechat','alipay'),
  created_at TIMESTAMPTZ
)

payment_orders (
  id, user_id, plan_level, amount NUMERIC,
  provider, provider_order_id,
  status ENUM('pending','paid','refunded'),
  created_at TIMESTAMPTZ
)
```

**额度重置：** Celery Beat 每月1日 00:00 北京时间执行，重置 `user_quota.used_count = 0`

**新增蓝图：** `backend/app/blueprints/payments.py` → `/api/v1/payments/`

### 领域 8：管理后台（FR49-56）

**方案：复用 Vue 3 + 路由守卫，不新建独立前端**
- `/admin/*` 路由组，`router.beforeEach` 检查 `user.role === 'admin'`
- 管理 API：`/api/v1/admin/` 蓝图，Flask 装饰器 `@require_admin`

**功能模块：**
- 策略审核队列：查询 `review_status='pending'` → 通过/拒绝 → 更新状态 + 发通知
- 回测任务监控：查询 `backtest_jobs` 状态 + Celery inspect API
- 用户管理：封禁（`users.is_banned BOOLEAN`）、查看操作日志
- 数据源健康监控：定时 ping 聚宽 API → 异常时邮件告警管理员（Celery Beat）

**审计日志（NFR29）：**
```sql
audit_logs (
  id, operator_id, action VARCHAR(100),
  target_type VARCHAR(50), target_id INTEGER,
  details JSONB, created_at TIMESTAMPTZ
)
-- 覆盖：支付操作、管理员操作（封禁/下架/权限变更）、策略代码访问
-- 保留 ≥ 90 天，仅 admin 角色可查
```

**新增蓝图：** `backend/app/blueprints/admin.py` → `/api/v1/admin/`

### 领域 9：通知系统（FR59-60）

**双通道通知：**

**站内通知：**
```sql
notifications (
  id, user_id, type VARCHAR(50),
  title VARCHAR(200), content TEXT,
  is_read BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ
)
```
- 前端 30 秒轮询 `GET /api/v1/notifications/unread-count`
- 全量通知分页：`GET /api/v1/notifications`

**邮件通知：**
- Flask-Mail + SMTP（阿里云邮件推送 / SendGrid）
- 异步通过 Celery 任务发送，不阻塞主请求
- 触发场景：策略审核结果、重要系统通知

**新增蓝图：** `backend/app/blueprints/notifications.py` → `/api/v1/notifications/`

---

## 完整平台项目结构（扩展版）

```
QYQuant/
├── pyproject.toml                  # uv workspace 根配置
├── uv.lock
├── docker-compose.yml
├── .github/workflows/ci.yml
│
├── packages/
│   └── qysp/                       # SDK + CLI（已有结构保留）
│       ├── src/qysp/
│       │   ├── context.py, indicators.py, validator.py, sandbox.py
│       │   ├── utils/time.py
│       │   ├── templates/trend_following/, mean_reversion/, momentum/
│       │   └── cli/main.py         # init/validate/build/backtest/import/migrate
│       └── tests/
│
├── backend/
│   ├── pyproject.toml
│   ├── Dockerfile, Makefile
│   ├── migrations/
│   ├── app/
│   │   ├── __init__.py             # Flask app factory
│   │   ├── blueprints/
│   │   │   ├── auth.py             # /api/v1/auth/         新增
│   │   │   ├── strategies.py       # /api/v1/strategies/   已有+扩展
│   │   │   ├── backtest.py         # /api/v1/backtest/     已有+扩展
│   │   │   ├── presets.py          # /api/v1/.../presets   已有
│   │   │   ├── marketplace.py      # /api/v1/marketplace/  新增
│   │   │   ├── community.py        # /api/v1/posts/        新增
│   │   │   ├── simulation.py       # /api/v1/simulation/   新增
│   │   │   ├── payments.py         # /api/v1/payments/     新增
│   │   │   ├── notifications.py    # /api/v1/notifications/ 新增
│   │   │   └── admin.py            # /api/v1/admin/        新增
│   │   ├── models/
│   │   │   ├── user.py             # 新增
│   │   │   ├── strategy.py         # 扩展
│   │   │   ├── preset.py           # 已有
│   │   │   ├── backtest_job.py     # 新增
│   │   │   ├── user_quota.py       # 新增
│   │   │   ├── market_data.py      # 新增（缓存）
│   │   │   ├── post.py             # 新增
│   │   │   ├── simulation.py       # 新增
│   │   │   ├── subscription.py     # 新增
│   │   │   ├── notification.py     # 新增
│   │   │   └── audit_log.py        # 新增
│   │   ├── tasks/
│   │   │   ├── celery_app.py       # Celery 配置
│   │   │   ├── backtest_tasks.py   # 回测执行任务
│   │   │   ├── simulation_tasks.py # 模拟托管调度
│   │   │   ├── quota_tasks.py      # 月度额度重置
│   │   │   └── notification_tasks.py # 邮件发送任务
│   │   └── utils/
│   │       ├── time.py             # 时区工具
│   │       ├── crypto.py           # AES-256-GCM 加解密
│   │       ├── storage.py          # 对象存储（MinIO/OSS）封装
│   │       └── sms.py              # 短信服务封装
│   └── tests/
│
├── frontend/
│   └── src/
│       ├── stores/
│       │   ├── useAuthStore.ts         # 新增
│       │   ├── useStrategyStore.ts     # 新增
│       │   ├── useBacktestStore.ts     # 新增
│       │   ├── usePresetsStore.ts      # 新增
│       │   ├── useMarketplaceStore.ts  # 新增
│       │   ├── useCommunityStore.ts    # 新增
│       │   ├── useSimulationStore.ts   # 新增
│       │   └── useNotificationStore.ts # 新增
│       ├── views/
│       │   ├── Login.vue               # 新增
│       │   ├── Onboarding.vue          # 新增（FR7-8 新手引导）
│       │   ├── Marketplace.vue         # 新增（策略广场）
│       │   ├── StrategyDetail.vue      # 新增
│       │   ├── Backtest.vue            # 扩展
│       │   ├── BacktestResult.vue      # 扩展
│       │   ├── SimulationDashboard.vue # 新增
│       │   ├── Profile.vue             # 新增
│       │   ├── Subscription.vue        # 新增
│       │   └── admin/
│       │       ├── AdminDashboard.vue
│       │       ├── StrategyReview.vue
│       │       ├── UserManagement.vue
│       │       └── BacktestMonitor.vue
│       └── components/
│           ├── strategy/
│           │   ├── StrategyCard.vue, ParameterForm.vue, StrategyImport.vue
│           ├── backtest/
│           │   └── BacktestResult.vue, EquityCurve.vue
│           ├── simulation/
│           │   ├── SimulationBot.vue
│           │   └── SimulationChart.vue
│           └── common/
│               ├── QuotaBadge.vue      # 剩余额度展示
│               └── NotificationBell.vue
│
└── docs/
    ├── quickstart.md
    ├── api-reference.md
    └── strategy-format/             # 已有
```

## 完整数据库 Schema 概览

| 表名 | 用途 | 关键字段 |
|------|------|---------|
| `users` | 用户账户 | id, phone, role, plan_level |
| `refresh_tokens` | JWT 刷新令牌 | user_id, token_hash, expires_at |
| `strategies` | 策略包 | author_id, code_encrypted, is_verified, review_status |
| `strategy_parameter_presets` | 参数预设 | strategy_id, user_id, parameters JSONB |
| `backtest_jobs` | 回测任务 | user_id, strategy_id, status, result_summary JSONB |
| `user_quota` | 回测额度 | user_id, used_count, reset_at |
| `market_data_cache` | 行情缓存 | symbol, trade_date, OHLCV |
| `posts` | 社区帖子 | user_id, strategy_id, content |
| `post_interactions` | 点赞/收藏 | user_id, post_id, type |
| `comments` | 评论 | post_id, user_id, content |
| `simulation_bots` | 模拟机器人 | user_id, strategy_id, status |
| `simulation_positions` | 模拟持仓 | bot_id, symbol, quantity |
| `simulation_records` | 模拟收益记录 | bot_id, trade_date, equity |
| `subscriptions` | 订阅套餐 | user_id, plan_level, ends_at |
| `payment_orders` | 支付订单 | user_id, amount, provider, status |
| `notifications` | 站内通知 | user_id, type, is_read |
| `audit_logs` | 操作审计 | operator_id, action, target_type |

## 完整 API 端点概览（/api/v1/）

| 模块 | 端点前缀 | 蓝图 |
|------|---------|------|
| 认证 | `/auth/` | auth.py |
| 策略管理 | `/strategies/` | strategies.py |
| 回测 | `/backtest/` | backtest.py |
| 参数预设 | `/strategies/:id/presets/` | presets.py |
| 策略广场 | `/marketplace/` | marketplace.py |
| 社区 | `/posts/` | community.py |
| 模拟托管 | `/simulation/` | simulation.py |
| 支付 | `/payments/` | payments.py |
| 通知 | `/notifications/` | notifications.py |
| 管理后台 | `/admin/` | admin.py |

## 平台级 FR 覆盖映射（prd.md 65 FRs）

| FR范围 | 功能域 | 架构支撑 |
|--------|--------|---------|
| FR1-6 | 用户管理 | `users`表 + `auth.py`蓝图 + JWT方案 |
| FR7-9 | 新手引导 | `Onboarding.vue` + `users.onboarding_completed` |
| FR10-24 | 量化回测 | Celery + E2B沙箱 + `backtest_jobs`表 + 对象存储 |
| FR25-34 | 策略广场 | `strategies`扩展表 + `marketplace.py` + PG全文搜索 |
| FR35-39 | 社区互动 | `posts/comments/post_interactions`表 + `community.py` |
| FR40-48 | 模拟托管 | Celery Beat + SSE + `simulation_*`表 |
| FR49-56 | 平台管理 | `admin.py` + `audit_logs`表 + Celery Beat监控 |
| FR57-65 | 平台安全/通知 | `notifications`表 + AES-256加密 + 速率限制 |

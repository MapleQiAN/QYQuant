---
title: 'QYStrategy 格式改进技术规范 (Phase 1 + Phase 2)'
slug: 'qystrategy-improvement-phase1-2'
created: '2026-02-05'
status: 'in-progress'
stepsCompleted: [1, 2]
tech_stack: ['Python 3.11', 'Flask 3.x', 'PostgreSQL', 'pytest', 'flask-smorest', 'Celery']
files_to_modify: ['backend/app/backtest/engine.py', 'backend/app/blueprints/strategies.py', 'docs/strategy-format/README.md', 'docs/strategy-format/examples/GoldStepByStep/']
code_patterns: ['Blueprint架构', 'SQLAlchemy ORM', 'UUID主键', '统一API响应(ok())', '毫秒级时间戳']
test_patterns: ['pytest + pytest-flask', 'conftest.py fixtures', 'API集成测试']
---

# Tech-Spec: QYStrategy 格式改进技术规范 (Phase 1 + Phase 2)

**Created:** 2026-02-05

## Overview

### Problem Statement

当前 QYStrategy 格式存在核心问题阻塞开发者使用：

1. **参数定义无法在代码中读取（P0）**：`strategy.json` 中定义了 `parameters` 字段，但策略代码无法读取使用，开发者需要硬编码参数，失去了参数化的意义
2. **接口约定不清晰（P0）**：`interface: "event_v1"` 字段存在但无文档说明，开发者不知道如何实现策略入口函数
3. **缺少 SDK 和开发者工具（P1）**：每次都要重复编写数据类、账户管理代码，开发门槛高
4. **示例代码未遵循最佳实践（P1）**：GoldStepByStep 策略使用 `input()` 手动输入价格，误导新手

### Solution

通过 Phase 1 + Phase 2 实现完整的开发者体验：

1. **定义清晰的 `event_v1` 接口规范和文档**：包含完整的类型注解、参数说明和示例代码
2. **实现完整的运行时参数注入机制**：设计 StrategyContext 抽象层，让参数自动从 `strategy.json` 注入到策略代码中
3. **开发 Python SDK**：提供核心类（StrategyContext、BarData、Order、Position、Account）和技术指标函数库（5-10 个常用函数）
4. **实现 `qys` 命令行工具**：支持 init、validate、build、backtest、import 命令
5. **创建策略模板库**：提供 trend-following、mean-reversion、momentum 等常用策略模板
6. **重写 GoldStepByStep 示例策略**：展示最佳实践
7. **制定版本兼容性测试策略**：确保向后兼容性

### Scope

**In Scope:**

- ✅ **Phase 1 (P0) - 基础改进**：
  - `event_v1` 接口规范文档和 Python 类型定义
  - StrategyContext 参数抽象层设计（完整运行时注入，跳过简化版）
  - 参数验证机制（JSON Schema + 运行时类型检查）
  - 重写 GoldStepByStep 示例策略
  - 更新 README 和接口文档

- ✅ **Phase 2 (P1) - 开发者体验**：
  - Python SDK 核心类（StrategyContext、BarData、Order、Position、Account）
  - SDK 技术指标函数库（sma、ema、atr、cross_over、cross_under 等 5-10 个函数）
  - `qys` CLI 工具（init、validate、build、backtest、import 命令）
  - 策略模板（trend-following、mean-reversion、momentum）
  - SDK API 文档
  - 版本兼容性测试策略文档

**Out of Scope:**

- ❌ **Phase 3 (P2) - Web UI**：策略导入页面、参数配置器、策略浏览器
- ❌ **Phase 4 (P1-P2) - 生态完善**：导出功能、策略评分、分享社区、策略库（10+ 策略）

## Context for Development

### Codebase Patterns

**现有技术栈：**
- **后端**：Python 3.11 + Flask 3.x + PostgreSQL (psycopg3)
- **任务队列**：Celery + Redis
- **测试**：pytest + pytest-flask
- **API 文档**：flask-smorest (OpenAPI 3.0)
- **前端**：Vue 3 + TypeScript + Vite（本规范不涉及前端开发）

**后端架构模式：**
- **Blueprint 架构**：模块化的 Flask 蓝图设计（见 [backend/app/__init__.py](e:\QYQuant\backend\app\__init__.py)）
- **数据模型**：SQLAlchemy ORM，使用 `gen_id()` 生成 UUID 主键（见 [backend/app/models.py](e:\QYQuant\backend\app\models.py)）
- **API 响应**：统一使用 `ok()` 函数包装成功响应（见 [backend/app/utils/response.py](e:\QYQuant\backend\app\utils\response.py)）
- **时间处理**：使用 `now_ms()` 返回毫秒级时间戳（见 [backend/app/utils/time.py](e:\QYQuant\backend\app\utils\time.py)）
- **文件存储**：本地文件系统，默认路径 `backend/strategy_store`（见 [backend/app/blueprints/strategies.py:21](e:\QYQuant\backend\app\blueprints\strategies.py#L21)）

**回测引擎现状：**
- **回测引擎**：[backend/app/backtest/engine.py](e:\QYQuant\backend\app\backtest\engine.py) - 仅包含基础框架，缺少策略执行逻辑
- **数据提供者**：[backend/app/backtest/providers.py](e:\QYQuant\backend\app\backtest\providers.py) - 支持 mock、auto、freegold、binance 四种数据源
- **数据模型**：`Backtest` 和 `BacktestTrade` 表已存在（见 [backend/app/models.py:53-77](e:\QYQuant\backend\app\models.py#L53-L77)）

**现有策略示例问题：**
1. **GoldStepByStep** 使用 `input()` 手动输入价格（见 [strategy.py:59](e:\QYQuant\docs\strategy-format\examples\GoldStepByStep\src\strategy.py#L59)），完全不符合回测需求
2. 策略代码自己实现了 `Date`、`Holding`、`Account` 等数据类（见 [strategy.py:5-35](e:\QYQuant\docs\strategy-format\examples\GoldStepByStep\src\strategy.py#L5-L35)），重复造轮子
3. **没有参数注入机制**：`strategy.json` 中定义的 `parameters` 字段无法在代码中使用
4. **接口约定不清晰**：`entrypoint.callable` 是 `"main"`，但没有标准接口文档

**关键约束：**
1. **SDK 零依赖策略**：自实现技术指标函数，不依赖 ta-lib 等外部库
2. **严格向后兼容**：现有 .qys 文件必须继续工作
3. **跨平台支持**：Windows 10+、macOS 12+、Ubuntu 20.04+
4. **Python 3.11+ 兼容**：使用类型注解和现代 Python 特性
5. **集成到现有系统**：策略导入、回测结果需要与现有 Flask + Celery 架构集成

**关键架构决策（来自架构文档）：**
1. **参数注入策略**：直接实现完整的运行时动态注入（跳过打包时生成配置的简化版）
2. **SDK 依赖策略**：零依赖 + 核心函数自实现
3. **版本兼容性**：语义化版本控制 + 迁移工具（v1.x → v1.y 必须向后兼容）

### Files to Reference

| File | Purpose |
| ---- | ------- |
| [docs/strategy-format/README.md](e:\QYQuant\docs\strategy-format\README.md) | 当前 QYSP 格式规范文档 |
| [docs/strategy-format/qysp.schema.json](e:\QYQuant\docs\strategy-format\qysp.schema.json) | JSON Schema 定义 |
| [docs/strategy-format/examples/GoldStepByStep/strategy.json](e:\QYQuant\docs\strategy-format\examples\GoldStepByStep\strategy.json) | 需要重写的示例策略清单 |
| [docs/strategy-format/examples/GoldStepByStep/src/strategy.py](e:\QYQuant\docs\strategy-format\examples\GoldStepByStep\src\strategy.py) | 需要重写的示例策略代码 |
| [docs/strategy-format/examples/GoldTrend/strategy.json](e:\QYQuant\docs\strategy-format\examples\GoldTrend\strategy.json) | 另一个示例策略（含 parameters 定义） |
| [backend/app/blueprints/strategies.py](e:\QYQuant\backend\app\blueprints\strategies.py) | 策略蓝图（验证逻辑、导入流程） |
| [backend/app/backtest/engine.py](e:\QYQuant\backend\app\backtest\engine.py) | 回测引擎（需集成策略执行） |
| [backend/app/backtest/providers.py](e:\QYQuant\backend\app\backtest\providers.py) | 数据提供者（mock, auto, freegold, binance） |
| [backend/app/models.py](e:\QYQuant\backend\app\models.py) | 数据模型（Strategy, StrategyVersion, Backtest） |
| [backend/requirements.txt](e:\QYQuant\backend\requirements.txt) | 后端依赖清单 |
| [backend/tests/test_strategies.py](e:\QYQuant\backend\tests\test_strategies.py) | 策略测试示例 |
| [_bmad-output/planning-artifacts/prd-qystrategy-improvement.md](e:\QYQuant\_bmad-output\planning-artifacts\prd-qystrategy-improvement.md) | 产品需求文档 |
| [_bmad-output/planning-artifacts/architecture.md](e:\QYQuant\_bmad-output\planning-artifacts\architecture.md) | 架构决策文档 |

### Technical Decisions

**1. 参数抽象层设计：**

- 创建 `StrategyContext` 类作为参数提供者
- 策略函数通过 `ctx.parameters.get()` 访问参数
- 支持类型转换和默认值
- 参数验证失败时给出明确错误信息
- 集成到回测引擎中：在执行策略前注入参数

**2. SDK 结构：**

- 包名：`qyquant-sdk`（将发布到 PyPI）
- 核心模块组织：
  - `qyquant.context` - StrategyContext 等上下文类
  - `qyquant.data` - BarData 等数据类
  - `qyquant.orders` - Order、Position、Account 等交易类
  - `qyquant.indicators` - 技术指标函数库
- 类型注解完整，支持 IDE 自动补全
- 零依赖：仅使用 Python 标准库

**3. event_v1 接口规范：**

- 入口函数签名：`def on_bar(ctx: StrategyContext, data: BarData) -> list[Order]`
- 每根 K 线调用一次（事件驱动）
- `ctx` 包含：parameters、account、position 等信息
- `data` 包含：time、open、high、low、close、volume
- 返回值：订单列表（可为空）

**4. CLI 工具设计：**

- 命令名称：`qys`
- 使用 `argparse` 实现子命令（避免外部依赖）
- 支持配置文件（`~/.qys/config.yaml`）
- 错误信息清晰可操作
- 子命令：
  - `qys init <name> --template` - 创建新策略
  - `qys validate <file.qys>` - 验证策略包
  - `qys build <dir>` - 打包策略
  - `qys backtest <file.qys>` - 运行回测
  - `qys import <file.qys>` - 导入到数据库

**5. 回测引擎集成：**

- 修改 `backend/app/backtest/engine.py:run_backtest()`
- 添加策略执行逻辑：加载 .qys 文件 → 注入参数 → 逐 K 线调用 `on_bar()`
- 收集订单并更新账户状态
- 计算回测指标（复用现有 `_calculate_summary()`）

**6. 版本兼容性：**

- `schemaVersion` 字段使用语义化版本
- 新字段都是可选的，保持向后兼容
- 提供 `qys migrate` 命令用于版本升级
- 策略验证时检查 schemaVersion，给出清晰错误提示

## Implementation Plan

### Tasks

（待 Step 2 深入调查后填充）

### Acceptance Criteria

（待 Step 2 深入调查后填充）

## Additional Context

### Dependencies

- **内部依赖**：回测引擎、数据源接口（需要进一步调查）
- **外部依赖**：无（SDK 零依赖，CLI 工具仅依赖标准库）

### Testing Strategy

（待 Step 2 深入调查后填充）

### Notes

- 技术规范需要涵盖所有实现细节，让新的开发代理可以直接执行
- 每个 FR（功能需求）都需要有明确的验收标准（Given/When/Then 格式）
- 需要考虑错误处理和边界情况
- 文档更新需要与代码同步进行

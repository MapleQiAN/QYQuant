---
stepsCompleted: []
inputDocuments:
  - docs/strategy-format/README.md
  - docs/strategy-format/qysp.schema.json
  - docs/strategy-format/examples/GoldTrend/strategy.json
  - docs/strategy-format/examples/GoldStepByStep/strategy.json
  - docs/strategy-format/examples/GoldStepByStep/src/strategy.py
workflowType: 'prd'
---

# Product Requirements Document - QYStrategy 格式改进

**Author:** Serendy
**Date:** 2026-02-05
**Version:** 1.0

---

## 1. 执行摘要

### 1.1 项目概述

改进 QYQuant 的统一策略文件格式（QYStrategy Package, QYSP），构建一个完整的策略生态系统，连接策略开发者、策略分享者和终端用户。

### 1.2 业务目标

- **降低策略开发门槛**：让有编程经验的开发者能快速创建和测试策略
- **简化策略分享流程**：实现策略的标准化打包、版本管理和分发
- **提升终端用户体验**：让非技术用户能轻松发现、配置和使用现成策略
- **建立策略市场基础**：为未来构建策略共享社区打下技术基础

### 1.3 成功指标

- 策略开发时间减少 50%（从手动编写到使用 SDK 和模板）
- 策略导入成功率提升至 95%+（通过标准化验证）
- 用户能在 5 分钟内完成策略导入和参数配置（通过 Web UI）
- 策略包格式的向后兼容性达到 100%（通过 schema 版本控制）

---

## 2. 目标用户

### 2.1 主要用户群体

| 用户类型 | 技术水平 | 主要需求 | 使用场景 |
|---------|---------|---------|---------|
| **策略开发者** | 有 Python 编程经验 | 快速实现策略逻辑、调试和回测 | 创建自定义交易策略、分享给社区 |
| **策略研究者** | 有限编程经验 | 可视化配置参数、快速验证想法 | 调整现有策略参数、组合多个策略 |
| **个人投资者** | 非技术背景 | 一键导入策略、查看回测结果 | 使用现成策略进行模拟/实盘交易 |

### 2.2 用户画像

#### 开发者 - David
- 量化交易爱好者，3 年 Python 经验
- 熟悉 pandas、numpy，了解回测框架
- **痛点**：每次都要重复编写数据类、账户管理代码
- **需求**：清晰的接口定义、SDK、自动化测试工具

#### 研究者 - Emily
- 金融分析师，懂基础 Python
- 更关注策略逻辑而非底层实现
- **痛点**：示例代码混乱，参数定义无法使用
- **需求**：清晰的文档、可视化参数编辑器

#### 投资者 - Frank
- 退休工程师，不写代码
- 想使用社区验证过的策略
- **痛点**：不知道如何配置和运行 .qys 文件
- **需求**：Web UI、一键导入、参数说明

---

## 3. 问题陈述

### 3.1 当前问题

基于对现有 QYStrategy 格式的分析，发现以下核心问题：

#### 问题 1：参数定义无法使用
- **现象**：strategy.json 中定义了 `parameters` 字段，但代码中无法读取
- **影响**：开发者需要硬编码参数，失去了参数化的意义
- **根因**：缺少参数注入机制和运行时环境

#### 问题 2：接口约定不清晰
- **现象**：`interface: "event_v1"` 字段存在但无文档说明
- **影响**：开发者不知道如何实现策略入口函数
- **根因**：接口规范文档缺失

#### 问题 3：示例代码脱节
- **现象**：GoldStepByStep 策略使用 `input()` 手动输入价格
- **影响**：新手误以为这是正确做法
- **根因**：示例未遵循最佳实践

#### 问题 4：开发者体验差
- **现象**：需要手动实现 Date、Holding、Account 等数据类
- **影响**：重复造轮子，容易出错
- **根因**：缺少 SDK 和基类

#### 问题 5：终端用户无法使用
- **现象**：非技术用户无法处理 .qys 压缩包和 JSON 配置
- **影响**：策略分享只能在开发者之间进行
- **根因**：缺少用户友好的配置工具

### 3.2 问题优先级

| 优先级 | 问题 | 影响 | 紧急程度 |
|-------|------|------|---------|
| P0 | 参数定义无法使用 | 阻塞核心功能 | 🔴 高 |
| P0 | 接口约定不清晰 | 阻塞开发者上手 | 🔴 高 |
| P1 | 缺少 SDK/基类 | 开发体验差 | 🟡 中 |
| P1 | 示例代码脱节 | 误导新手 | 🟡 中 |
| P2 | 终端用户无法使用 | 限制受众范围 | 🟢 低 |

---

## 4. 功能需求

### 4.1 策略格式改进（P0）

#### FR-1: 清晰的接口规范
定义策略实现的标准接口：

**event_v1 接口**：
```python
from qyquant import StrategyContext, BarData, Order

def on_bar(ctx: StrategyContext, data: BarData) -> list[Order]:
    """
    每根 K 线调用一次

    Args:
        ctx: 策略上下文（包含参数、账户、持仓等）
        data: 当前 K 线数据（OHLCV）

    Returns:
        订单列表
    """
    pass
```

**接受标准**：
- 接口文档完整，包含类型注解
- 提供至少 3 个示例策略
- 支持 Python 3.11+

#### FR-2: 参数注入机制
strategy.json 中定义的参数必须能在代码中使用：

```python
def on_bar(ctx: StrategyContext, data: BarData) -> list[Order]:
    # ctx.parameters 中自动包含定义的参数
    lookback = ctx.parameters.get('breakoutLookback', 252)
    drop_pct = ctx.parameters.get('dropOneDayPct', 3.0)
    ...
```

**接受标准**：
- 参数自动注入到 StrategyContext
- 支持类型转换和默认值
- 参数验证失败时给出明确错误信息

#### FR-3: 策略元数据增强
在 strategy.json 中添加新字段：

```json
{
  "ui": {
    "icon": "strategies/gold.png",
    "category": "trend-following",
    "difficulty": "intermediate"
  },
  "backtest": {
    "defaultPeriod": {
      "start": "2020-01-01",
      "end": "2025-12-31"
    },
    "initialCapital": 100000
  }
}
```

**接受标准**：
- 新字段完全向后兼容（可选）
- UI 相关字段用于 Web 展示
- 回测默认值用于快速测试

### 4.2 开发者工具（P1）

#### FR-4: Python SDK
提供官方 Python SDK，包含：

**核心类**：
- `StrategyContext`: 策略上下文（参数、账户、持仓）
- `BarData`: K 线数据封装
- `Order`: 订单类
- `Position`: 持仓类
- `Account`: 账户类

**工具函数**：
- `sma(series, period)`: 简单移动平均
- `ema(series, period)`: 指数移动平均
- `atr(high, low, close, period)`: 平均真实波幅
- `cross_over(series1, series2)`: 金叉检测
- `cross_under(series1, series2)`: 死叉检测

**接受标准**：
- SDK 包含完整类型注解
- 提供 API 文档和示例代码
- 单元测试覆盖率 ≥ 80%

#### FR-5: 命令行工具
提供 `qys` 命令行工具：

```bash
# 创建新策略
qys init my-strategy --template trend-following

# 验证策略包
qys validate my-strategy.qys

# 打包策略
qys build my-strategy/

# 运行回测
qys backtest my-strategy.qys --start 2020-01-01 --end 2025-12-31

# 导入策略到数据库
qys import my-strategy.qys
```

**接受标准**：
- 每个命令都有帮助文档
- 错误信息清晰可操作
- 支持 Windows/Linux/macOS

#### FR-6: 策略模板
提供常用策略模板：

- `trend-following`: 趋势跟踪策略模板
- `mean-reversion`: 均值回归策略模板
- `momentum`: 动量策略模板
- `multi-indicator`: 多指标组合策略模板

**接受标准**：
- 每个模板都是可直接运行的完整策略
- 包含详细注释说明
- 通过示例数据验证

### 4.3 Web 配置界面（P2）

#### FR-7: 策略导入页面
Web UI 用于导入 .qys 文件：

**功能**：
- 拖拽上传 .qys 文件
- 自动解析 strategy.json
- 显示策略元数据（名称、描述、标签、作者）
- 验证文件完整性（sha256 校验）

**接受标准**：
- 上传进度显示
- 验证失败时明确提示原因
- 导入成功后跳转到配置页面

#### FR-8: 参数配置器
可视化编辑策略参数：

**功能**：
- 根据 `parameters` 定义动态生成表单
- 支持 slider（带 min/max/step）
- 支持 dropdown（枚举类型）
- 实时参数验证
- 参数说明提示

**接受标准**：
- UI 响应式，适配移动端
- 参数修改后可保存为预设
- 支持导入/导出参数配置

#### FR-9: 策略浏览器
浏览已导入的策略：

**功能**：
- 卡片式展示策略列表
- 按标签/分类筛选
- 搜索策略名称和描述
- 显示策略性能摘要（如果有回测数据）

**接受标准**：
- 支持分页加载
- 点击卡片进入详情页
- 支持删除和导出操作

### 4.4 示例和文档（P1）

#### FR-10: 更新示例策略
重写 GoldStepByStep 示例：

**要求**：
- 使用标准 `event_v1` 接口
- 从 `ctx.parameters` 读取参数
- 使用 SDK 提供的数据类
- 包含完整注释

#### FR-11: 完整文档
创建文档站点：

**章节**：
- 快速开始（5 分钟上手）
- 策略格式规范
- SDK API 参考
- 命令行工具文档
- 常见问题 FAQ

---

## 5. 非功能需求

### 5.1 性能

- 参数注入开销 < 10ms
- 策略验证时间 < 1s（对于典型策略包）
- Web 页面加载时间 < 2s

### 5.2 兼容性

- **向后兼容**：现有的 .qys 文件必须能继续工作
- **向前兼容**：新版本的策略应能在旧版本系统上降级使用（警告）
- **跨平台**：SDK 和 CLI 工具支持 Windows 10+、macOS 12+、Ubuntu 20.04+

### 5.3 可维护性

- SDK 代码遵循 PEP 8 规范
- 公共 API 变更需要通过 deprecation 流程
- 文档与代码同步更新

### 5.4 安全性

- 策略包在沙箱环境中执行
- 不允许策略代码访问文件系统（只读白名单）
- 参数注入经过验证和清洗

### 5.5 可扩展性

- 支持自定义参数类型（通过插件机制）
- 支持多语言策略（Python 优先，未来可扩展）
- 支持自定义策略接口版本

---

## 6. 技术约束

### 6.1 现有技术栈

- **前端**：Vue 3 + TypeScript + Vite
- **后端**：Python 3.11 + Flask
- **数据库**：PostgreSQL（已有 strategies 表）

### 6.2 依赖约束

- SDK 必须兼容 Python 3.11+
- Web UI 使用现有的 Vue 3 前端框架
- 不引入新的数据库（使用现有的 PostgreSQL）

### 6.3 集成点

- 策略导入需要集成到现有的 Dashboard
- 回测结果需要显示在 BacktestCard 组件
- 策略列表需要使用现有的 RecentList 组件

---

## 7. 实施优先级

### Phase 1: 基础改进（2-3 周）- P0

**目标**：让策略格式真正可用

- [ ] 定义 `event_v1` 接口规范文档
- [ ] 实现参数注入机制
- [ ] 重写 GoldStepByStep 示例策略
- [ ] 更新 README 和文档

**交付物**：
- 接口规范文档
- 1 个完整的示例策略
- 更新后的 README

### Phase 2: 开发者体验（2-3 周）- P1

**目标**：降低策略开发门槛

- [ ] 开发 Python SDK（核心类 + 工具函数）
- [ ] 实现 `qys` 命令行工具（init, validate, build）
- [ ] 创建策略模板（trend-following, mean-reversion）
- [ ] 编写 SDK API 文档

**交付物**：
- PyPI 包 `qyquant-sdk`
- 命令行工具 `qys`
- 4 个策略模板

### Phase 3: Web 配置（3-4 周）- P2

**目标**：让非技术用户也能使用策略

- [ ] 实现策略导入页面
- [ ] 实现参数配置器（动态表单）
- [ ] 实现策略浏览器
- [ ] 集成到现有 Dashboard

**交付物**：
- Web UI 组件（3 个页面）
- API 接口文档

### Phase 4: 生态完善（1-2 周）- P1-P2

**目标**：建立策略市场基础

- [ ] 实现策略导出功能
- [ ] 添加策略评分/评论（预留接口）
- [ ] 创建策略分享指南
- [ ] 建立示例策略库（10+ 策略）

**交付物**：
- 分享功能
- 策略库文档

---

## 8. 风险与依赖

### 8.1 风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 策略格式变更导致现有策略失效 | 高 | 保持向后兼容，提供迁移工具 |
| SDK 开发工作量超出预期 | 中 | 分阶段交付，优先核心功能 |
| Web UI 与现有架构冲突 | 中 | 复用现有组件，渐进式集成 |

### 8.2 依赖

- **内部依赖**：回测引擎、数据源接口
- **外部依赖**：无（纯内部项目）

---

## 9. 验收标准

### 9.1 Phase 1 验收

- [ ] 开发者能在 10 分钟内理解如何实现策略
- [ ] 参数能在策略代码中正确读取和使用
- [ ] 示例策略通过回测并产生预期结果

### 9.2 Phase 2 验收

- [ ] 新手能在 30 分钟内创建第一个策略（使用模板）
- [ ] `qys validate` 能检测 90% 的常见错误
- [ ] SDK 单元测试覆盖率 ≥ 80%

### 9.3 Phase 3 验收

- [ ] 非技术用户能在 5 分钟内导入并配置策略
- [ ] 参数配置器支持所有定义的参数类型
- [ ] Web UI 在主流浏览器中正常工作

### 9.4 Phase 4 验收

- [ ] 用户能导出配置好的策略并分享
- [ ] 策略库包含至少 10 个不同类型的策略
- [ ] 文档覆盖所有核心功能

---

## 10. 附录

### 10.1 术语表

- **QYSP**: QY Strategy Package，QYQuant 策略包格式
- **event_v1**: 策略接口版本 1，基于事件驱动的回测
- **SDK**: Software Development Kit，软件开发工具包

### 10.2 参考文档

- [当前策略格式规范](../docs/strategy-format/README.md)
- [JSON Schema 定义](../docs/strategy-format/qysp.schema.json)
- [现有示例策略](../docs/strategy-format/examples/)

---

**文档变更历史**：

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|---------|
| 1.0 | 2026-02-05 | Serendy | 初始版本 |

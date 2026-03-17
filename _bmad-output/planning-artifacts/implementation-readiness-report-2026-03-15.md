---
stepsCompleted: ["step-01-document-discovery", "step-02-prd-analysis", "step-03-epic-coverage-validation", "step-04-ux-alignment", "step-05-epic-quality-review", "step-06-final-assessment"]
documentsSelected:
  prd: "_bmad-output/planning-artifacts/prd.md"
  architecture: "_bmad-output/planning-artifacts/architecture.md"
  epics: "_bmad-output/planning-artifacts/epics.md"
  ux: "_bmad-output/planning-artifacts/ux-design-specification.md"
---

# Implementation Readiness Assessment Report

**Date:** 2026-03-15
**Project:** QYQuant

---

## 文档清单（Step 1 输出）

| 类型 | 文件 | 大小 | 日期 |
|------|------|------|------|
| PRD（主版本） | `prd.md` | 34 KB | 2026-03-14 |
| PRD（废弃草稿） | `prd-qystrategy-improvement.md` | 13 KB | 2026-02-05（已确认废弃） |
| PRD 验证报告 | `prd-validation-report.md` | 22 KB | 2026-03-14 |
| 架构文档 | `architecture.md` | 49 KB | 2026-03-15 |
| Epics & Stories | `epics.md` | 65 KB | 2026-03-15 |
| UX 设计规范 | `ux-design-specification.md` | 33 KB | 2026-03-14 |

**本次评估采用：** `prd.md`（主PRD）、`architecture.md`、`epics.md`、`ux-design-specification.md`

---

## PRD 分析（Step 2 输出）

### 功能需求（FRs）提取 — 共 65 条

| 域 | 编号范围 | 数量 |
|----|---------|------|
| 用户管理 | FR1–FR6 | 6 |
| 新手引导与学习 | FR7–FR9 | 3 |
| 量化回测 | FR10–FR24 | 15 |
| 策略广场 | FR25–FR34 | 10 |
| 社区互动 | FR35–FR39 | 5 |
| 模拟托管 | FR40–FR48 | 9 |
| 平台管理与安全 | FR49–FR65 | 17 |
| **合计** | | **65** |

完整 FR 列表见 `prd.md` 第 483–569 行。

### 非功能需求（NFRs）提取 — 共 29 条

| 类别 | 编号 | 数量 |
|------|------|------|
| 性能 | NFR1–NFR5 | 5 |
| 可用性与可靠性 | NFR6–NFR9 | 4 |
| 安全性 | NFR10–NFR14 | 5 |
| 可扩展性 | NFR15–NFR17 | 3 |
| 用户体验 | NFR18–NFR21 | 4 |
| 合规性 | NFR22–NFR23 | 2 |
| 小白友好性 | NFR24–NFR25 | 2 |
| UI 设计风格 | NFR26 | 1 |
| 数据一致性与运行环境 | NFR27–NFR28 | 2 |
| 审计与合规追踪 | NFR29 | 1 |
| **合计** | | **29** |

### PRD 完整性初步评估

✅ PRD 结构完整，包含执行摘要、成功标准、产品范围、用户旅程、领域特定需求、功能需求、非功能需求。
✅ FRs 编号清晰（FR1–FR65），覆盖全部主要功能模块。
✅ NFRs 有明确量化指标（如"30秒内完成"、"99.5%可用性"）。
⚠️ **注意**：Epics 文件中还引用了来自已废弃草稿的 11 条 QYSP-FRs（QYSP-FR1~FR11），主 PRD 中未包含这些需求（详见 Step 3 分析）。

---

## Epic 覆盖验证（Step 3 输出）

### 覆盖统计

- **主 PRD 功能需求（FR1–FR65）：** 65 条
- **Epics 声称覆盖：** 76/76（含 11 条 QYSP-FRs）
- **平台 FR（FR1–FR65）实际覆盖：** 65/65 = **100%**

### FR 覆盖矩阵（平台 FR 部分）

| FR 编号 | Epic 归属 | 状态 |
|---------|----------|------|
| FR1–FR2, FR6 | Epic 2 | ✅ 已覆盖 |
| FR3–FR5 | Epic 8 | ✅ 已覆盖 |
| FR7–FR9 | Epic 4 | ✅ 已覆盖 |
| FR10–FR24, FR57, FR58, FR63, FR64 | Epic 3 | ✅ 已覆盖 |
| FR25–FR34, FR61, FR62 | Epic 5 | ✅ 已覆盖 |
| FR35–FR39 | Epic 6 | ✅ 已覆盖 |
| FR40–FR48 | Epic 7 | ✅ 已覆盖 |
| FR49–FR54, FR56, FR65 | Epic 10 | ✅ 已覆盖 |
| FR55 | Epic 4 | ✅ 已覆盖 |
| FR59–FR60 | Epic 9 | ✅ 已覆盖 |

### ⚠️ 关键发现：QYSP-FRs 来源问题

Epics 文件将 11 条 QYSP-FRs（来自已废弃草稿 `prd-qystrategy-improvement.md`）作为正式需求纳入，Epic 1（平台基础 & QYSP 策略格式）完全基于这些需求。

- **现状**：Architecture 文档明确引用 QYSP 格式（uv workspace monorepo、packages/qysp SDK+CLI、E2B 沙箱），说明 QYSP 已被架构采纳
- **风险**：这 11 条需求**未在主 PRD 中有正式对应条目**，需求来源文档已废弃
- **建议**：评估是否应将 QYSP-FRs 纳入主 PRD 补充条款，或在 Epics 中明确标注其来源为架构约束而非 PRD 需求

### 缺失 FR 汇总

**平台 FR（FR1–FR65）：无缺失，100% 覆盖。**

---

## UX 对齐评估（Step 4 输出）

### UX 文档状态

✅ **已找到**：`ux-design-specification.md`（33KB，2026-03-14，完整的 14 步工作流输出）

### UX ↔ PRD 对齐

| 检查项 | PRD 要求 | UX 规范 | 状态 |
|--------|---------|---------|------|
| NFR18：≤5步完成首次回测 | ≤5 步 | 明确定义3次点击路径 | ✅ 一致 |
| NFR20：Equity Curve 首屏可见 | 图表首屏默认可见 | 明确定义为"决策界面"，P0 组件 | ✅ 一致 |
| NFR25：>3s 操作进度反馈 | 进度条/百分比/阶段提示 | BacktestProgress 三阶段组件 | ✅ 一致 |
| NFR26：极简金融仪表盘 | 白色主背景、红色强调色 | 白色主背景 `#F8FAFC` ✅ | ✅ 一致 |
| NFR26：单屏指标≤7 | ≤7个数据指标 | 核心三指标+折叠方式 | ✅ 一致 |
| NFR26：核心功能≤3次点击 | 到达路径≤3次点击 | 明确定义"≤3次点击" | ✅ 一致 |
| FR7–FR8：新手引导 | 3步互动卡片 | OnboardingGuide 组件，完整流程图 | ✅ 一致 |
| FR46：模拟托管免责一次性弹窗 | 首次确认，此后不再弹出 | 一次性弹窗，记录`sim_disclaimer_accepted` | ✅ 一致 |
| FR21：智能错误提示 | 含示例引导 | SmartErrorAlert 组件（含代码行数+示例链接） | ✅ 一致 |

### ⚠️ UX ↔ PRD 不一致项（关键冲突）

**🔴 冲突 1：CTA 按钮颜色定义相互矛盾（高优先级）**

| 文档 | 描述 |
|------|------|
| PRD NFR26 | "红色仅用于**CTA按钮**和收益/亏损指示" |
| UX 规范 | "CTA 主操作按钮：纯黑 `#1A1A1A`；红色用途：涨幅/强调/价格" |

这是直接矛盾——PRD 说 CTA 用红色，UX 规范说 CTA 用黑色。实现团队需在开发前明确取哪个版本。

**建议**：以 UX 规范为准（黑色 CTA + 红色涨跌色），并更新 PRD NFR26 措辞为"红色仅用于涨跌指示和强调色"。

### UX ↔ Architecture 对齐

| UX 技术决策 | Architecture 约束 | 状态 |
|------------|-----------------|------|
| Vue 3 + 自定义 CSS | 无 UI 框架约束，ECharts 集成 | ✅ 一致 |
| ECharts 封装 EquityCurveChart | ECharts 已有集成基础 | ✅ 一致 |
| SSE 实时推送模拟托管 | ARCH-12：SSE（GET /api/v1/simulation/:bot_id/stream）| ✅ 一致 |
| 30 秒轮询通知未读数 | ARCH-13：30 秒轮询端点 | ✅ 一致 |
| Desktop-First SPA | PRD 明确"Web优先，不做原生App" | ✅ 一致 |
| 回测三阶段进度展示 | Celery 任务队列异步执行 | ✅ 一致（前端状态与后端任务状态映射需确认） |

### 警告

**⚠️ 警告 1：Mobile 功能范围未在 PRD 中明确**
- UX 规范定义了 Mobile 仅提供"40% 功能（监控视图）"
- PRD 仅说"响应式设计，支持桌面和移动端浏览器"，未定义功能裁减范围
- 建议：在 PRD 或架构文档补充说明移动端功能范围限制，避免实现歧义

**⚠️ 警告 2：管理员 UI 设计缺失**
- UX 规范未包含管理后台（Epic 10）的 UI 设计
- Epic 10 覆盖 FR49-FR54、FR56、FR65 共 8 个管理员 FR，审核/封禁/任务监控均需 UI
- 影响评估：管理后台通常为内部工具，设计约束低，可在开发时按需设计，风险可接受

---

## Epic 质量评审（Step 5 输出）

### 整体评审标准

对照创建 Epic & Story 的最佳实践逐一审查 10 个 Epic、51 个 Story。

---

### 🔴 严重问题（建议在实现前处理）

#### 问题 1：多个 Story 使用"作为平台"技术性 Actor（共 7 处）

以下 Story 以系统/平台为主体，而非真实用户，属于技术里程碑而非用户故事：

| Story | 技术 Actor | 描述 |
|-------|-----------|------|
| Story 3.1 | 作为平台 | Celery + Redis 任务队列基础设施搭建 |
| Story 3.2 | 作为平台 | PostgreSQL 历史数据缓存层 |
| Story 3.3 | 作为平台 | E2B 沙箱集成与策略安全执行 |
| Story 7.2 | 作为平台 | Celery Beat 定时执行模拟策略 |
| Story 8.3 | 作为平台 | 支付回调处理与套餐激活 |
| Story 8.4 | 作为平台 | Celery Beat 月度额度重置 |
| Story 9.2 | 作为平台 | 邮件通知异步发送 |

**影响评估**：这些 Story 的验收标准清晰、可测试，且是系统必需的后台行为（定时任务、Webhook、异步队列）。在许多团队中，"作为系统/平台"类 Story 被接受为 Platform Story 模式的合法用法。**建议**：保留这些 Story，但在 Sprint Planning 时明确区分这是"平台能力 Story"，不影响用户可见价值计算。

#### 问题 2：Story 2.4 对 Epic 10 存在显式前向依赖

Story 2.4（账号注销）验收标准包含：
> "该用户已发布策略的处理逻辑由 Epic 10 Story 10.x 实现（本 Story 仅标记用户状态）"

**问题**：FR6（注销账号并删除所有个人数据）需要 Story 2.4 + Story 10.7 联合实现才算完整。如果 Epic 2 开发完成后未完成 Epic 10，FR6 的"删除所有数据"承诺未兑现，存在合规风险（《个人信息保护法》）。

**建议**：在 Story 2.4 验收标准中明确说明"Epic 完成标准：Story 2.4 + Story 10.7 均合并后，FR6 验收通过"，并将两者排入同一 Sprint 或相邻 Sprint。

#### 问题 3：Story 1.6 CLI 包含桩实现（显式前向依赖）

Story 1.6 明确标注：
> "注：qys backtest 和 qys import 在本 Epic 中为桩实现，打印说明信息，将在 Epic 3/Epic 5 中完整集成"

**问题**：Story 1.6 在 Epic 1 中不可独立完成——其 `backtest` 和 `import` 子命令需要 Epic 3 和 Epic 5 的实现才能真正工作。这违反了 Story 独立性原则。

**建议**：可接受的处理方式——桩实现是一种合理的增量开发策略，只要在 Epic 3 和 Epic 5 中有相应 Story 完成全功能集成，并在 Epic 1 Story 1.6 验收标准中明确"桩实现验收通过，完整实现在 Epic 3/5 中"。**当前文档已做到此处理，风险可接受。**

---

### 🟠 重要问题

#### 问题 4：数据库表创建分散在多个 Story 的验收标准中

多处 Story 将数据库 migration 作为其第一条验收标准（Given/When/Then 语法）：
- Story 2.1 AC 1：`users` 和 `refresh_tokens` 表创建
- Story 3.1 AC 3-4：`backtest_jobs` 和 `user_quota` 表创建
- Story 7.2 AC 1：`simulation_records` 和 `simulation_positions` 表创建
- Story 9.1 AC 1：`notifications` 表创建

**评估**：每个 Story 在其首个 AC 中创建所需表格的"即时创建"模式实际上是合理的——它确保表在最早需要的时候创建，避免了前置全量数据库 migration 的维护负担。**这是可接受的做法**，不是严重问题。

---

### 🟡 轻微问题

#### 问题 5：Epic 1 纯技术定位，对非开发者用户价值不直观

Epic 1（平台基础 & QYSP 策略格式）的 8 个 Story 完全面向策略开发者（SDK、CLI、模板库）和平台工程（uv workspace 初始化）。对于以量化小白为核心用户的平台，Epic 1 对核心用户群无直接价值，需要等到 Epic 3 才能看到端到端体验。

**建议**：在 Sprint Review 时准备好对非技术利益相关者的说明："Epic 1 是让后续所有 Epic 成为可能的技术基础"。此顺序是合理的架构决策，不影响整体规划合理性。

#### 问题 6：Epic 顺序中 Epic 4（新手引导）依赖 Epic 3（回测引擎）

Epic 4 需要 Epic 3 的回测引擎才能真正引导用户"完成首次回测"（Story 4.2），这个顺序是合理的，但意味着新手引导无法在回测引擎完成前进行完整验收测试。**已通过 Epic 编号顺序隐式解决，无需额外处理。**

---

### 验收标准质量评估

抽样检查部分关键 Story 的验收标准：

| Story | Given/When/Then 格式 | 可测试性 | 错误场景 | 评分 |
|-------|---------------------|---------|---------|------|
| Story 2.1（注册） | ✅ 标准 BDD | ✅ 具体 | ✅ 429 错误、重发限制 | ⭐⭐⭐⭐ |
| Story 3.4（回测提交） | ✅ 标准 BDD | ✅ 具体 | ✅ 额度超限 429 | ⭐⭐⭐⭐ |
| Story 3.5（回测报告） | ✅ 标准 BDD | ✅ 引用 NFR 编号 | ⚠️ 缺少加载失败场景 | ⭐⭐⭐ |
| Story 5.3（一键导入） | ✅ 标准 BDD | ✅ 具体 | ✅ 重复导入检查 | ⭐⭐⭐⭐ |
| Story 8.3（支付回调） | ✅ 标准 BDD | ✅ 具体 | ✅ 重复回调幂等 | ⭐⭐⭐⭐⭐ |
| Story 10.5（审计日志） | ✅ 标准 BDD | ✅ 具体 | ✅ 只读、不可篡改 | ⭐⭐⭐⭐⭐ |

**总体质量评价**：验收标准普遍使用 Given/When/Then 格式，且绑定了具体 API 路径、FR 编号和 NFR 编号，可测试性强，质量较高。

---

## 最终评估（Step 6 输出）

### 总体就绪状态

## ✅ 就绪（READY）

项目规划整体质量良好，FR 覆盖完整（65/65，100%），验收标准可测试，架构文档详细。但以下问题需在开始实现前解决或明确决策。

---

### 关键问题汇总（按优先级排序）

| 优先级 | 问题 | 影响范围 | 建议行动 |
|--------|------|---------|---------|
| ✅ P0 已解决 | CTA 颜色：已确认黑色（`#1A1A1A`），PRD NFR26 已更新 | 所有页面实现 | 已完成 |
| ✅ P0 已解决 | QYSP-FRs 已正式纳入主 PRD"开发者工具需求"章节 | Epic 1 全部 8 个 Story | 已完成 |
| 🟠 P1 | Story 2.4 与 Story 10.7 前向依赖导致 FR6 不完整 | 用户注销功能合规性 | 将 Story 2.4 与 10.7 排入相邻 Sprint，明确联合验收条件 |
| 🟠 P1 | Mobile 端功能范围未在 PRD 中明确（UX 已定义 40% 功能） | 移动端开发范围 | 在 PRD 或架构文档中补充移动端功能范围说明 |
| 🟡 P2 | 7 个 Story 使用"作为平台"技术性 Actor | Sprint 规划 | 在 Sprint Planning 中将其标记为 Platform Story，说明不直接产生用户可见价值 |
| 🟡 P2 | 管理后台（Epic 10）无 UX 设计 | Epic 10 实现 | 开发时参照现有组件库按需设计，或预留 1 次设计评审 |

---

### 正向发现（已做好的部分）

| 维度 | 状态 | 详情 |
|------|------|------|
| FR 覆盖 | ✅ 完整 | 65/65 平台 FR 全部覆盖，0 缺失 |
| NFR 可量化 | ✅ 优秀 | 29 条 NFR 均有具体测量标准（时间/百分比/SLA）|
| 验收标准 | ✅ 良好 | BDD 格式普及，绑定 FR/NFR 编号，可测试性强 |
| 架构对齐 | ✅ 详细 | 19 条 ARCH 约束已在 Epics 中反映（ARCH-1~ARCH-19）|
| UX 对齐 | ✅ 良好 | UX 规范与 PRD NFR 高度一致，无重大架构冲突 |
| Story 数量 | ✅ 适量 | 51 个 Story / 10 个 Epic，平均 5.1 个/Epic，规模合理 |
| 数据库设计 | ✅ 完整 | 17 张核心表均有对应 Story 创建和验收 |

---

### 推荐的开始前行动（实施前检查清单）

- [ ] **P0：解决 CTA 颜色冲突** — 与设计方确认：CTA 按钮是红色还是黑色？更新 PRD NFR26 措辞使其与 UX 规范一致
- [ ] **P0：QYSP-FR 正式化** — 在主 PRD 中新增"开发者工具需求"章节，将 QYSP-FR1~FR11 正式列入
- [ ] **P1：Story 2.4 + 10.7 排期对齐** — Sprint Planning 时确认两个 Story 在相邻 Sprint 完成，避免 FR6 合规漏洞
- [ ] **P1：补充 Mobile 功能范围说明** — 在 PRD"实施考量"章节补充"移动端仅提供监控视图（约 40% 功能），不支持回测配置和策略发布操作"
- [ ] **P2：管理后台 UX 计划** — 确认 Epic 10 开发时的 UI 决策方式（参照现有组件 / 专项设计 / 低保真原型）

---

**报告生成时间：** 2026-03-15
**评估范围：** PRD（65 FR + 29 NFR）、Architecture、10 个 Epic / 51 个 Story、UX 设计规范
**发现问题总数：** 6 项（2 项严重 P0 · 2 项重要 P1 · 2 项轻微 P2）



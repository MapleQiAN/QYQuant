# Story 4.3: 帮助文档与 FAQ 随时访问

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

作为用户，
我希望随时访问帮助文档和 FAQ，了解基础量化概念，
以便看不懂回测指标时能自助找到解释。

## Acceptance Criteria

1. **Given** 用户点击页面帮助入口或指标旁的 ❓ 图标
   **When** 帮助面板展开
   **Then** 显示常见问题分类：什么是回测、什么是夏普比率、什么是最大回撤等（FR9）
   **And** 每个核心指标名称旁有 ❓ 图标，点击弹出该指标的简单中文解释
   **And** 帮助内容为静态 Markdown 渲染，无需外部服务

## Tasks / Subtasks

- [ ] Task 1: 帮助内容数据准备 (AC: #1)
  - [ ] 1.1 创建 `frontend/src/data/help-content.ts` — 定义帮助文档内容数据结构（分类 + FAQ 条目）
  - [ ] 1.2 编写帮助内容：至少覆盖以下分类及条目：
    - 基础概念类：什么是量化回测、什么是策略、什么是标的
    - 核心指标类：夏普比率、最大回撤、累计收益率、年化收益率、胜率、盈亏比、Alpha、Beta、信息比率、卡尔马比率、索提诺比率
    - 平台操作类：如何运行回测、如何导入策略、如何开启模拟托管、回测额度说明
  - [ ] 1.3 每个指标解释控制在 2-3 句话，使用通俗中文，避免公式和专业术语堆砌；适当用比喻帮助小白理解
  - [ ] 1.4 数据结构设计：`{ id: string, category: string, question: string, answer: string, relatedMetricKey?: string }`，`relatedMetricKey` 用于将 FAQ 条目关联到具体指标名（供 ❓ 图标查询）
- [ ] Task 2: HelpPanel 侧滑面板组件 (AC: #1)
  - [ ] 2.1 创建 `frontend/src/components/help/HelpPanel.vue` — 右侧滑出面板（Slide Panel 模式，参考 UX 规范弹窗模式表）
  - [ ] 2.2 面板宽度：桌面端 400px，移动端全屏；使用 `position: fixed; right: 0; z-index: 200`
  - [ ] 2.3 面板头部：标题"帮助中心" + 关闭按钮（X 图标，44×44px 最小点击区域）
  - [ ] 2.4 分类筛选：使用胶囊形 Chip 横向排列（参考 UX 搜索与筛选模式），支持"全部/基础概念/核心指标/平台操作"切换
  - [ ] 2.5 搜索框：面板顶部，胶囊形输入框（浅灰背景 `#F8FAFC`），支持关键词实时过滤 FAQ 条目
  - [ ] 2.6 FAQ 列表：使用手风琴（Accordion）展开/折叠模式，点击问题展开答案，同一时间只展开一个
  - [ ] 2.7 面板打开/关闭动画：右侧滑入/滑出，duration 250ms，支持 `prefers-reduced-motion`
  - [ ] 2.8 点击面板外部遮罩层关闭面板（半透明黑色遮罩 `rgba(0,0,0,0.3)`）
  - [ ] 2.9 使用 Vue `<Teleport to="body">` 挂载到 body，避免 z-index 层级冲突
- [ ] Task 3: MetricTooltip 指标解释组件 (AC: #1)
  - [ ] 3.1 创建 `frontend/src/components/help/MetricTooltip.vue` — 指标名旁的 ❓ 图标 + 弹出解释
  - [ ] 3.2 Props：`metricKey: string`（对应 help-content.ts 中的 relatedMetricKey）
  - [ ] 3.3 交互：hover 触发，300ms 延迟后显示 tooltip（参考 UX 弹窗模式表 Tooltip 规范）；移动端改为 click 触发
  - [ ] 3.4 Tooltip 样式：白色背景 + 细边框 `#E5E5E5` + 轻阴影，圆角 8px，最大宽度 280px，字号 14px
  - [ ] 3.5 内容：从 help-content.ts 按 metricKey 查找对应 FAQ answer 字段
  - [ ] 3.6 位置：自动检测空间，优先展示在上方，空间不足时展示在下方
- [ ] Task 4: 全局帮助入口集成 (AC: #1)
  - [ ] 4.1 在 TopNav 右侧区域添加帮助按钮（❓ 圆形图标按钮），点击打开 HelpPanel
  - [ ] 4.2 帮助按钮位置：通知铃铛按钮左侧，复用 `.nav-btn` 样式（40×40px，hover 变色）
  - [ ] 4.3 在 `App.vue` 中引入 HelpPanel 组件，使用 Pinia 或 `provide/inject` 管理面板开关状态
- [ ] Task 5: MetricTooltip 集成到回测报告页 (AC: #1)
  - [ ] 5.1 在 `BacktestResultView.vue` 的各指标名称旁添加 `<MetricTooltip metricKey="sharpe_ratio" />` 等
  - [ ] 5.2 需要添加 tooltip 的指标：累计收益率、年化收益率、最大回撤、夏普比率、胜率、盈亏比及其他已展示的指标
  - [ ] 5.3 在 `StatCard.vue` 组件中预留 slot 或 prop 支持在标题旁显示 ❓ 图标
- [ ] Task 6: 键盘快捷键与快速访问 (AC: #1)
  - [ ] 6.1 支持 `?` 或 `F1` 键盘快捷键打开帮助面板（全局 keydown 监听，排除输入框聚焦状态）
  - [ ] 6.2 面板打开时按 `Escape` 关闭
  - [ ] 6.3 面板内支持 Tab 键导航 FAQ 条目
- [ ] Task 7: 样式与响应式 (AC: #1)
  - [ ] 7.1 桌面端（≥1024px）：400px 宽侧滑面板，不覆盖整屏
  - [ ] 7.2 平板端（768-1023px）：320px 宽侧滑面板
  - [ ] 7.3 移动端（<768px）：全屏面板，底部 padding 适配底部导航栏
  - [ ] 7.4 所有文字使用 CSS 变量（`--font-size-sm`、`--font-size-base` 等），遵循设计令牌
  - [ ] 7.5 手风琴展开/折叠动画：max-height 过渡，duration 200ms
- [ ] Task 8: 无障碍 (AC: #1)
  - [ ] 8.1 HelpPanel：`role="dialog"` + `aria-label="帮助中心"` + focus trap（打开时焦点移入，关闭时焦点还原）
  - [ ] 8.2 FAQ 手风琴：`role="button"` + `aria-expanded` + `aria-controls`
  - [ ] 8.3 MetricTooltip：`role="tooltip"` + `aria-describedby` 关联
  - [ ] 8.4 帮助按钮：`aria-label="打开帮助中心"`
  - [ ] 8.5 所有交互元素最小 44×44px，focus 样式 `2px solid #E53935 + outline-offset: 2px`
- [ ] Task 9: 测试 (AC: #1)
  - [ ] 9.1 HelpPanel 单元测试：打开/关闭、分类筛选、搜索过滤、键盘快捷键、无障碍属性
  - [ ] 9.2 MetricTooltip 单元测试：hover 显示/隐藏、内容正确性、位置计算
  - [ ] 9.3 help-content 数据测试：所有指标 key 有对应解释、无空内容、分类完整
  - [ ] 9.4 集成测试：TopNav 帮助按钮 → HelpPanel 打开 → 搜索 → 展开 FAQ

## Dev Notes

### 架构约束与模式

- **前端框架**: Vue 3 + Composition API + `<script setup>` + TypeScript
- **状态管理**: Pinia stores（组件级状态用 `ref()`，面板开关状态用 provide/inject 或 Pinia）
- **CSS**: 自定义 CSS 设计令牌体系（无 UI 组件库），CSS 变量在 `global.css`
- **无 i18n 框架**: TopNav 中使用了 `$t()` 但项目中未发现 i18n 配置；帮助内容直接用中文硬编码
- **组件命名**: PascalCase.vue（`HelpPanel.vue`、`MetricTooltip.vue`）
- **测试**: 组件同目录 co-located（`HelpPanel.vue` + `HelpPanel.test.ts`）

### 本 Story 的技术特点

本 story 是**纯前端实现**，无需新增后端 API 或数据库变更：
- 帮助内容为静态数据，存储在 `frontend/src/data/help-content.ts`
- 不依赖任何外部 Markdown 渲染库 — FAQ 答案为纯文本/HTML 字符串，直接渲染
- 不需要用户认证（帮助面板对所有用户可见，含未登录状态）

### UX 设计要求

- **面板模式**: Slide Panel（UX 规范弹窗模式表：右侧滑入，不覆盖整屏）
- **Tooltip 模式**: hover 触发，300ms 延迟（UX 规范弹窗模式表）
- **搜索与筛选**: 胶囊形搜索框 + Chip 筛选标签（UX 搜索与筛选模式）
- **设计令牌**:
  - 卡片/面板圆角: 16px（弹窗/面板专用）
  - 输入框背景: `#F8FAFC`，聚焦时蓝色边框
  - CTA 按钮: `#1A1A1A`（如有按钮场景）
  - 关闭按钮色: `#94A3B8`
  - 分类 Chip 激活态: 依据项目主色填充
  - 主文本: `#1E293B`，次要文本: `#64748B`，辅助文本: `#94A3B8`
- **渐进式信息披露**: FAQ 手风琴默认全部折叠，点击展开单个，避免信息过载
- **"小白优先"原则**: 指标解释使用通俗中文 + 生活类比，不堆砌公式

### 指标解释内容指南

为每个核心指标提供：
1. **一句话定义** — 用最通俗的语言
2. **生活类比** — 帮助小白理解
3. **判断标准** — 这个数字是高好还是低好

示例：
- **夏普比率**: 衡量每承担一份风险能换来多少收益。类比：同样辛苦工作，夏普比率高的策略"性价比"更高。一般 >1 为好，>2 为优秀。
- **最大回撤**: 策略运行期间，从最高点到最低点亏了多少。类比：过山车从最高点往下冲的深度。数字越小越好，<20% 通常可接受。
- **累计收益率**: 策略从开始到结束一共赚了百分之多少。正数表示赚钱，负数表示亏钱，数字越大越好。

### 前端组件规范

- **组件路径**: `frontend/src/components/help/` 目录（新建 help 子目录）
- **数据路径**: `frontend/src/data/help-content.ts`
- **HelpPanel 挂载**: 使用 `<Teleport to="body">`，z-index: 200（低于引导 overlay 的 1000，高于 TopNav 的 100）
- **MetricTooltip**: 轻量级，不引入第三方 tooltip 库（如 Tippy.js），自行用 CSS + JS 实现定位
- **图标**: 沿用项目内 inline SVG `h()` 渲染方式（参考 TopNav.vue 的 BellIcon 实现模式），不引入图标库

### 集成点

| 集成位置 | 修改内容 |
|---------|---------|
| `TopNav.vue` | nav-right 区域添加帮助 ❓ 按钮 |
| `App.vue` | 引入 `<HelpPanel />` 组件 |
| `BacktestResultView.vue` | 指标名旁添加 `<MetricTooltip>` |
| `StatCard.vue` | 预留 tooltip slot 或 prop |

### 防踩坑提醒

- **不要** 引入 Markdown 渲染库（如 marked、markdown-it） — FAQ 答案直接使用 HTML/纯文本，保持零新增依赖
- **不要** 引入第三方 Tooltip 库（如 Tippy.js、floating-ui） — 自行实现轻量 tooltip 定位
- **不要** 创建后端 API — 帮助内容全部为前端静态数据
- **不要** 使用 localStorage 缓存帮助面板状态 — 每次打开都是新鲜状态
- **不要** 在 HelpPanel 内使用路由导航 — 面板是 overlay 层，不影响当前页面
- **不要** 使用 `position: absolute` 做面板定位 — 必须用 `position: fixed` + `<Teleport>` 避免父容器 overflow 裁剪
- **不要** 将 MetricTooltip 做成全局指令 — 保持为独立组件，Props 传入 metricKey

### Previous Story Intelligence

Story 4.2（首次回测全流程引导）建立的关键模式：
- **组件目录**: `frontend/src/components/onboarding/` — 本 story 使用独立的 `help/` 子目录
- **高亮/overlay 方案**: z-index: 1000 + `clip-path` 镂空 — 帮助面板 z-index 应低于引导 overlay（使用 200）
- **状态管理**: Pinia `useUserStore()` — 帮助面板开关不需要持久化，可用简单 `ref()` 或 provide/inject
- **设计令牌**: 12px 圆角（卡片）、16px 圆角（面板）、20px 内边距、#1A1A1A CTA、#94A3B8 关闭按钮
- **无障碍**: Tab 导航、aria-label、44×44px 最小尺寸、2px 红色 focus 边框

### Git Intelligence

近期提交模式：
- `caf64e4` 实现了回测报告页与权益曲线指标展示 — 确认 `BacktestResultView.vue` 已存在，包含 StatCard 指标展示
- `1e29ab9` 实现策略库页面并接入鉴权接口 — 确认前端已有认证集成
- `c5cf6e0` 完善策略库元数据管理并新增回测错误提示 — 确认 ErrorDisplay 组件已存在
- 项目使用 inline SVG + `h()` 渲染图标（TopNav.vue 模式），不使用图标库

### Project Structure Notes

- 新建目录: `frontend/src/components/help/`（HelpPanel.vue、MetricTooltip.vue）
- 新建文件: `frontend/src/data/help-content.ts`（帮助内容静态数据）
- 修改文件: `TopNav.vue`（添加帮助按钮）、`App.vue`（引入 HelpPanel）、`BacktestResultView.vue`（添加 MetricTooltip）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.3]
- [Source: _bmad-output/planning-artifacts/prd.md#FR9 — 用户可以随时访问帮助文档/FAQ 了解基础量化概念]
- [Source: _bmad-output/planning-artifacts/prd.md#学习功能分层 — MVP 帮助文档/FAQ 低复杂度]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#UX一致性模式规范 — Tooltip/Slide Panel/搜索筛选模式]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#情感设计原则#1 — 赋能而非炫技，专业术语旁配人话解释]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#组件策略 — MetricTooltip P2 组件]
- [Source: _bmad-output/planning-artifacts/architecture.md#前端架构 — Vue 3 + Pinia + 自定义 CSS]
- [Source: _bmad-output/planning-artifacts/architecture.md#实现模式 — 命名规范/组件策略]
- [Source: _bmad-output/implementation-artifacts/4-2-首次回测全流程引导.md — 前置 story 模式与无障碍约定]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

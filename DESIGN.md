# QY Quant Design

## 1. 适用范围

本文件定义 QY Quant 当前前端视觉基线。目标不是讲历史，而是给后续页面、组件、重构直接落地。

本文件只基于以下真源：

- `E:/QYQuant/frontend/public/design-preview.html`
- `E:/QYQuant/frontend/src/styles/global.css`
- `E:/QYQuant/frontend/src/views/BacktestResultView.vue`
- `E:/QYQuant/frontend/src/components/SideNav.vue`
- `E:/QYQuant/frontend/src/components/TopNav.vue`
- `E:/QYQuant/frontend/src/components/StatCard.vue`
- `E:/QYQuant/frontend/src/components/backtest/StrategyParamsPanel.vue`
- `E:/QYQuant/frontend/src/components/backtest/BenchmarkComparison.vue`
- `E:/QYQuant/frontend/src/components/backtest/TradeTable.vue`

明确排除：

- `E:/QYQuant/DESIGN_SYSTEM_UPDATE.md`
- `E:/QYQuant/COMPONENT_DESIGN_UPGRADE.md`

## 2. 设计定位

QY Quant 当前设计语言不是传统量化黑绿终端，也不是 SaaS 紫色玻璃风。

定位应固定为：

- `Bauhaus Quant`
- `企业级金融感`
- `数据优先`
- `浅底高对比`
- `几何装饰 + 强边框`

界面气质要点：

- 背景干净，不花。
- 信息层级靠字号、粗细、边框、留白，不靠大面积渐变。
- 装饰只做点睛：圆、方块、斜切块。
- 数值始终比说明更抢眼。
- 视觉上要像“正式报告 + 专业控制台”，不是营销页。

## 3. 当前视觉真源

当前视觉真源是 `global.css`，不是 `tokens.ts`。

现状：

- `global.css` 已切到 Bauhaus 浅色体系。
- `design-preview.html` 与 `BacktestResultView.vue` 已高度对齐。
- `src/styles/tokens.ts` 仍保留旧紫色 token，且当前未被代码引用。
- `theme.ts` 仍保留 `dark | light` 语义，但 `global.css` 里 `:root` 与 `:root[data-theme="dark"]` 使用同一套浅色 Bauhaus token。

结论：

- 新页面、新组件、一切视觉改动，以 `global.css` 为准。
- `tokens.ts` 视为遗留文件，不得再作为新设计依据。
- 在主题系统未真正分化前，不要按“暗色默认站点”思路设计新 UI。

## 4. 核心 Token

### 4.1 颜色

主色板来自 `design-preview.html` 与 `global.css` 的交集。

| 角色 | 值 | 用途 |
| --- | --- | --- |
| 主蓝 | `#1976d2` | 主导航激活、链接、信息强调、图表主线 |
| 主蓝浅底 | `rgba(25, 118, 210, 0.08)` | 轻提示、选中背景、信息 badge |
| 强调黄 | `#f9a825` | 主按钮、重点装饰、提醒但非危险 |
| 风险红 | `#d4393b` | 风险、亏损、警示、几何装饰 |
| 稳定绿 | `#2e7d32` | 正向结果、收益、健康状态 |
| 点缀青 | `#46A9A0` | 点缀图形、辅助几何装饰、局部视觉调剂 |
| 背景米灰 | `#f3f2ee` | 全局背景 |
| 主面板白 | `#ffffff` | 卡片、导航、弹层 |
| 提升面 | `#fafafa` | 表头、tile、弱分层区 |
| 悬停面 | `#f5f5f2` | hover 背景 |
| 主文本 | `#111111` | 标题、主值 |
| 次文本 | `#6b6b6b` | 正文说明 |
| 弱文本 | `#8a8a8a` | 辅助说明 |
| 主边框 | `#1a1a1a` | 2px 强边框 |
| 弱边框 | `#e0e0dc` | 内部分隔、tile 边界 |

市场涨跌默认遵循当前实现：

- `CN style`: `涨 = 红`, `跌 = 绿`
- 如切到 `data-market-style="us"`，再反转

### 4.2 字体

- 主字体：`DM Sans`, `Noto Sans SC`
- 等宽字体：`DM Mono`

规则：

- 标题、导航、标签：无衬线粗体
- 数值、日期、ID、比率：等宽字体
- 英文缩写、状态标签可大写
- 中文正文保持克制，不做过度 letter-spacing

### 4.3 边框、圆角、阴影

- 卡片主边框：`2px solid var(--color-border)`
- 默认圆角：`12px / 16px`
- 大卡片阴影：轻，不漂浮，不霓虹
- 设计关键词：`粗边框 > 阴影`

### 4.4 间距

- 基准间距：`4 / 8 / 16 / 24 / 32 / 48`
- 常规卡片内边距：`20-24px`
- 大区块间距：`24-32px`
- 页面左右留白：桌面端 `24-32px`

## 5. 版式语法

### 5.1 总体结构

标准页结构：

1. 左侧固定导航
2. 顶部工具条
3. 主内容纵向分块
4. 每个区块自成卡片

布局原则：

- 页面先看大块，再看卡片，再看 tile。
- 一屏内避免超过 2 层嵌套卡片。
- 横向并列优先 `2 列` 或 `4 列`，少用 `3 列`。

### 5.2 装饰语法

允许的装饰只有三类：

- 角落圆点
- 斜切方块
- 底部色条

装饰色允许范围：

- 现有主蓝、强调黄、风险红、稳定绿
- 额外允许 `#46A9A0` 作为点缀图形色

限制：

- 装饰必须低频出现。
- 装饰只占角落，不进入主阅读区。
- 单卡片只保留 1 个主装饰。

## 6. 页面信息架构

`design-preview.html` 对应的回测报告结构，已是当前最强基线。后续相关页面按此组织：

1. `Page Header`
2. `Report Summary`
3. `Core Metrics Grid`
4. `Analysis Grid`
5. `Support Grid`
6. `Chart Sections`
7. `Trade Table / Detail`
8. `Disclaimer / Footer`

判断标准：

- 先给结论，再给指标，再给证据。
- 先给摘要，再给全量明细。
- 报告页必须能在不读表格情况下看懂结果。

## 7. 组件规范

### 7.1 SideNav

侧边栏是“白底 + 强边框 + 几何角标”。

规则：

- 激活项用实心主蓝底。
- hover 只变浅底，不加复杂动画。
- 品牌区可有装饰圆形，但透明度要低。
- Premium 徽章允许局部特殊色，但不能反向污染全站主色。

### 7.2 TopNav

顶栏要轻，不抢主内容。

规则：

- 高度固定，白底，底边 2px。
- 搜索框、图标按钮都是轻量胶囊。
- 激活 tab 用实心深色或主色块。
- 用户菜单用白底强边框，不做毛玻璃。

### 7.3 按钮

按钮优先级：

- `Primary`: 黄底，黑字，强边框
- `Secondary`: 白底，黑边
- `Ghost`: 无底，hover 才出现底色
- `Danger`: 红底，谨慎使用

按钮动作反馈：

- 只允许轻微上浮 `translateY`
- 不要弹簧感，不要夸张缩放

### 7.4 Badge / Chip / Pill

规则：

- 小而硬朗
- 圆角胶囊
- 强调靠边框和文字，不靠高饱和大底色
- 标签字体偏粗，字号偏小

### 7.5 指标卡

指标卡是当前系统最关键组件之一。

规则：

- 顶部小标签，全大写或准大写
- 主值必须最大、最重、等宽
- 底部允许一条状态色条
- 卡片本体白底，不用大面积渐变

主值颜色规则：

- 正值：`positive`
- 负值：`negative`
- 中性指标：黑字

### 7.6 分析面板

分析面板用于“解释指标”，不是重复指标。

规则：

- 标题 + 副标题 + 列表正文
- 每条 insight 用小圆点或小标记引导
- 诊断类内容用左右对齐行
- 装饰透明度必须低，不影响阅读

### 7.7 支撑面板

如 `StrategyParamsPanel`、`BenchmarkComparison`、风险与信号面板。

规则：

- 外层大卡片
- 内部用 `tile` 分块
- tile 背景略高于主面，但不脱离体系
- 参数、symbol、版本、收益率都用 mono

### 7.8 图表区

图表容器规则：

- 外层统一卡片
- 顶部统一 section header
- 图表说明短句化
- 图表本身是主角，容器样式不能抢戏

图表配色：

- 主净值线：蓝
- 回撤：红
- 胜负或信号：跟随正负色
- 网格线：浅灰

### 7.9 表格

表格是报告末端“证据层”。

规则：

- 表头浅底 + 强分隔
- 行 hover 轻微高亮
- 数字右对齐
- 时间、价格、数量、PnL 全部 mono
- 买卖方向用 badge，不用纯文本

## 8. 文案与数据表达

文案风格：

- 直给
- 短句
- 少形容词
- 少营销口吻

推荐写法：

- “策略表现优于基准，风险可控”
- “超额收益 +89.2%”
- “震荡阶段信号噪声偏高”

避免写法：

- “革命性提升”
- “令人惊艳的结果”
- “强大而优雅的金融体验”

## 9. 动效规范

当前系统适合低动效。

允许：

- hover 变底色
- 轻微上浮
- 淡入
- 通知点脉冲

避免：

- 大面积 parallax
- 长时渐变流动
- 玻璃折射感
- 霓虹发光

时长建议：

- `150ms`: hover / focus
- `200ms`: 普通切换
- `300ms`: 区块进入

## 10. 响应式规则

断点按当前实现：

- `<= 1024px`: 两列逐步收缩
- `<= 900px`: 主要分析区改单列
- `<= 640px`: 指标、摘要、tile 多改为单列
- `<= 480px`: 收紧内边距，保留可读性优先

移动端原则：

- 不保留复杂横向并排
- 先保 summary，再保指标，再保图表
- 表格允许横向滚动，不强压缩字段

## 11. 实施准则

后续任何新界面，必须遵守：

1. 先复用 `global.css` token，不要新起一套颜色。
2. 先复用现有 card / badge / button / section header 语法。
3. 数字必须默认考虑 `tabular-nums`。
4. 主卡片默认白底 + 2px 深边框。
5. 几何装饰只做辅助，不做主题图案。
6. 页面先有摘要，再有细节。
7. 没有明确理由，不引入紫色、赛博蓝紫渐变、重玻璃效果。

## 12. 待收敛项

当前实现里仍有两个设计债：

- `E:/QYQuant/frontend/src/styles/tokens.ts` 仍是旧紫色 token，且未被引用。
- `E:/QYQuant/frontend/src/styles/theme.ts` 保留暗色语义，但当前视觉并未真正提供独立暗色方案。

在这两个问题解决前，团队执行口径应固定为：

- 视觉规范看 `global.css`
- 页面范式看 `BacktestResultView.vue`
- 预览稿看 `design-preview.html`

## 13. 一句话原则

QY Quant 的正确方向不是“更炫”，而是“更像一份专业、清晰、可快速阅读的量化报告”。

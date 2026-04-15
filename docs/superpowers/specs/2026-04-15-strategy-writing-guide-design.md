# 策略创建页增加“策略编写指导”设计稿

## 背景

当前策略创建页 `frontend/src/views/NewStrategyView.vue` 仅提供两类入口：

- 从零创建策略基础信息
- 从文件导入 `.qys` / `.py` / `.zip`

对于第一次接触 QYSP 策略格式的用户，页面缺少“如何开始写一个可导入策略”的即时指导。仓库中已经存在策略格式规范文档 `docs/strategy-format/README.md`，但它更偏格式说明与字段参考，不足以在创建页内快速帮助新手启动。

本次设计目标是在不削弱“创建 / 导入”为主任务的前提下，在策略创建页增加一个并列的指导卡片，并配套一篇前端新手教程页，同时保留深入规范入口。

## 目标

- 在策略创建页提供低打断、可直接上手的编写指导
- 为新手提供一篇面向实操的教程页，而不是只给格式规范
- 复用已有 `docs/strategy-format/README.md` 的规范内容，避免维护两套完整规范
- 保持现有页面视觉节奏，不让文档内容压过创建与导入动作

## 非目标

- 不在创建页内嵌完整长文档或长篇教程
- 不改动现有策略创建 API、导入 API、后端数据结构
- 不在本次设计中实现 Markdown 渲染系统
- 不重写 `docs/strategy-format/README.md` 的完整规范内容

## 用户问题

新手用户进入“创建策略”页面时，常见阻塞点包括：

- 不知道一个策略包最少需要哪些文件
- 不知道 `strategy.json` 与 `src/strategy.py` 的关系
- 不清楚 `event_v1` 最小可运行示例长什么样
- 不知道写完后该如何验证或导入
- 看到“导入”入口，但不知道应导入什么格式的产物

## 方案总览

采用“组合式引导”：

1. 在 `NewStrategyView` 中新增第三张并列卡片，作为补充资源而非主流程
2. 卡片中展示可立即上手的摘要内容：
   - 3 步开始编写
   - 最小目录结构
   - 最小 `on_bar` 示例
   - 两个入口按钮
3. 新增一页前端教程页，面向新手讲清楚“怎么写”
4. 在卡片与教程页中都保留“查看规范文档”入口，指向现有规范内容

## 信息架构

### 1. 策略创建页

位置：

- 保持现有“从零创建”“文件导入”两张卡片
- 新增“策略编写指南”卡片，与前两张卡片保持同级布局
- 在桌面端采用三卡布局或兼容性良好的换行布局
- 在移动端保持单列堆叠，指导卡片位于创建/导入卡片之后

内容结构：

- 标题：`策略编写指南`
- 简介：强调“不会写策略也可以从这里开始”
- `3 步开始编写`
- 最小目录树
- 最小代码示例
- 主按钮：`查看新手教程`
- 次按钮：`查看规范文档`

设计原则：

- 指导卡片视觉权重低于创建和导入卡片
- 信息可扫描，尽量不需要滚动很久
- 代码示例和目录结构只展示“最小可开始版本”

### 2. 新手教程页

新增页面建议：`frontend/src/views/StrategyWritingGuideView.vue`

建议路由：

- 路径：`/strategies/guide`
- 路由名：`strategy-writing-guide`

页面目标：

- 面向第一次写 QYSP 策略的用户
- 用教程式结构解释如何从零写到可导入
- 与创建页卡片中的摘要内容保持一致但更完整

页面结构建议：

1. 顶部标题区
2. “你将完成什么”摘要
3. 最小目录结构
4. `strategy.json` 必填字段说明
5. `src/strategy.py` 最小示例
6. 导入 / 验证方式
7. 常见错误
8. 规范入口与返回策略创建页入口

### 3. 规范文档入口

规范入口不承载“教学”，只承载深入参考。

优先级顺序：

1. 前端内提供一个规范摘要或专门的规范阅读页，内容源于 `docs/strategy-format/README.md`
2. 如果当前项目没有成熟的文档渲染链路，则先使用稳定的跳转入口或静态承载方式

实现要求：

- 文案层面区分“新手教程”和“规范文档”
- 避免用户误以为两者是重复内容

## 页面内容设计

### 创建页指导卡片内容

建议卡片文案骨架：

- 标题：`策略编写指南`
- 说明：`先准备 strategy.json，再实现 src/strategy.py，最后导入或打包验证。`

3 步内容：

1. 定义 `strategy.json`
2. 编写 `src/strategy.py`
3. 导入 `.qys` 或用示例结构继续完善

最小目录结构示例：

```text
my-strategy/
├── strategy.json
└── src/
   └── strategy.py
```

最小代码示例：

```python
from qysp import BarData, Order, StrategyContext


def on_bar(ctx: StrategyContext, data: BarData) -> list[Order]:
    if data.close > float(ctx.parameters.get("threshold", 1.0)):
        return [ctx.buy(data.symbol, quantity=1)]
    return []
```

按钮行为：

- `查看新手教程`：跳转到新教程页
- `查看规范文档`：跳转到规范阅读入口

### 新手教程页内容

教程页建议使用编辑性较强的布局，而不是纯文档排版。页面内容应覆盖：

1. 为什么最少需要两个核心文件
2. `strategy.json` 里哪些字段必须先写
3. `entrypoint.path` / `entrypoint.callable` 如何对应到 Python 文件
4. `event_v1` 的最小函数签名和返回值约束
5. 参数如何从 `ctx.parameters` 中读取
6. 写完后如何导入现有系统
7. 常见错误示例：
   - 缺少 `strategy.json`
   - `entrypoint.path` 路径不匹配
   - `callable` 与 Python 函数名不一致
   - 返回值不是 `list[Order]`

## 数据与内容来源

### 复用内容

- 现有规范来源：`docs/strategy-format/README.md`
- 现有示例来源：`docs/strategy-format/examples/*`

### 前端呈现策略

- 创建页卡片中的目录结构和最小代码示例直接写在组件中
- 教程页内容以前端模板和短段落方式组织，不直接依赖 Markdown 渲染
- 规范页或规范入口的文本结构以现有 README 为准，减少重复维护

原因：

- 现有前端未体现出通用 Markdown 文档管线
- 直接在视图中维护短教程，更利于样式控制、国际化和测试

## 国际化设计

需要在以下文件新增文案：

- `frontend/src/i18n/messages/zh.ts`
- `frontend/src/i18n/messages/en.ts`

建议新增文案分组：

- `strategyNew.guideTitle`
- `strategyNew.guideHint`
- `strategyNew.guideSteps`
- `strategyNew.guidePrimaryAction`
- `strategyNew.guideSecondaryAction`
- `strategyGuide.*`

不建议把长代码块或目录树完整塞进 i18n：

- 代码块跨语言差异很小
- 放在 i18n 中会增加转义与维护复杂度
- 更适合作为组件常量或局部模板内容

## 组件与路由设计

### 需要修改的文件

- `frontend/src/views/NewStrategyView.vue`
- `frontend/src/router/index.ts`
- `frontend/src/i18n/messages/zh.ts`
- `frontend/src/i18n/messages/en.ts`

### 需要新增的文件

- `frontend/src/views/StrategyWritingGuideView.vue`
- `frontend/src/views/StrategyWritingGuideView.test.ts`
- 视需要补充 `frontend/src/views/NewStrategyView.test.ts`

### 可选抽取

如果 `NewStrategyView.vue` 变得过长，可抽取：

- `frontend/src/components/strategy/StrategyWritingGuideCard.vue`

本次优先原则：

- 如果新增卡片后页面仍清晰，则先不额外拆组件
- 若模板与样式明显膨胀，再进行抽取

## 交互流程

### 流程 A：首次写策略

1. 用户进入 `/strategies/new`
2. 用户看到“策略编写指南”卡片
3. 用户快速浏览 3 步、目录结构和最小示例
4. 用户点击 `查看新手教程`
5. 用户进入 `/strategies/guide`
6. 用户阅读完整说明后点击“返回策略创建”

### 流程 B：已有经验用户

1. 用户进入 `/strategies/new`
2. 用户直接执行创建或导入
3. 若需核对字段，再点击 `查看规范文档`

## 错误处理

本次为静态内容增强，错误处理重点在导航与可用性：

- 教程页入口必须有稳定路由，避免跳转到不存在页面
- 规范入口若暂不能做前端渲染，应提供稳定可访问的过渡方案
- 页面内按钮文本应明确区分“教程”和“规范”
- 若规范入口依赖外部静态资源，需提供最小降级文案

## 测试策略

### 单元/组件测试

建议新增或补充以下测试：

- `NewStrategyView` 渲染指导卡片
- 指导卡片中存在两个关键按钮
- 页面中出现目录结构或关键教学文案
- `StrategyWritingGuideView` 成功渲染关键章节
- 教程页中存在“返回策略创建”入口

### 路由测试

补充 `frontend/src/router/index.test.ts`：

- 新路由 `strategy-writing-guide` 注册成功
- 未登录访问策略教程页时遵循当前全站鉴权规则

### 视觉/布局回归关注点

- 桌面端三卡布局是否过窄
- 移动端卡片堆叠顺序是否自然
- 代码块在窄屏下是否溢出

## 验收标准

- 策略创建页出现并列的“策略编写指南”卡片
- 卡片中包含 3 步说明、目录结构、最小代码示例
- 卡片提供“查看新手教程”和“查看规范文档”两个入口
- 新手教程页可访问，并覆盖从目录结构到导入验证的基础流程
- 中英文文案完整
- 相关前端测试覆盖新入口和关键内容

## 风险与取舍

### 风险 1：创建页过重

控制方式：

- 卡片只放摘要，不放完整教程
- 保持指导卡片视觉权重低于主流程卡片

### 风险 2：教程与规范内容重复

控制方式：

- 教程讲“怎么开始”
- 规范讲“字段与约束全量说明”

### 风险 3：规范入口实现方式不一致

控制方式：

- 第一阶段先保证入口稳定
- 第二阶段再统一前端文档承载体验

## 实施建议

建议按以下顺序实现：

1. 增加创建页指导卡片
2. 新增教程页和路由
3. 补充中英文文案
4. 接入规范入口
5. 补测试并验证响应式布局

## 当前假设

- 当前仓库未暴露可直接读取的 GitNexus MCP 资源，因此本设计以源码和现有文档为准
- `RTK.md` 未在仓库附近定位到，本设计未引入其中潜在约束
- 规范入口具体承载方式可在实现阶段根据现有前端能力微调，但不改变本设计的信息架构

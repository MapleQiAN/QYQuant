---
stepsCompleted: [1, 2, 3, 4]
status: 'complete'
completedAt: '2026-03-15'
totalEpics: 10
totalStories: 51
frCoverage: '76/76'
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/prd-qystrategy-improvement.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
  - _bmad-output/planning-artifacts/prd-validation-report.md
---

# QYQuant - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for QYQuant, decomposing the requirements from the PRD, UX Design, and Architecture requirements into implementable stories.

---

## Requirements Inventory

### Functional Requirements

**来源：prd.md（平台级，65 条 FR）**

#### 用户管理（FR1-FR6）
- FR1: 用户可以通过手机号注册和登录平台
- FR2: 用户可以设置和修改个人主页信息（头像、昵称、个人简介）
- FR3: 用户可以查看当前订阅套餐等级和剩余回测额度
- FR4: 用户可以升级或降级订阅套餐
- FR5: 用户可以通过微信支付或支付宝完成套餐付费
- FR6: 用户可以注销账号并删除所有个人数据

#### 新手引导与学习（FR7-FR9）
- FR7: 新用户首次进入平台时可以体验互动式新手引导流程（3 步卡片）
- FR8: 新手引导可以将用户直接引导至完成首次回测操作
- FR9: 用户可以随时访问帮助文档/FAQ 了解基础量化概念

#### 量化回测（FR10-FR24）
- FR10: 用户可以上传 Python 策略代码文件发起回测
- FR11: 用户可以从策略库中选择已有策略发起回测
- FR12: 用户可以设定回测参数（标的、时间区间）
- FR13: 用户可以选择多标的组合进行回测
- FR14: 系统可以在沙箱环境中安全执行策略代码并返回结果
- FR15: 系统可以对接外部数据源获取历史行情数据
- FR16: 系统可以缓存已获取的历史数据以提升性能
- FR17: 用户可以查看回测报告，包含核心三指标（累计收益率、最大回撤、夏普比率）的醒目展示
- FR18: 用户可以查看完整的 11 项量化评价指标（折叠展示）
- FR19: 用户可以查看 Equity Curve 资金曲线图
- FR20: 用户可以查看回测区间内的买卖点标注
- FR21: 系统可以在代码执行出错时提供智能错误提示（含示例引导）
- FR22: 系统可以统计和扣减用户的回测次数额度
- FR23: 用户可以在回测界面看到剩余额度和计费规则说明
- FR24: 用户可以查看支持的 Python 依赖库清单

#### 策略广场（FR25-FR34）
- FR25: 用户可以浏览策略广场中的策略列表
- FR26: 用户可以查看策略详情页（名称、描述、展示指标、Equity Curve）
- FR27: 用户可以识别带有"平台验证回测"徽章的策略
- FR28: 策略广场可以展示人工运营的精选策略推荐位
- FR29: 用户可以将策略广场中的策略一键导入自己的策略库
- FR30: 用户可以对导入的策略一键发起回测试用
- FR31: 用户可以发布自己的策略到策略广场（免费分享模式）
- FR32: 策略发布者可以设置策略的展示指标
- FR33: 系统可以在发布时向用户展示代码保护机制说明和知识产权协议
- FR34: 系统可以保证策略代码对其他用户不可见、不可下载、不可导出

#### 社区互动（FR35-FR39）
- FR35: 用户可以在策略广场发布帖子
- FR36: 用户可以点赞帖子
- FR37: 用户可以评论帖子
- FR38: 用户可以收藏帖子
- FR39: 用户可以查看其他用户的个人主页

#### 模拟托管（FR40-FR48）
- FR40: 用户可以从策略库中选择策略创建模拟托管机器人
- FR41: 用户可以设置模拟托管的初始资金金额
- FR42: 系统可以基于行情数据持续运行模拟策略
- FR43: 用户可以查看模拟机器人的运行状态
- FR44: 用户可以查看模拟持仓详情
- FR45: 用户可以查看模拟收益曲线和买卖信号记录
- FR46: 系统可以在用户首次进入模拟托管时展示免责提示（一次性确认）
- FR47: 用户可以停止或删除模拟托管机器人
- FR48: 系统可以限制用户的模拟托管槽位数量（按套餐等级）

#### 平台管理与安全（FR49-FR65）
- FR49: 管理员可以查看和审核待发布的策略
- FR50: 管理员可以通过或拒绝策略发布申请
- FR51: 管理员可以处理用户举报（下架违规策略并通知作者）
- FR52: 管理员可以查看回测任务队列状态（排队数、耗时、失败率）
- FR53: 管理员可以手动干预卡死的回测任务
- FR54: 管理员可以管理用户账户（封禁、查看操作日志）
- FR55: 系统可以在全站各场景展示合规免责声明
- FR56: 系统可以监控外部数据源健康状态并在异常时通知管理员
- FR57: 系统可以在回测任务排队时向用户展示预估等待时间
- FR58: 用户可以查看和管理自己的策略库（查看列表、删除策略）
- FR59: 系统可以向用户发送站内通知（策略审核结果、额度提醒等）
- FR60: 系统可以通过邮件向用户发送重要通知
- FR61: 用户可以按关键词搜索策略广场中的策略和帖子
- FR62: 用户可以按条件筛选策略（如按标的、收益率范围、最大回撤范围）
- FR63: 系统可以限制策略代码的执行权限（禁止网络访问、文件系统写入、系统命令执行）
- FR64: 系统可以限制单次回测的最大执行时间和内存使用
- FR65: 系统可以在策略发布者注销时处理其已发布策略

---

**来源：prd-qystrategy-improvement.md（QYSP 格式改进，11 条 FR）**

- QYSP-FR1: 定义并文档化 event_v1 策略接口规范（含类型注解，提供 ≥3 个示例策略，支持 Python 3.11+）
- QYSP-FR2: 实现参数注入机制，让 strategy.json 中定义的参数自动注入到 StrategyContext，支持类型转换和默认值
- QYSP-FR3: 增强策略元数据（添加 ui 和 backtest 字段），完全向后兼容现有 .qys 文件
- QYSP-FR4: 提供 Python SDK（核心类 StrategyContext/BarData/Order/Position/Account + 技术指标函数，单元测试覆盖率 ≥80%）
- QYSP-FR5: 提供 qys CLI 工具（init/validate/build/backtest/import/migrate 6 个子命令，支持 Windows/Linux/macOS）
- QYSP-FR6: 提供常用策略模板库（trend-following/mean-reversion/momentum/multi-indicator，每个均可直接运行）
- QYSP-FR7: Web UI 策略导入页面（拖拽上传 .qys、自动解析元数据、SHA256 完整性验证、导入成功跳转配置页）
- QYSP-FR8: 参数配置器（根据 parameters 定义动态生成表单，支持 slider/dropdown，实时验证，可保存预设）
- QYSP-FR9: 策略浏览器（卡片式列表，按标签/分类筛选，支持搜索，分页加载，显示性能摘要）
- QYSP-FR10: 重写 GoldStepByStep 示例策略使用 event_v1 接口、ctx.parameters 参数读取和 SDK 数据类
- QYSP-FR11: 创建完整文档站（快速开始/策略格式规范/SDK API 参考/CLI 文档/常见问题 FAQ）

---

### NonFunctional Requirements

**来源：prd.md（29 条 NFR）**

#### 性能
- NFR1: 回测任务提交后，系统应在 5 秒内开始执行或进入排队状态并返回确认
- NFR2: 简单策略（单标的、1 年数据、日线）回测应在 30 秒内完成；已缓存时应在 10 秒内完成
- NFR3: 复杂策略（多标的、5 年数据、分钟线）回测应在 5 分钟内完成
- NFR4: 策略广场页面首屏加载时间应 ≤2 秒（含策略卡片列表）
- NFR5: K 线图表交互（缩放、拖拽、切换周期）响应时间应 ≤200ms

#### 可用性与可靠性
- NFR6: 量化回测服务月度可用性应 ≥99.5%（不含计划维护窗口）
- NFR7: 数据缓存层应支持 JoinQuant API 不可用时仍可使用已缓存的历史数据回测；缓存命中时 ≥90% 回测任务无需调用外部 API；缓存未命中时降级仍可返回已缓存数据并展示明确的数据范围提示
- NFR8: 单个回测任务失败不应影响其他用户的回测任务（容器隔离）
- NFR9: 系统应支持优雅降级：当外部数据源不可用时，应在 ≤3 秒内展示明确错误提示（含数据源状态说明），不出现空白页面或未捕获崩溃

#### 安全性
- NFR10: 用户上传的策略代码必须在隔离的 Docker/Firecracker 容器沙箱中执行，禁止网络访问和文件系统写入
- NFR11: 存储的策略代码必须使用 AES-256-GCM 加密，解密密钥与密文分离存储（生产环境用 KMS）
- NFR12: 用户密码必须使用 bcrypt（cost factor ≥ 12）哈希存储
- NFR13: 所有 API 端点必须实施速率限制（免费用户：60 次/分钟，付费用户：120 次/分钟）
- NFR14: 敏感操作（支付、密码修改、绑定券商 API）必须要求二次验证

#### 可扩展性
- NFR15: 系统架构应支持从单机部署平滑迁移到分布式部署（微服务就绪）；各功能模块（回测引擎/策略广场/模拟托管）通过接口边界解耦，每个模块可独立启动并通过接口联通验证
- NFR16: 回测任务队列应支持水平扩展（添加更多 Worker 节点）；系统应能在 15 分钟内完成 Worker 节点扩容至当前数量 2 倍，扩容期间已排队任务不丢失
- NFR17: 模拟托管服务可用性应 ≥99.5%（初期阶段合理目标，随成熟度提升至 99.9%）

#### 用户体验
- NFR18: 新用户从注册到完成首次回测的操作步骤应 ≤5 步
- NFR19: 所有核心功能页面应适配主流桌面浏览器（Chrome、Firefox、Edge 最新两个版本）
- NFR20: 回测结果页面必须包含可交互 Equity Curve 图表（支持缩放、悬停显示数值），不得仅展示数字表格；图表应作为页面首屏默认可见内容
- NFR21: 错误提示应包含具体原因和建议操作，而非通用错误码

#### 合规性
- NFR22: 平台所有页面应在适当位置展示投资风险免责声明
- NFR23: 用户数据存储和处理应符合《个人信息保护法》要求（数据最小化、明确授权、可删除）

#### 小白友好性
- NFR24: 平台提供的预置策略首次回测成功率应 ≥95%（因平台原因导致的失败率 ≤5%）
- NFR25: 所有耗时超过 3 秒的操作必须提供进度反馈（进度条、百分比或阶段提示）

#### UI 设计风格
- NFR26: 全平台采用极简金融仪表盘风格：白色主背景、红色强调色、卡片式布局、扁平化设计；单屏可见数据指标不超过 7 个；任何核心功能到达路径不超过 3 次点击；红色仅用于 CTA 按钮和收益/亏损指示

#### 数据一致性与运行环境
- NFR27: 回测结果可复现性——同一策略、同一时间段、同一参数，多次回测结果必须一致
- NFR28: 回测容器预热池——系统应维持预热容器池，容器冷启动时间 ≤1 秒，确保回测任务可即时分配执行环境

#### 审计与合规追踪
- NFR29: 平台应记录关键操作审计日志，覆盖范围：支付操作、管理员账户操作（用户封禁/策略下架/权限变更）、策略代码访问记录；日志保留期限 ≥90 天，仅管理员角色可访问审计日志，日志数据不可篡改

---

### Additional Requirements

**来自 Architecture（技术架构约束）**

**基础设施与项目结构：**
- ARCH-1: 采用 uv workspace monorepo 结构，packages/qysp 为 SDK+CLI 包，使用 hatchling 构建，Click 8.3.1 作为 CLI 框架
- ARCH-2: 第一个 Epic 第一个 Story（Epic 1 Story 1）需要初始化 uv workspace 和项目骨架结构（`uv init --workspace` + `uv init packages/qysp --lib`）

**沙箱执行：**
- ARCH-3: MVP 阶段使用 E2B Cloud（Firecracker microVM）作为策略代码执行沙箱（80ms 启动，硬件级隔离），通过 packages/qysp/src/qysp/sandbox.py 封装
- ARCH-4: 系统应维持预热容器池，通过 E2B Cloud API 管理，MVP 阶段最多 10 个任务并发（CELERYD_CONCURRENCY=10，可配置）

**任务队列：**
- ARCH-5: 使用 Celery + Redis 作为回测任务队列；Redis 同时用于 Refresh Token 黑名单（不同 DB 编号）
- ARCH-6: 使用 Celery Beat 处理定时任务：每交易日 16:00（北京时间）触发模拟机器人执行；每月 1 日 00:00（北京时间）重置用户回测额度

**认证：**
- ARCH-7: JWT + Refresh Token 双令牌：Access Token 有效期 15 分钟存内存（防 XSS），Refresh Token 有效期 30 天存 HttpOnly Cookie
- ARCH-8: 手机号验证码登录，验证码存 Redis TTL 5 分钟，60 秒内同号不可重发

**加密：**
- ARCH-9: 策略代码使用 AES-256-GCM 加密存 PostgreSQL，密钥存环境变量，生产环境用阿里云 KMS
- ARCH-10: .qys 原始包存对象存储（MinIO/阿里云 OSS），路径 UUID 混淆；Equity Curve 时序数据存对象存储

**搜索：**
- ARCH-11: 使用 PostgreSQL tsvector + zhparser 扩展实现中文全文搜索（MVP 数据量 < 1000 策略，无需 Elasticsearch）

**实时推送：**
- ARCH-12: 模拟托管实时推送使用 Server-Sent Events (SSE)（端点：GET /api/v1/simulation/:bot_id/stream），非 WebSocket，零新依赖
- ARCH-13: 站内通知使用 30 秒轮询（GET /api/v1/notifications/unread-count），非长连接

**支付：**
- ARCH-14: 集成微信支付官方 SDK（wechatpayv3）和支付宝官方 SDK（alipay-sdk-python），Webhook 回调更新订阅状态

**邮件：**
- ARCH-15: 使用 Flask-Mail + SMTP 异步发送邮件（Celery 任务），触发场景：策略审核结果、重要系统通知

**时区：**
- ARCH-16: 所有时间统一规范——数据库存 UTC（TIMESTAMP WITH TIME ZONE），Flask 内部全程 UTC，API 响应输出 ISO 8601 带 +08:00 偏移，禁止使用 datetime.now()（无时区），必须使用 qysp/utils/time.py 和 backend/app/utils/time.py 中的工具函数

**API 组织：**
- ARCH-17: Flask 蓝图组织，所有路由前缀 /api/v1/，10 个蓝图模块：auth/strategies/backtest/presets/marketplace/community/simulation/payments/admin/notifications

**数据库：**
- ARCH-18: 共 17 张核心表：users/refresh_tokens/strategies/strategy_parameter_presets/backtest_jobs/user_quota/market_data_cache/posts/post_interactions/comments/simulation_bots/simulation_positions/simulation_records/subscriptions/payment_orders/audit_logs/notifications

**速率限制：**
- ARCH-19: API 速率限制（NFR13）：免费用户 60 次/分钟，付费用户 120 次/分钟，在 Flask 入口层统一实施

---

**来自 UX Design Specification（用户体验约束）**

- UX-1: Web 优先 SPA，MVP 不做原生移动端 App，响应式设计支持桌面和移动端浏览器
- UX-2: 浏览器兼容性：Chrome、Edge、Firefox、Safari 最新两个版本
- UX-3: 新手引导采用渐进式信息披露（3 步互动卡片），不一次性暴露所有功能
- UX-4: Equity Curve 作为回测报告首屏可见的核心决策界面（NFR20 强制要求）
- UX-5: 极简金融仪表盘风格：白色主背景、红色强调色（仅 CTA + 收益/亏损）、卡片式布局
- UX-6: 单屏可见数据指标不超过 7 个，核心功能到达路径不超过 3 次点击（NFR26 UX 化）
- UX-7: 所有耗时 ≥3 秒操作必须显示进度反馈（进度条/百分比/阶段提示）
- UX-8: 错误提示包含具体原因和可操作建议（如智能回测错误提示含示例代码链接）
- UX-9: 模拟托管首次进入显示免责提示弹窗（一次性确认，记录 sim_disclaimer_accepted）
- UX-10: 全站多场景免责声明分层展示（注册时/回测结果页底部/策略详情 tooltip/模拟托管弹窗）

---

### FR Coverage Map

| FR | Epic | 简述 |
|----|------|------|
| QYSP-FR1 | Epic 1 | event_v1 接口规范定义 |
| QYSP-FR2 | Epic 1 | 参数注入机制 |
| QYSP-FR3 | Epic 1 | 策略元数据增强 |
| QYSP-FR4 | Epic 1 | Python SDK |
| QYSP-FR5 | Epic 1 | qys CLI 工具 |
| QYSP-FR6 | Epic 1 | 策略模板库 |
| QYSP-FR7 | Epic 3 | Web 策略导入页面 |
| QYSP-FR8 | Epic 3 | 参数配置器 |
| QYSP-FR9 | Epic 5 | 策略浏览器 |
| QYSP-FR10 | Epic 1 | 示例策略重写 |
| QYSP-FR11 | Epic 1 | 完整文档站 |
| FR1 | Epic 2 | 手机号注册/登录 |
| FR2 | Epic 2 | 个人主页信息管理 |
| FR3 | Epic 8 | 查看套餐等级和额度 |
| FR4 | Epic 8 | 升级/降级套餐 |
| FR5 | Epic 8 | 微信支付/支付宝付费 |
| FR6 | Epic 2 | 注销账号并删除数据 |
| FR7 | Epic 4 | 新手引导 3 步卡片 |
| FR8 | Epic 4 | 引导完成首次回测 |
| FR9 | Epic 4 | 帮助文档/FAQ |
| FR10 | Epic 3 | 上传 Python 策略代码 |
| FR11 | Epic 3 | 从策略库选择策略 |
| FR12 | Epic 3 | 设定回测参数 |
| FR13 | Epic 3 | 多标的组合回测 |
| FR14 | Epic 3 | 沙箱安全执行策略代码 |
| FR15 | Epic 3 | 对接外部数据源 |
| FR16 | Epic 3 | 历史数据缓存 |
| FR17 | Epic 3 | 核心三指标展示 |
| FR18 | Epic 3 | 11 项指标折叠展示 |
| FR19 | Epic 3 | Equity Curve 图表 |
| FR20 | Epic 3 | 买卖点标注 |
| FR21 | Epic 3 | 智能错误提示 |
| FR22 | Epic 3 | 回测额度统计与扣减 |
| FR23 | Epic 3 | 剩余额度和计费规则展示 |
| FR24 | Epic 3 | 支持的依赖库清单 |
| FR25 | Epic 5 | 策略广场列表浏览 |
| FR26 | Epic 5 | 策略详情页 |
| FR27 | Epic 5 | 平台验证徽章 |
| FR28 | Epic 5 | 精选策略推荐位 |
| FR29 | Epic 5 | 一键导入策略库 |
| FR30 | Epic 5 | 一键发起回测试用 |
| FR31 | Epic 5 | 发布策略到广场 |
| FR32 | Epic 5 | 设置策略展示指标 |
| FR33 | Epic 5 | 代码保护说明和知识产权协议 |
| FR34 | Epic 5 | 策略代码不可见/不可下载 |
| FR35 | Epic 6 | 发布帖子 |
| FR36 | Epic 6 | 点赞帖子 |
| FR37 | Epic 6 | 评论帖子 |
| FR38 | Epic 6 | 收藏帖子 |
| FR39 | Epic 6 | 查看用户主页 |
| FR40 | Epic 7 | 创建模拟托管机器人 |
| FR41 | Epic 7 | 设置模拟初始资金 |
| FR42 | Epic 7 | 持续运行模拟策略 |
| FR43 | Epic 7 | 查看机器人运行状态 |
| FR44 | Epic 7 | 查看模拟持仓 |
| FR45 | Epic 7 | 查看模拟收益曲线和买卖信号 |
| FR46 | Epic 7 | 首次进入模拟托管免责提示 |
| FR47 | Epic 7 | 停止或删除机器人 |
| FR48 | Epic 7 | 限制槽位数（按套餐） |
| FR49 | Epic 10 | 管理员审核策略 |
| FR50 | Epic 10 | 通过/拒绝策略发布 |
| FR51 | Epic 10 | 处理用户举报 |
| FR52 | Epic 10 | 查看回测任务队列状态 |
| FR53 | Epic 10 | 手动干预卡死任务 |
| FR54 | Epic 10 | 管理用户账户（封禁/日志） |
| FR55 | Epic 4 | 全站合规免责声明 |
| FR56 | Epic 10 | 数据源健康监控与告警 |
| FR57 | Epic 3 | 排队时展示预估等待时间 |
| FR58 | Epic 3 | 策略库管理（列表/删除） |
| FR59 | Epic 9 | 站内通知 |
| FR60 | Epic 9 | 邮件通知 |
| FR61 | Epic 5 | 关键词搜索策略和帖子 |
| FR62 | Epic 5 | 按条件筛选策略 |
| FR63 | Epic 3 | 限制策略执行权限（沙箱约束） |
| FR64 | Epic 3 | 限制最大执行时间和内存 |
| FR65 | Epic 10 | 注销用户的已发布策略处理 |

---

## Epic List

### Epic 1: 平台基础 & QYSP 策略格式
策略开发者可以使用标准 QYSP 格式开发、验证、打包策略，通过 SDK 和 CLI 工具高效工作；同时完成 uv workspace 项目骨架和 E2B 沙箱基础接入。
**FRs covered:** QYSP-FR1, QYSP-FR2, QYSP-FR3, QYSP-FR4, QYSP-FR5, QYSP-FR6, QYSP-FR10, QYSP-FR11

### Epic 2: 用户注册、登录与账户管理
用户可通过手机号安全注册/登录，管理个人主页（头像、昵称、简介），随时注销并删除所有个人数据。
**FRs covered:** FR1, FR2, FR6

### Epic 3: 量化回测引擎（平台核心）
用户可上传策略或从策略库选择，设定回测参数（标的/时间区间，支持多标的），在沙箱中安全执行，查看含 Equity Curve + 11 项指标的完整报告，并通过智能错误提示排查代码问题。
**FRs covered:** FR10, FR11, FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR19, FR20, FR21, FR22, FR23, FR24, FR57, FR58, FR63, FR64, QYSP-FR7, QYSP-FR8

### Epic 4: 新手引导与首次体验
新用户（尤其零代码小白）通过 3 步互动引导，在 ≤5 步内完成首次回测；全站展示分层合规免责声明；提供帮助文档/FAQ 随时查阅。
**FRs covered:** FR7, FR8, FR9, FR55

### Epic 5: 策略广场与发现
用户可浏览、搜索（中文关键词）、按条件筛选策略广场；识别平台验证徽章；一键导入并回测试用；策略开发者可安全发布策略（代码加密保护，展示 IP 协议）。
**FRs covered:** FR25, FR26, FR27, FR28, FR29, FR30, FR31, FR32, FR33, FR34, FR61, FR62, QYSP-FR9

### Epic 6: 社区互动
用户可在策略广场发布帖子、点赞、评论、收藏，查看其他用户的个人主页，形成活跃社区生态。
**FRs covered:** FR35, FR36, FR37, FR38, FR39

### Epic 7: 模拟托管
用户可创建模拟机器人，设置模拟资金，系统每交易日自动运行策略；用户可实时查看模拟持仓、收益曲线和买卖信号；首次进入时展示免责提示。
**FRs covered:** FR40, FR41, FR42, FR43, FR44, FR45, FR46, FR47, FR48

### Epic 8: 订阅套餐与支付
用户可查看当前套餐等级和剩余回测额度，升级/降级套餐，通过微信支付或支付宝完成付费，解锁更多回测次数和模拟托管槽位。
**FRs covered:** FR3, FR4, FR5

### Epic 9: 通知与消息
用户可在平台内实时收到站内通知（策略审核结果、额度提醒等），并通过邮件接收重要系统通知（审核结果、账户变更）。
**FRs covered:** FR59, FR60

### Epic 10: 平台管理与合规运营
运营管理员可审核策略发布申请、处理用户举报、管理用户账户（封禁/查看操作日志）、监控回测任务队列（含手动干预）、监控数据源健康状态，维护不可篡改的审计日志（≥90 天）。
**FRs covered:** FR49, FR50, FR51, FR52, FR53, FR54, FR56, FR65

---

## Epic 1: 平台基础 & QYSP 策略格式

策略开发者可以使用标准 QYSP 格式开发、验证、打包策略，通过 SDK 和 CLI 工具高效工作；同时完成 uv workspace 项目骨架和 E2B 沙箱基础接入。

### Story 1.1: uv Workspace 项目骨架初始化

作为开发者，
我希望项目拥有 uv workspace 结构并完成 packages/qysp 初始化，
以便 monorepo 拥有统一的依赖管理，SDK 和 CLI 包具备正确的构建结构。

**验收标准：**

**Given** QYQuant 仓库根目录
**When** 执行 `uv init --workspace` 和 `uv init packages/qysp --lib`
**Then** 根目录 pyproject.toml 声明 workspace members: `["packages/qysp", "backend"]`
**And** packages/qysp/pyproject.toml 使用 hatchling 构建后端，Click 8.3.1 作为依赖
**And** `uv sync` 生成统一的 uv.lock 文件
**And** packages/qysp/src/qysp/\_\_init\_\_.py 导出 `__version__` 版本字符串
**And** packages/qysp/src/qysp/utils/time.py 包含 `BEIJING_TZ`、`to_beijing()`、`now_beijing()` 工具函数
**And** backend/pyproject.toml 将 packages/qysp 列为可编辑 workspace 依赖

---

### Story 1.2: event_v1 接口规范与 StrategyContext 核心类

作为策略开发者，
我希望拥有完整的 SDK 类（StrategyContext、BarData、Order、Position、Account）和文档化的 event_v1 接口，
以便我能写出类型安全、结构正确的 on_bar 函数。

**验收标准：**

**Given** qysp SDK 已安装至 workspace
**When** 编写策略文件
**Then** `from qysp import StrategyContext, BarData, Order, Position, Account` 可成功导入
**And** 所有类均有完整 Python 3.11+ 类型注解
**And** `on_bar(ctx: StrategyContext, data: BarData) -> list[Order]` 为文档化的标准入口函数
**And** `ctx.account` 返回包含 cash、total_value、positions 属性的 Account 对象
**And** packages/qysp/tests/test_context.py 单元测试分支覆盖率 ≥80%

---

### Story 1.3: 参数注入机制（ParameterProvider）

作为策略开发者，
我希望 strategy.json 中定义的参数在运行时自动注入到 ctx.parameters，
以便策略代码无需硬编码即可读取可配置的参数值。

**验收标准：**

**Given** strategy.json 中包含 `parameters: [{name: "lookback", type: "int", default: 20}]`
**When** 运行时加载该策略
**Then** `ctx.parameters.get("lookback", 20)` 返回正确的整数值
**And** 类型转换支持 int/float/bool/str（从 JSON 字符串转换）
**And** 必填参数缺失时抛出 `ValidationError`，错误信息明确指出缺失的参数名称
**And** 不含 parameters 字段的旧 .qys 文件仍可正常加载（向后兼容）

---

### Story 1.4: 技术指标函数库

作为策略开发者，
我希望直接使用预置的技术指标函数（SMA、EMA、ATR、金叉/死叉检测），
以便专注于策略逻辑而无需重复实现常用计算。

**验收标准：**

**Given** pandas Series 格式的 OHLCV 数据
**When** 调用 `sma(series, period=20)`
**Then** 返回等长的 pandas Series，数值正确（与 pandas.rolling.mean 一致）
**And** `ema(series, period=20)` 返回指数移动平均 Series
**And** `atr(high, low, close, period=14)` 返回平均真实波幅 Series
**And** `cross_over(s1, s2)` 返回布尔 Series（在 s1 上穿 s2 的 K 线处为 True）
**And** `cross_under(s1, s2)` 返回布尔 Series（在 s1 下穿 s2 的 K 线处为 True）
**And** tests/test_indicators.py 单元测试分支覆盖率 ≥80%

---

### Story 1.5: QYSP 元数据增强与 JSON Schema 验证

作为策略开发者，
我希望 strategy.json 支持可选的 ui 和 backtest 元数据字段，并且验证器能检查 .qys 包完整性，
以便策略携带展示元数据，且发布前可被校验。

**验收标准：**

**Given** 包含新增可选字段 `ui`（icon、category、difficulty）和 `backtest`（defaultPeriod、initialCapital）的 strategy.json
**When** 加载该策略
**Then** 新字段正确解析，旧版不含这些字段的 strategy.json 仍可正常加载（完全向后兼容）
**Given** 一个 .qys 包文件
**When** 调用 `qysp.validator.validate(path)`
**Then** SHA256 校验和与 manifest 一致时验证通过（返回成功）
**And** 校验和不匹配时抛出包含 "checksum mismatch" 的 `ValidationError`
**And** strategy.json 不符合 schema 时错误信息指明具体的无效字段名
**And** tests/test_validator.py 单元测试分支覆盖率 ≥80%

---

### Story 1.6: qys CLI 命令行工具（6 个子命令）

作为策略开发者，
我希望使用 qys CLI 工具的 init、validate、build、backtest、import、migrate 子命令，
以便从终端管理策略开发的完整生命周期。

**验收标准：**

**Given** qys 已通过 `uv tool install packages/qysp` 安装
**When** 运行 `qys --help`
**Then** 6 个子命令全部列出，每个附有一行说明
**When** 运行 `qys init my-strategy --template trend-following`
**Then** 创建包含 strategy.json、src/strategy.py、README.md 的目录
**When** 运行 `qys validate my-strategy.qys`
**Then** 有效包返回退出码 0；无效包返回非零退出码并输出具体字段级错误信息
**When** 运行 `qys build my-strategy/`
**Then** 生成 my-strategy.qys 压缩包，manifest 中包含正确的 SHA256
**When** 运行 `qys migrate my-strategy.qys`
**Then** 包升级至最新 schema 版本（或输出"已是最新版本"）
**And** 所有命令在 Windows 10+、macOS 12+、Ubuntu 20.04+ 上正常工作
**注：** `qys backtest` 和 `qys import` 在本 Epic 中为桩实现，打印说明信息，将在 Epic 3/Epic 5 中完整集成

---

### Story 1.7: 策略模板库（4 种模板）

作为策略开发者，
我希望通过 `qys init --template` 从 4 种内置模板快速创建新策略，
以便从一个可运行、有注释的示例开始，无需从零编写框架代码。

**验收标准：**

**Given** 4 种模板：trend-following、mean-reversion、momentum、multi-indicator
**When** 运行 `qys init my-strat --template mean-reversion`
**Then** 创建的策略直接通过 `qys validate`，无任何报错
**And** 每个模板使用 event_v1 接口（on_bar 带类型注解的 ctx 和 data 参数）和 SDK 数据类
**And** 每个模板通过 `ctx.parameters` 读取至少一个参数，并设有文档化的默认值
**And** 行内注释解释关键逻辑（入场/出场条件、参数作用）

---

### Story 1.8: 示例策略重写与完整文档

作为策略开发者，
我希望 GoldStepByStep 示例策略遵循最佳实践重写，并有完整文档可供参考，
以便在 30 分钟内掌握 QYSP 标准开发模式。

**验收标准：**

**Given** 更新后的 GoldStepByStep 示例
**When** 阅读代码
**Then** 使用 event_v1 接口（on_bar 带类型注解）、通过 ctx.parameters 读取所有参数（零硬编码）、使用 SDK 数据类（BarData、Order）
**And** 行内注释说明每个代码段的作用
**Given** docs/ 文档目录
**When** 阅读 docs/quickstart.md
**Then** 开发者可在 ≤10 分钟内创建并验证第一个策略
**And** docs/api-reference.md 记录所有公共 SDK 类和函数的类型签名
**And** docs/cli-reference.md 列出全部 6 个 qys 子命令及使用示例
**And** docs/strategy-format/ 包含完整的 QYSP 格式规范

---

## Epic 2: 用户注册、登录与账户管理

用户可通过手机号安全注册/登录，管理个人主页（头像、昵称、简介），随时注销并删除所有个人数据。

### Story 2.1: 手机号验证码注册

作为新用户，
我希望通过手机号接收验证码并完成注册，
以便快速开始使用平台而无需记住额外的账号密码。

**验收标准：**

**Given** 项目已完成 DB 初始化
**When** 执行首次 migration
**Then** users 表和 refresh_tokens 表已按架构定义创建（含所有字段和约束）
**Given** 用户填写手机号并点击"获取验证码"
**When** 服务端接收到 `POST /api/v1/auth/send-code` 请求
**Then** 通过短信服务商发送 6 位验证码，验证码存入 Redis，TTL 为 5 分钟
**And** 同一手机号 60 秒内再次请求返回 429 错误，提示"请 X 秒后重试"
**Given** 用户提交手机号 + 验证码 + 昵称
**When** 调用 `POST /api/v1/auth/login`（首次自动注册）
**Then** 验证码匹配后创建 users 表记录（role=user, plan_level=free）
**And** 返回 Access Token（15 分钟有效期），同时在响应中设置 HttpOnly Cookie 存储 Refresh Token（30 天）

---

### Story 2.2: 登录与 Token 刷新

作为已注册用户，
我希望通过手机号验证码登录，Access Token 过期后能无感刷新，
以便在安全的前提下保持登录状态不中断。

**验收标准：**

**Given** 已注册用户提交手机号 + 验证码
**When** 调用 `POST /api/v1/auth/login`
**Then** 验证码匹配后返回新 Access Token，并刷新 HttpOnly Cookie 中的 Refresh Token
**Given** Access Token 已过期但 Refresh Token 有效
**When** 前端调用 `POST /api/v1/auth/refresh`
**Then** 服务端验证 Cookie 中的 Refresh Token（未在 Redis 黑名单中），返回新 Access Token
**Given** 用户点击登出
**When** 调用 `POST /api/v1/auth/logout`
**Then** 服务端将当前 Refresh Token 写入 Redis 黑名单，清除 Cookie
**And** 此后用该 Token 调用 /refresh 返回 401

---

### Story 2.3: 个人主页信息管理

作为已登录用户，
我希望设置和修改我的头像、昵称和个人简介，
以便在策略广场和社区中展示我的个人身份。

**验收标准：**

**Given** 已登录用户访问个人设置页
**When** 提交 `PATCH /api/v1/users/me`（昵称、简介、头像 URL）
**Then** users 表更新成功，API 返回最新用户信息（含 updated_at 北京时间 ISO 8601+08:00）
**And** 昵称长度限制 2–30 字符，超出返回 422 并说明限制
**And** 简介长度限制 ≤200 字符
**Given** 其他用户访问该用户主页
**When** 调用 `GET /api/v1/users/:id`
**Then** 返回公开信息（昵称、头像、简介、注册时间），不返回手机号等敏感字段

---

### Story 2.4: 账号注销与数据删除

作为已登录用户，
我希望注销账号并删除所有个人数据，
以便行使《个人信息保护法》赋予的被遗忘权。

**验收标准：**

**Given** 已登录用户在账户设置页点击"注销账号"
**When** 调用 `DELETE /api/v1/users/me`（需二次验证：输入手机验证码确认）
**Then** 验证通过后软删除 users 记录（写入 deleted_at，不物理删除）
**And** 用户昵称替换为"已注销用户"，手机号字段清空
**And** 所有 Refresh Token 立即写入 Redis 黑名单（强制登出所有设备）
**And** 操作写入 audit_logs 表（operator_id、action="user_delete"）
**And** 该用户已发布策略的处理逻辑由 Epic 10 Story 10.x 实现（本 Story 仅标记用户状态）

---

## Epic 3: 量化回测引擎（平台核心）

用户可上传策略或从策略库选择，设定参数（标的/时间区间，支持多标的），在沙箱中安全执行，查看含 Equity Curve + 11 项指标的完整报告，管理策略库，获得智能错误提示。

### Story 3.1: Celery + Redis 任务队列基础设施

作为平台，
我希望搭建 Celery + Redis 任务队列基础设施，
以便回测任务可以异步执行并支持水平扩展。

**验收标准：**

**Given** Redis 实例已运行，Celery Worker 已启动
**When** 提交一个回测任务到队列
**Then** 任务在 5 秒内进入 pending 或 running 状态（NFR1）
**And** 多个 Worker 可同时处理不同任务（最多 10 个并发，`CELERYD_CONCURRENCY=10`）
**And** backtest_jobs 表已创建（id、user_id、strategy_id、status ENUM、params JSONB、result_summary JSONB、result_storage_key、error_message、started_at、completed_at、created_at）
**And** user_quota 表已创建（user_id、plan_level、used_count、reset_at）
**And** 单个任务失败不影响其他任务（NFR8）

---

### Story 3.2: 历史行情数据缓存层

作为平台，
我希望建立 PostgreSQL 时序缓存层，优先从本地缓存获取历史数据，
以便降低外部 API 调用量并在数据源不可用时仍能服务回测。

**验收标准：**

**Given** market_data_cache 表已创建（symbol、trade_date、OHLCV、source、cached_at，PRIMARY KEY (symbol, trade_date)）
**When** 回测任务请求某 symbol 的历史数据
**Then** 优先查询缓存，命中率目标 ≥90%（NFR7）
**And** 缓存未命中时调用聚宽 JQData API，结果写入缓存后返回
**Given** 聚宽 API 不可用
**When** 回测任务请求数据
**Then** ≤3 秒内返回已缓存的数据，并在响应中附加"数据范围提示"（NFR9）
**And** 不出现空白页面或未捕获异常

---

### Story 3.3: E2B 沙箱集成与策略安全执行

作为平台，
我希望通过 E2B Cloud 在 Firecracker microVM 沙箱中执行策略代码，
以便策略代码在完全隔离的环境中运行，禁止网络访问和文件系统写入。

**验收标准：**

**Given** strategies 表中有 AES-256-GCM 加密存储的策略代码
**When** Worker 执行回测任务
**Then** Flask 解密策略代码 → 传入 E2B 沙箱执行 → 执行完毕后沙箱销毁，明文不落盘
**And** 沙箱内禁止网络访问（NFR10/FR63）
**And** 沙箱内禁止文件系统写入（NFR10/FR63）
**And** 单次回测最大执行时间 5 分钟，超时后任务状态更新为 timeout（FR64）
**And** 简单策略（单标的/1年/日线）在已缓存时 10 秒内完成（NFR2）
**And** 系统维持预热容器池，冷启动时间 ≤1 秒（NFR28）

---

### Story 3.4: 回测任务提交与额度管理

作为已登录用户，
我希望提交回测任务时系统自动校验和扣减额度，并在界面实时看到排队状态，
以便了解何时可以获得结果，以及剩余可用次数。

**验收标准：**

**Given** 用户点击"开始回测"
**When** 调用 `POST /api/v1/backtest/`（含策略 ID、标的列表、时间区间参数）
**Then** 服务端检查 user_quota.used_count < 套餐限额，否则返回 429 并提示"额度已用完，请升级套餐"
**And** 验证通过后创建 backtest_jobs 记录（status=pending），返回 job_id
**And** 任务开始执行时（Worker 侧）扣减 used_count + 1（避免队列积压虚耗）
**Given** 回测任务排队中
**When** 前端轮询 `GET /api/v1/backtest/:job_id`
**Then** 返回 status 和预估等待时间（基于队列长度估算，FR57）
**And** 用户可在回测界面随时查看剩余额度和计费规则说明（FR23）

---

### Story 3.5: 回测报告展示（Equity Curve + 11 项指标）

作为已登录用户，
我希望查看包含 Equity Curve 图表和完整量化指标的回测报告，
以便直观评估策略表现。

**验收标准：**

**Given** 回测任务 status=completed
**When** 用户访问回测报告页
**Then** 页面首屏默认展示可交互 Equity Curve 图表（NFR20），支持缩放和悬停显示数值（响应 ≤200ms，NFR5）
**And** 核心三指标（累计收益率、最大回撤、夏普比率）醒目展示（FR17）
**And** 完整 11 项量化指标以折叠方式展示（FR18），点击展开可见全部
**And** 图表上标注买卖点（FR20）
**And** 报告底部显示合规免责声明（FR55）
**And** 同一策略、同一参数多次回测结果完全一致（NFR27）

---

### Story 3.6: 智能错误提示与依赖库清单

作为已登录用户，
我希望策略代码执行出错时看到智能错误提示，并能查看平台支持的依赖库清单，
以便快速定位问题并修复代码。

**验收标准：**

**Given** 回测任务 status=failed（用户代码错误）
**When** 用户查看失败报告
**Then** 错误提示包含具体行号、错误类型和可读说明（NFR21），不是通用错误码
**And** 对常见错误（缺少参数、未定义变量、类型错误）提供示例代码链接（FR21）
**Given** 用户点击"查看支持的依赖库"
**When** 访问 `GET /api/v1/backtest/supported-packages`
**Then** 返回平台白名单库列表（pandas、numpy、ta-lib 等）及版本号（FR24）

---

### Story 3.7: 策略库管理与 Web 策略导入

作为已登录用户，
我希望管理我的策略库（查看、删除），并能通过拖拽上传 .qys 文件导入策略，
以便有序管理我的所有策略。

**验收标准：**

**Given** 用户访问"我的策略库"页
**When** 调用 `GET /api/v1/strategies/`
**Then** 返回当前用户的策略列表（名称、分类、创建时间、来源），支持分页（FR58）
**When** 用户删除某策略
**Then** 调用 `DELETE /api/v1/strategies/:id` 成功，列表刷新
**Given** 用户拖拽 .qys 文件到导入区域（QYSP-FR7）
**When** 文件上传完成
**Then** 后端解析 strategy.json 并展示策略元数据（名称、描述、标签）
**And** SHA256 校验失败时提示"文件完整性校验失败"
**And** 校验通过后策略 AES-256-GCM 加密存储，跳转至参数配置页

---

### Story 3.8: 参数配置器（动态表单与预设保存）

作为已登录用户，
我希望在 Web 上通过动态生成的表单配置策略参数，并保存为预设，
以便无需修改代码即可调整参数进行多次回测。

**验收标准：**

**Given** 策略的 strategy.json 中定义了 parameters 数组
**When** 用户访问策略参数配置页
**Then** 根据参数类型自动渲染控件：slider（含 min/max/step）、dropdown（枚举）、数字输入框（QYSP-FR8）
**And** 参数说明以 tooltip 方式展示
**And** 输入不合法时实时显示错误提示
**When** 用户点击"保存预设"
**Then** 当前参数组合存入 strategy_parameter_presets 表，可供下次回测复用

---

## Epic 4: 新手引导与首次体验

新用户（尤其零代码小白）通过 3 步互动引导，在 ≤5 步内完成首次回测；全站展示分层合规免责声明；提供帮助文档/FAQ 随时查阅。

### Story 4.1: 新手引导 3 步互动卡片

作为新注册用户，
我希望首次进入平台时体验 3 步互动引导卡片，
以便快速了解 QYQuant 的核心功能，不被复杂界面劝退。

**验收标准：**

**Given** 用户首次登录（users.onboarding_completed = false）
**When** 进入平台首页
**Then** 自动展示 3 步引导卡片：第 1 步"认识策略广场"、第 2 步"一键回测策略"、第 3 步"查看回测报告"
**And** 每步卡片有一个主操作按钮，点击后高亮对应界面区域
**And** 用户可随时点击"跳过引导"关闭，并写入 users.onboarding_completed = true
**And** 引导完成后不再重复展示（FR7）

---

### Story 4.2: 首次回测全流程引导（≤5 步）

作为新注册用户，
我希望引导流程直接带我完成第一次回测，
以便在 5 步以内体验到 QYQuant 的核心价值。

**验收标准：**

**Given** 新手引导第 2 步"一键回测策略"被触发
**When** 用户按引导步骤操作
**Then** 操作路径为：进入策略广场选择精选策略（1步）→ 确认回测参数（1步）→ 点击运行（1步）→ 查看报告（1步），总计 ≤4 步（NFR18，≤5 步）（FR8）
**And** 每步有明确视觉引导（高亮或箭头），告知用户下一步做什么
**And** 引导使用的预置策略回测成功率 ≥95%（NFR24）
**And** 回测执行时显示进度动画并提示预计等待时间（NFR25）

---

### Story 4.3: 帮助文档与 FAQ 随时访问

作为用户，
我希望随时访问帮助文档和 FAQ，了解基础量化概念，
以便看不懂回测指标时能自助找到解释。

**验收标准：**

**Given** 用户点击页面帮助入口或指标旁的 ❓ 图标
**When** 帮助面板展开
**Then** 显示常见问题分类：什么是回测、什么是夏普比率、什么是最大回撤等（FR9）
**And** 每个核心指标名称旁有 ❓ 图标，点击弹出该指标的简单中文解释
**And** 帮助内容为静态 Markdown 渲染，无需外部服务

---

### Story 4.4: 全站分层合规免责声明

作为平台，
我希望在全站各关键场景展示分层的合规免责声明，
以便满足监管要求并管理用户预期。

**验收标准：**

**Given** 新用户注册时
**When** 提交注册表单
**Then** 必须勾选服务协议（含免责条款）才能提交，否则提交按钮置灰（NFR22，FR55）
**Given** 用户查看回测结果页
**When** 页面加载完成
**Then** 底部显示灰色小字"基于历史数据，不构成投资建议"
**Given** 用户查看策略详情页的收益数据
**When** 悬停在收益数字上
**Then** tooltip 显示"仅供参考，历史表现不代表未来收益"
**And** 上述免责文本在页面 DOM 中始终存在，不因任何用户操作消失

---

## Epic 5: 策略广场与发现

用户可浏览、搜索（中文关键词）、按条件筛选策略广场；识别平台验证徽章；一键导入并回测试用；策略开发者可安全发布策略（代码加密保护，展示 IP 协议）。

### Story 5.1: 策略广场列表与精选推荐位

作为用户，
我希望浏览策略广场中的策略列表，并看到人工运营的精选推荐位，
以便快速发现值得试用的优质策略。

**验收标准：**

**Given** 用户进入策略广场页面
**When** 访问 `GET /api/v1/marketplace/strategies`
**Then** 页面首屏 ≤2 秒加载（NFR4），展示卡片式策略列表（FR25）
**And** 页面顶部有精选推荐位（最多 6 个），展示运营标记为 is_featured=true 的策略（FR28）
**And** 策略卡片展示：名称、分类标签、核心指标摘要、平台验证徽章（is_verified=true 时，FR27）
**And** 支持分页加载，每页 20 条

---

### Story 5.2: 策略详情页

作为用户，
我希望查看策略详情页，包含完整描述、展示指标和 Equity Curve，
以便在不看代码的前提下判断策略是否值得试用。

**验收标准：**

**Given** 用户点击任意策略卡片
**When** 访问 `GET /api/v1/marketplace/strategies/:id`
**Then** 详情页展示：名称、作者昵称/头像、分类、描述、标签、发布时间（北京时间 ISO 8601+08:00）（FR26）
**And** 展示发布者设置的展示指标（display_metrics JSONB，FR32）
**And** 展示策略 Equity Curve 图（来自 result_storage_key）
**And** 若 is_verified=true 显示蓝色"平台验证回测"标识（FR27）
**And** 策略代码对访问者完全不可见，无任何下载入口（FR34）

---

### Story 5.3: 一键导入策略库并发起回测试用

作为用户，
我希望将策略广场中的策略一键导入我的策略库，并立即发起回测试用，
以便在 2 步内体验"策略即服务"的核心流程。

**验收标准：**

**Given** 用户在策略详情页点击"免费回测试用"
**When** 调用 `POST /api/v1/marketplace/strategies/:id/import`
**Then** 在用户的 strategies 中创建关联记录（source='marketplace'，FR29）
**And** 自动跳转至回测参数配置页（复用 Epic 3 参数配置器，FR30）
**And** 操作总步骤 ≤2 步（点击导入 → 确认参数）
**And** 已导入过的策略显示"已在策略库中"，不重复创建记录

---

### Story 5.4: 策略发布（免费分享模式）

作为已登录用户，
我希望将我的策略发布到策略广场并设置展示指标，发布前了解代码保护机制，
以便与社区分享策略而无需担心代码泄露。

**验收标准：**

**Given** 用户选择策略库中的策略并点击"发布到策略广场"
**When** 填写名称、描述、标签、分类，设置 display_metrics
**Then** 发布前弹出代码保护说明和知识产权协议（FR33）
**And** 用户确认后 strategies.review_status 设为 pending，调用 `POST /api/v1/marketplace/strategies`
**And** 系统发送站内通知"策略已提交审核"（FR59）
**And** review_status=approved 后 is_public=true，策略在广场可见（FR31）

---

### Story 5.5: 策略搜索与条件筛选

作为用户，
我希望通过关键词搜索或按条件筛选策略广场中的策略，
以便在众多策略中快速找到符合我需求的策略。

**验收标准：**

**Given** 用户在搜索框输入中文关键词（如"均线"）
**When** 调用 `GET /api/v1/marketplace/strategies?q=均线`
**Then** 使用 PostgreSQL tsvector + zhparser 全文搜索，返回名称/描述匹配的策略（FR61）
**Given** 用户展开筛选面板并选择条件（分类=趋势跟踪、最大回撤 ≤20%）
**When** 提交筛选请求
**Then** 返回满足所有条件的策略列表（FR62），支持与关键词搜索组合
**And** 搜索和筛选结果均支持分页

---

## Epic 6: 社区互动

用户可在策略广场发布帖子、点赞、评论、收藏，查看其他用户的个人主页，形成活跃社区生态。

### Story 6.1: 发布帖子

作为已登录用户，
我希望在策略广场发布帖子（可关联策略），
以便分享我的策略心得和回测经验。

**验收标准：**

**Given** 用户点击"发布帖子"
**When** 提交 `POST /api/v1/posts`（content、可选 strategy_id）
**Then** posts 表创建新记录，返回帖子数据（含 created_at 北京时间，FR35）
**And** 帖子内容长度限制 ≤2000 字符，超出返回 422 并说明限制
**And** 若关联了 strategy_id，帖子详情页展示该策略的卡片预览
**And** 发布成功后帖子立即出现在策略广场信息流中

---

### Story 6.2: 点赞与收藏帖子

作为已登录用户，
我希望点赞和收藏感兴趣的帖子，
以便表达认可并方便后续回看。

**验收标准：**

**Given** 用户点击帖子的点赞按钮
**When** 调用 `POST /api/v1/posts/:id/like`
**Then** post_interactions 表插入记录（type='like'），posts.likes_count +1（FR36）
**And** 再次点击取消点赞，likes_count -1，对应记录删除
**And** UNIQUE(user_id, post_id, type) 约束保证同一用户不重复点赞
**Given** 用户点击收藏按钮
**When** 调用 `POST /api/v1/posts/:id/collect`
**Then** post_interactions 表插入记录（type='collect'），支持取消收藏（FR38）
**And** 用户可在"我的收藏"列表查看所有收藏的帖子

---

### Story 6.3: 评论帖子

作为已登录用户，
我希望在帖子下方发表评论，
以便与帖子作者和其他用户交流讨论。

**验收标准：**

**Given** 用户在帖子详情页评论框输入内容并提交
**When** 调用 `POST /api/v1/posts/:id/comments`
**Then** comments 表创建新记录，posts.comments_count +1（FR37）
**And** 评论内容长度限制 ≤500 字符
**And** 新评论立即出现在评论列表中
**Given** 访问帖子详情页
**When** 调用 `GET /api/v1/posts/:id/comments`
**Then** 返回评论列表，按 created_at 正序排列，支持分页（每页 20 条）

---

### Story 6.4: 查看用户个人主页

作为用户，
我希望查看其他用户的个人主页，了解其发布的策略和帖子，
以便发现优秀的策略开发者。

**验收标准：**

**Given** 用户点击帖子或策略卡片上的作者头像/昵称
**When** 访问 `GET /api/v1/users/:id`
**Then** 展示该用户公开信息：头像、昵称、简介、注册时间（FR39）
**And** 展示该用户在广场的策略列表（is_public=true）
**And** 展示该用户发布的帖子列表
**And** 不展示手机号等敏感信息

---

## Epic 7: 模拟托管

用户可创建模拟机器人，设置模拟资金，系统每交易日自动运行策略；用户可实时查看模拟持仓、收益曲线和买卖信号；首次进入时展示免责提示。

### Story 7.1: 创建模拟托管机器人与免责提示

作为已登录用户，
我希望从策略库中选择策略创建模拟托管机器人，并在首次进入时看到免责提示，
以便开始模拟交易前了解风险。

**验收标准：**

**Given** 用户首次进入模拟托管页面（users.sim_disclaimer_accepted = false）
**When** 页面加载
**Then** 弹出一次性免责提示弹窗，用户勾选"我已知晓"后关闭，写入 sim_disclaimer_accepted = true（FR46）
**And** 此后进入该页面不再弹出
**Given** 用户点击"创建机器人"并选择策略、输入初始资金
**When** 提交 `POST /api/v1/simulation/bots`
**Then** simulation_bots 表创建记录（status=active，FR40/FR41）
**And** 若当前 active 机器人数已达套餐上限（free=1，lite=2，pro=3，expert=5），返回 403 并提示升级（FR48）

---

### Story 7.2: Celery Beat 定时执行模拟策略

作为平台，
我希望每个交易日收盘后自动运行所有 active 状态的模拟机器人，
以便用户无需手动操作即可持续跟踪策略的模拟表现。

**验收标准：**

**Given** simulation_records 表（bot_id、trade_date、equity、cash、daily_return、created_at）和 simulation_positions 表（bot_id、symbol、quantity、avg_cost、updated_at）已通过 migration 创建
**When** Celery Beat 已配置每个交易日 16:00（北京时间）触发定时任务并执行
**Then** 查询所有 status=active 的 simulation_bots，逐一通过 E2B 沙箱执行策略逻辑（FR42）
**And** 执行结果写入 simulation_records（trade_date、equity、cash、daily_return）
**And** 更新 simulation_positions（symbol、quantity、avg_cost）
**And** 单个机器人执行失败不影响其他机器人继续运行（容错隔离）

---

### Story 7.3: 查看机器人运行状态与持仓

作为已登录用户，
我希望查看模拟机器人的运行状态和当前持仓详情，
以便了解模拟组合的实时持仓情况。

**验收标准：**

**Given** 用户访问模拟托管页面
**When** 调用 `GET /api/v1/simulation/bots`
**Then** 返回当前用户所有机器人列表，含 status、策略名称、初始资金、创建时间（北京时间，FR43）
**Given** 用户点击某个机器人
**When** 调用 `GET /api/v1/simulation/bots/:id/positions`
**Then** 返回当前模拟持仓列表（symbol、持仓数量、平均成本，FR44）

---

### Story 7.4: 查看模拟收益曲线与买卖信号（SSE 实时推送）

作为已登录用户，
我希望查看模拟收益曲线图和买卖信号记录，并在机器人执行后实时收到更新，
以便直观评估策略的模拟表现。

**验收标准：**

**Given** 用户访问机器人详情页
**When** 页面加载
**Then** 展示 simulation_records 数据生成的收益曲线图（FR45）
**And** 展示历史买卖信号记录列表（日期、标的、方向、价格）
**Given** 机器人当日执行完毕
**When** 用户保持详情页打开（SSE 连接：`GET /api/v1/simulation/:bot_id/stream`）
**Then** 服务端通过 SSE 推送最新持仓和收益数据，页面自动刷新图表（ARCH-12）
**And** SSE 连接断开后前端自动重连，无需用户手动刷新

---

### Story 7.5: 停止与删除模拟机器人

作为已登录用户，
我希望能暂停或彻底删除模拟托管机器人，
以便管理我的模拟托管槽位。

**验收标准：**

**Given** 用户点击"暂停机器人"
**When** 调用 `PATCH /api/v1/simulation/bots/:id`（status=paused）
**Then** 机器人状态更新为 paused，Celery Beat 跳过该机器人（FR47）
**And** 用户可重新启动（status=active），恢复定时执行
**Given** 用户点击"删除机器人"
**When** 调用 `DELETE /api/v1/simulation/bots/:id`
**Then** simulation_bots 记录软删除（deleted_at 标记），释放一个槽位
**And** 相关历史记录（simulation_records、simulation_positions）保留不删除

---

## Epic 8: 订阅套餐与支付

用户可查看当前套餐等级和剩余回测额度，升级/降级套餐，通过微信支付或支付宝完成付费，解锁更多回测次数和模拟托管槽位。

### Story 8.1: 查看套餐信息与剩余额度

作为已登录用户，
我希望随时查看我当前的订阅套餐等级和剩余回测额度，
以便合理安排回测计划并决定是否升级。

**验收标准：**

**Given** 用户访问个人账户页或回测界面
**When** 调用 `GET /api/v1/users/me/quota`
**Then** 返回当前套餐等级、本月已用次数、套餐上限、重置时间（北京时间，FR3）
**And** 回测界面顶部始终显示剩余额度和重置日期
**And** 额度用完时回测按钮变为"升级套餐解锁更多次数"引导升级

---

### Story 8.2: 选择套餐并发起支付

作为已登录用户，
我希望选择套餐并通过微信支付或支付宝完成付费，
以便解锁更多回测次数和模拟托管槽位。

**验收标准：**

**Given** 用户访问套餐升级页面
**When** 查看套餐对比表
**Then** 展示 4 级套餐（免费/轻量 200元/进阶 500元/专业 1000元）及对应回测次数和模拟槽位（FR4）
**Given** 用户选择套餐并点击"微信支付"
**When** 调用 `POST /api/v1/payments/orders`（plan_level、provider=wechat）
**Then** 创建 payment_orders 记录（status=pending），返回微信支付二维码或跳转链接（FR5）
**And** 支付宝支付同样支持，返回支付宝收银台链接
**And** 支付页面展示金额、套餐内容和服务条款确认（NFR14）

---

### Story 8.3: 支付回调处理与套餐激活

作为平台，
我希望安全处理微信/支付宝的支付回调并立即激活用户的新套餐，
以便用户付款后无感知地获得升级权益。

**验收标准：**

**Given** 用户完成支付，支付平台向 Webhook 端点发送回调
**When** `POST /api/v1/payments/webhook/wechat`（或 /alipay）收到有效回调
**Then** 验证回调签名，更新 payment_orders.status = paid
**And** 在 subscriptions 表创建或更新记录（plan_level、starts_at、ends_at）
**And** 更新 users.plan_level 和 user_quota 套餐上限
**And** 发送站内通知"套餐升级成功，已解锁 X 次/月回测额度"（FR59）
**And** 重复回调幂等处理，不重复激活套餐
**And** 支付操作写入 audit_logs（NFR29）

---

### Story 8.4: Celery Beat 月度额度重置

作为平台，
我希望每月 1 日自动重置所有用户的回测额度，
以便套餐按月计费的逻辑正确运行。

**验收标准：**

**Given** Celery Beat 已配置每月 1 日 00:00（北京时间）触发重置任务
**When** 定时任务执行
**Then** 将所有 user_quota.used_count 重置为 0，更新 reset_at 为下月 1 日
**And** 已过期订阅的用户降级为 free 套餐上限
**And** 重置操作幂等，重复执行不产生副作用

---

## Epic 9: 通知与消息

用户可在平台内实时收到站内通知（策略审核结果、额度提醒等），并通过邮件接收重要系统通知。

### Story 9.1: 站内通知系统

作为已登录用户，
我希望在平台内收到及时的站内通知，
以便不遗漏任何重要平台消息。

**验收标准：**

**Given** notifications 表（id、user_id、type、title、content、is_read、created_at）已通过 migration 创建
**When** 平台触发通知事件（策略审核通过/拒绝、额度用完提醒等）并写入 notifications 表（is_read=false）
**Then** 用户导航栏的通知图标显示未读数徽标（FR59）
**And** 前端每 30 秒轮询 `GET /api/v1/notifications/unread-count`，自动更新未读数（ARCH-13）
**Given** 用户点击通知图标
**When** 调用 `GET /api/v1/notifications`
**Then** 返回通知列表（按 created_at 倒序，分页每页 20 条），含标题、内容、时间（北京时间）、已读状态
**When** 用户点击某条通知
**Then** 调用 `PATCH /api/v1/notifications/:id/read`，is_read 更新为 true，未读数减 1

---

### Story 9.2: 邮件通知（异步发送）

作为平台，
我希望通过邮件异步发送重要系统通知，
以便用户即使未打开平台也能及时获知关键信息。

**验收标准：**

**Given** 策略审核结果产生（approved 或 rejected）
**When** 管理员操作触发审核完成
**Then** 系统通过 Celery 任务异步调用 Flask-Mail 发送审核结果邮件（FR60）
**And** 邮件主题清晰标注平台名称和通知类型（如"【QYQuant】您的策略审核结果"）
**And** 邮件发送失败时记录错误日志，不影响主请求响应（异步容错）
**And** 同一事件不重复发送邮件（幂等保护）
**Given** 邮件服务（SMTP）不可用
**When** Celery 任务执行邮件发送
**Then** 最多重试 3 次（指数退避），重试耗尽后记录 error 日志

---

## Epic 10: 平台管理与合规运营

运营管理员可审核策略发布申请、处理用户举报、管理用户账户（封禁/查看操作日志）、监控回测任务队列（含手动干预）、监控数据源健康状态，维护不可篡改的审计日志（≥90 天）。

### Story 10.1: 管理后台基础框架（路由守卫 + Admin 蓝图）

作为管理员，
我希望有一个受保护的管理后台入口，只有 admin 角色用户才能访问，
以便安全地执行运营管理操作。

**验收标准：**

**Given** role=admin 用户登录后访问 `/admin/*` 路由
**When** Vue Router beforeEach 守卫执行
**Then** 验证 users.role === 'admin'，非 admin 用户跳转首页并提示"无权限"
**And** 后端所有 `/api/v1/admin/` 端点均有 `@require_admin` Flask 装饰器，非 admin 请求返回 403
**And** admin 蓝图注册至 Flask app factory，audit_logs 表已创建（id、operator_id、action、target_type、target_id、details JSONB、created_at，NFR29）

---

### Story 10.2: 策略审核队列

作为管理员，
我希望查看待审核的策略列表，并可通过或拒绝策略发布申请，
以便管控平台内容质量。

**验收标准：**

**Given** 管理员访问策略审核页面
**When** 调用 `GET /api/v1/admin/strategies?review_status=pending`
**Then** 返回所有待审核策略列表（含策略名称、作者、提交时间、描述，FR49）
**Given** 管理员点击"通过"
**When** 调用 `PATCH /api/v1/admin/strategies/:id/review`（status=approved）
**Then** strategies.review_status=approved，is_public=true（FR50）
**And** 触发站内通知和邮件通知告知作者审核结果（FR59/FR60）
**And** 操作写入 audit_logs（action="strategy_approve"，NFR29）
**Given** 管理员点击"拒绝"并填写原因
**When** 提交审核
**Then** strategies.review_status=rejected，通知作者并附上拒绝原因（FR50）

---

### Story 10.3: 用户举报处理与内容下架

作为管理员，
我希望处理用户举报，可以下架违规策略并通知作者，
以便维护平台内容合规性。

**验收标准：**

**Given** 用户提交举报（`POST /api/v1/marketplace/strategies/:id/report`）
**When** 举报记录写入系统
**Then** 管理员在举报队列（`GET /api/v1/admin/reports`）可见该举报（FR51）
**Given** 管理员审查后决定下架策略
**When** 调用 `PATCH /api/v1/admin/strategies/:id/takedown`
**Then** strategies.is_public=false，发送站内通知给作者说明下架原因（FR51）
**And** 操作写入 audit_logs（action="strategy_takedown"，NFR29）

---

### Story 10.4: 回测任务队列监控与手动干预

作为管理员，
我希望查看回测任务队列状态，并能手动终止卡死的任务，
以便保障回测服务的稳定运行。

**验收标准：**

**Given** 管理员访问任务监控页面
**When** 调用 `GET /api/v1/admin/backtest/queue-stats`
**Then** 返回当前排队数、运行中数、平均耗时、近 1 小时失败率（FR52）
**And** 列出所有 status=running 且超过 10 分钟未完成的任务（疑似卡死）
**Given** 管理员点击"终止任务"
**When** 调用 `DELETE /api/v1/admin/backtest/:job_id`
**Then** Celery 撤销该任务，backtest_jobs.status=failed，error_message="管理员手动终止"（FR53）
**And** 操作写入 audit_logs（action="job_terminate"，NFR29）

---

### Story 10.5: 用户账户管理（封禁与审计日志查看）

作为管理员，
我希望查看用户列表、封禁违规用户，并查看审计日志，
以便处理违规行为并追溯问题。

**验收标准：**

**Given** 管理员访问用户管理页面
**When** 调用 `GET /api/v1/admin/users`（支持按手机号/昵称搜索）
**Then** 返回用户列表（昵称、注册时间、套餐、封禁状态，FR54）
**Given** 管理员点击"封禁用户"
**When** 调用 `PATCH /api/v1/admin/users/:id`（is_banned=true）
**Then** users.is_banned=true，该用户所有 Refresh Token 写入 Redis 黑名单（强制登出）
**And** 被封禁用户登录时返回 403 并提示"账号已被封禁"
**And** 操作写入 audit_logs（action="user_ban"，NFR29）
**Given** 管理员查看审计日志
**When** 调用 `GET /api/v1/admin/audit-logs`（支持按 operator_id/action/target 筛选）
**Then** 返回审计日志列表，覆盖支付操作、管理员操作、策略代码访问记录（NFR29）
**And** 审计日志只读，无任何修改或删除接口（不可篡改，NFR29）
**And** 日志保留期 ≥90 天，超期记录归档而非删除

---

### Story 10.6: 数据源健康监控与异常告警

作为管理员，
我希望平台自动监控聚宽 JQData API 健康状态，异常时立即通知，
以便及时处置数据源故障，减少对回测服务的影响。

**验收标准：**

**Given** Celery Beat 每 5 分钟触发一次数据源健康检查
**When** 检测到聚宽 API 响应超时或返回错误
**Then** 向管理员发送邮件告警"数据源异常：JQData API 不可用"（FR56）
**And** 管理员后台健康看板标记数据源状态为"异常"（红色指示）
**When** API 恢复正常
**Then** 状态自动更新为"正常"，发送恢复通知邮件

---

### Story 10.7: 注销用户的已发布策略处理

作为平台，
我希望当策略发布者注销账号时，正确处理其已发布的策略，
以便保障策略广场内容完整性和其他用户的使用体验。

**验收标准：**

**Given** 用户注销账号（Epic 2 Story 2.4 触发注销流程）
**When** 系统处理注销后置逻辑
**Then** 该用户已在广场公开的策略（is_public=true）保持可见，作者显示为"已注销用户"（FR65）
**And** 该用户私有策略（is_public=false）标记 deleted_at
**And** 其他用户已导入该用户策略的记录保持可用，不因作者注销而失效
**And** 该用户发布的帖子和评论保留，作者昵称显示为"已注销用户"

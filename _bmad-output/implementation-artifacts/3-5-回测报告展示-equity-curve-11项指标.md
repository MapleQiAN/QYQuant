# Story 3.5: 回测报告展示（Equity Curve + 11 项指标）

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

作为已登录用户，
我希望查看包含 Equity Curve 图表和完整量化指标的回测报告，
以便直观评估策略表现。

## 验收标准

1. **Equity Curve 图表展示**
   - Given 回测任务 status=completed
   - When 用户访问回测报告页
   - Then 页面首屏默认展示可交互 Equity Curve 图表（NFR20），支持缩放和悬停显示数值（响应 ≤200ms，NFR5）

2. **核心三指标醒目展示**
   - And 核心三指标（累计收益率、最大回撤、夏普比率）醒目展示（FR17）

3. **完整 11 项指标折叠展示**
   - And 完整 11 项量化指标以折叠方式展示（FR18），点击展开可见全部

4. **买卖点标注**
   - And 图表上标注买卖点（FR20）

5. **合规免责声明**
   - And 报告底部显示合规免责声明（FR55）

6. **结果一致性**
   - And 同一策略、同一参数多次回测结果完全一致（NFR27）

## 任务 / 子任务

- [ ] Task 1: 创建回测报告 API (AC: #1, #2, #3, #6)
  - [ ] 1.1 创建 `GET /api/v1/backtest/:job_id/report` 端点
  - [ ] 1.2 返回 result_summary（11 项摘要指标）从 backtest_jobs.result_summary JSONB
  - [ ] 1.3 返回 equity_curve 时序数据从对象存储（result_storage_key）
  - [ ] 1.4 返回 trades 列表（买卖点数据）
  - [ ] 1.5 权限校验：只能查看自己的报告

- [ ] Task 2: 实现 11 项量化指标计算 (AC: #2, #3, #6)
  - [ ] 2.1 创建 `backend/app/services/metrics.py`，实现指标计算
  - [ ] 2.2 核心三指标：累计收益率、最大回撤、夏普比率
  - [ ] 2.3 完整 11 项：年化收益率、波动率、索提诺比率、卡尔马比率、胜率、盈亏比、最大连续亏损次数、平均持仓天数、总交易次数、Alpha、Beta
  - [ ] 2.4 确保相同输入产生完全相同的输出（确定性计算，NFR27）
  - [ ] 2.5 在沙箱执行结束后由 Worker 计算指标，写入 result_summary

- [ ] Task 3: 实现结果存储（混合方案）(AC: #1)
  - [ ] 3.1 创建 `backend/app/utils/storage.py`，封装对象存储（开发用本地文件系统，生产用 MinIO/OSS）
  - [ ] 3.2 Equity Curve 时序数据存对象存储，路径为 `backtest-results/{job_id}/equity_curve.json`
  - [ ] 3.3 摘要指标（11 项）存 backtest_jobs.result_summary JSONB
  - [ ] 3.4 trades 列表存对象存储 `backtest-results/{job_id}/trades.json`

- [ ] Task 4: 前端回测报告页面 (AC: #1, #2, #3, #4, #5)
  - [ ] 4.1 创建/扩展 `frontend/src/views/BacktestResult.vue`
  - [ ] 4.2 使用 ECharts（或已有图表库）渲染可交互 Equity Curve 图表
  - [ ] 4.3 图表支持缩放（dataZoom）和悬停显示数值（tooltip）
  - [ ] 4.4 核心三指标醒目卡片展示（大字号、颜色区分正负）
  - [ ] 4.5 完整 11 项指标折叠面板（默认收起，点击展开）
  - [ ] 4.6 图表上标注买卖点（使用 markPoint 或 scatter 系列）
  - [ ] 4.7 报告底部固定合规免责声明文本

- [ ] Task 5: 前端状态管理 (AC: #1)
  - [ ] 5.1 创建/扩展 `frontend/src/stores/useBacktestStore.ts`
  - [ ] 5.2 实现报告数据获取和缓存
  - [ ] 5.3 实现任务状态轮询逻辑（配合 Story 3.4）

- [ ] Task 6: 编写测试 (AC: #1-#6)
  - [ ] 6.1 后端：测试报告 API 返回正确数据
  - [ ] 6.2 后端：测试 11 项指标计算正确性（使用已知数据集）
  - [ ] 6.3 后端：测试对象存储读写
  - [ ] 6.4 前端：组件快照测试
  - [ ] 6.5 测试相同参数多次计算结果一致（NFR27）

## Dev Notes

### 架构模式与约束

- **前端框架**：Vue 3 + Pinia + ECharts（或现有图表库）
- **结果存储**：混合方案 — 摘要存 JSONB（< 10KB），Equity Curve 存对象存储（可达数百KB）
- **图表响应**：≤200ms（NFR5），数据量大时考虑降采样
- **免责声明**：FR55 合规要求，报告底部固定展示

### 现有代码分析（关键！）

**⚠️ 前端已有回测相关组件：**

1. **`frontend/src/views/Backtest.vue`** 或类似页面：可能已有回测界面
2. **`frontend/src/components/`** 中可能已有 `BacktestCard.vue` 等组件
   - 架构规范提到"回测结果复用现有 BacktestCard 组件"
3. **Pinia stores**：可能已有 `useBacktestStore.ts`

**后端：**
1. **`backend/app/blueprints/backtests.py`**：已有端点，需扩展报告查询
2. **`backend/app/models.py`** 中 `BacktestJob`：result_summary JSONB 字段存放指标

### 项目结构参考

```
backend/app/
├── services/
│   └── metrics.py          # 新建：11 项量化指标计算
├── utils/
│   └── storage.py          # 新建：对象存储封装
├── blueprints/
│   └── backtests.py        # 扩展：报告查询 API
frontend/src/
├── views/
│   └── BacktestResult.vue  # 新建/扩展：报告展示页
├── stores/
│   └── useBacktestStore.ts # 新建/扩展
└── components/
    └── backtest/
        ├── EquityCurve.vue # 新建：Equity Curve 图表组件
        └── MetricsPanel.vue# 新建：指标面板组件
```

### 测试标准

- 指标计算测试使用已知数据集验证正确性
- 前端组件使用快照测试
- API 测试覆盖正常和异常场景
- 确定性测试：同一输入多次计算结果完全一致

### 关键技术细节

**11 项量化指标：**
1. 累计收益率 (Total Return)
2. 年化收益率 (Annualized Return)
3. 最大回撤 (Max Drawdown)
4. 夏普比率 (Sharpe Ratio)
5. 波动率 (Volatility)
6. 索提诺比率 (Sortino Ratio)
7. 卡尔马比率 (Calmar Ratio)
8. 胜率 (Win Rate)
9. 盈亏比 (Profit/Loss Ratio)
10. 最大连续亏损次数 (Max Consecutive Losses)
11. 总交易次数 (Total Trades)

**结果存储路径：**
```
对象存储/
└── backtest-results/
    └── {job_id}/
        ├── equity_curve.json   # 时序数据
        └── trades.json         # 买卖记录
```

**依赖关系：**
- 依赖 Story 3.1（BacktestJob 模型）
- 依赖 Story 3.3（沙箱执行产出结果）
- 依赖 Story 3.4（任务提交和状态轮询）
- 被 Story 3.6（错误提示）依赖

### Project Structure Notes

- ECharts 是 Vue 生态中最常用的图表库，已有 `vue-echarts` 包装
- 对象存储开发阶段使用本地文件系统（`backend/storage/` 目录），生产切换 MinIO/OSS
- 前端组件按功能分子目录（`backtest/`），与架构规范一致
- 图表数据降采样：如 Equity Curve 超过 2000 点，使用 LTTB 算法降采样

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#领域2：回测引擎架构（FR10-24）] — 结果存储混合方案
- [Source: _bmad-output/planning-artifacts/architecture.md#前端架构] — Vue 组件策略
- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.5] — 用户故事和验收标准
- [Source: backend/app/blueprints/backtests.py] — 现有回测蓝图
- [Source: _bmad-output/implementation-artifacts/3-1-celery-redis任务队列基础设施.md] — BacktestJob 模型定义

## Dev Agent Record

### Agent Model Used

<!-- 由 dev-story 执行时填写 -->

### Debug Log References

### Completion Notes List

### File List

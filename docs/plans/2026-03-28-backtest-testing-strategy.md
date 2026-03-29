# QYQuant 回测测试策略

## 目标

这份文件用于指导 QYQuant 当前回测系统的测试与回归，目标不是证明“回测能跑”，而是验证 3 件事：

1. 回测链路在功能上正确。
2. 回测结果在工程上可重复、可解释、可追溯。
3. 策略在进入更正式研究或上线前，已经被系统性地“打坏”过一次。

当前系统的回测主链路位于以下模块：

- `backend/app/backtest/providers.py`：数据源选择与 K 线获取
- `backend/app/backtest/engine.py`：同步回测入口与基础 summary
- `backend/app/strategy_runtime/loader.py`：策略包加载与清单校验
- `backend/app/strategy_runtime/params.py`：策略参数合并与校验
- `backend/app/strategy_runtime/sandbox.py`：本地沙箱执行与禁用能力检查
- `backend/app/services/sandbox.py`：测试环境本地执行 / 非测试环境远程 E2B 执行
- `backend/app/tasks/backtests.py`：异步任务状态流转、报告生成、结果落盘
- `backend/app/services/metrics.py`：权益曲线与结果指标生成

## 系统边界

本策略覆盖当前仓库已经存在的能力，不假设系统具备尚未实现的高级特性。

已实现边界：

- 支持同步调试接口 `/api/backtests/latest`
- 支持异步任务接口 `/api/backtests/run` 与 `/api/v1/backtest/`
- 支持 `mock`、`binance`、`freegold`、`joinquant`、`auto` 数据源路由
- 支持 `.qys` 策略包加载、参数校验、沙箱执行、报告落盘与结果查询
- 支持配额校验、任务状态机、结构化错误解析

当前限制：

- 没有原生的手续费、滑点、成交拒绝、部分成交建模
- 没有现成的 walk-forward / 参数扫描 / 样本外分析框架
- `JoinQuantBacktestProvider` 仅支持日线
- 测试环境默认走本地子进程沙箱，不覆盖真实 E2B 远端行为
- `qys backtest` CLI 仍是占位能力，正式测试应以 backend API/任务链路为准

这意味着测试必须分成两层：第一层验证“系统是否正确执行”，第二层验证“在当前能力边界下，结果是否足够可信”。两层都通过，回测才有参考价值。

## 测试原则

### 1. 先测正确性，再测收益解释

先回答“系统是否按规则执行”，再回答“这些结果值不值得信”。如果前者都没有锁死，后面的收益、胜率、Sharpe 都没有意义。

### 2. 测所有样本，不测精选样本

不能只用会上涨、会出信号、会盈利的数据做验证。必须覆盖：

- 不出单
- 连续亏损
- 横盘
- 大跳空
- 数据缺口
- 参数非法
- 策略运行超时

### 3. 寻找稳定平台，不寻找最优尖峰

如果策略只在一个极窄参数点工作，这是过拟合信号。测试设计应优先看参数扰动后的稳定区间，而不是单次最优结果。

### 4. 主动加摩擦

虽然系统目前没有内建滑点/手续费模型，但测试策略必须显式保留这部分位置。没有摩擦的回测只能作为“引擎行为验证”，不能作为生产级绩效结论。

### 5. 同步与异步结果必须可对齐

同一组输入在 `/api/backtests/latest` 与异步任务链路里，除了存储和元数据，核心交易结果与指标应保持一致，不能出现两套口径。

## 测试分层

### P0：回测链路正确性

这是发布门槛。P0 不通过，任何回测结果都不应被展示为可信结果。

### 1. 数据提供层

重点验证：

- `auto` 路由是否对黄金符号落到 `freegold`，对其他符号落到 `binance`
- provider alias 是否正确映射到 canonical provider
- `JoinQuantBacktestProvider` 是否拒绝非日线 interval
- `start_time` / `end_time` / `limit` 是否被正确归一化
- `data_range_notice` 是否能够透传到最终回测结果

建议新增：

- `backend/tests/test_backtest_providers.py`

### 2. 策略包与参数预检查

重点验证：

- 缺失策略版本、缺失文件、坏 zip、清单不合法时返回确定错误
- manifest 中的 `id` / `version` 与数据库记录不一致时拒绝运行
- 加密源码与 hash 不一致时拒绝运行
- 参数的 `required`、`type`、`min/max`、`enum`、`unknown` 分支全部覆盖

现有基础覆盖已经在：

- `backend/tests/test_strategy_runtime.py`

建议继续补足：

- manifest mismatch
- `strategy_code_integrity_error`
- `params_not_object`
- `enum` 与 `required` 分支

### 3. 沙箱执行层

重点验证：

- 禁止导入 `os`、`subprocess`、`socket` 等危险模块
- 禁止 `open`、`input`、`exec`、`eval` 等 builtin
- 入口函数不存在、入口不可调用、源码语法错误时返回结构化错误
- 超时任务标记为 `timeout`
- 相同 bars + params + strategy source 的结果是确定性的

建议新增：

- `backend/tests/test_strategy_sandbox.py`

### 4. 任务状态机与权限层

重点验证：

- pending -> running -> completed / failed / timeout 的状态迁移
- 配额在任务启动时扣减，而不是仅在提交时扣减
- 失败任务不会阻塞后续任务
- 非 owner 不能查看报告
- 报告缺失、未完成、失败三种状态响应码正确

现有基础覆盖已经在：

- `backend/tests/test_backtests.py`

### 5. 指标与报告层

重点验证：

- `equity_curve`、`drawdown`、`alpha`、`beta`、`sortinoRatio`、`calmarRatio` 的计算结果可复核
- 没有成交、只有买入未平仓、部分平仓、连续亏损时指标口径稳定
- trade 时间乱序时 `_normalize_trades()` 是否仍生成一致结果
- 零价格、零权益、极短区间时不能产生 `NaN` / `inf`

现有基础覆盖：

- `backend/tests/test_backtest_summary.py`

建议新增：

- `backend/tests/test_backtest_metrics.py`

### P1：回测健壮性

P1 用于证明这个回测系统不只是“能在干净样本上跑通”，而是在常见脏数据与边界输入下依旧可控。

### 1. 数据质量扰动

至少覆盖以下场景：

- bars 缺失某一天/某一分钟
- bars 时间戳乱序
- bars 重复
- bars 出现零成交量
- bars 出现极端跳空
- bars 只有 1 根或 2 根

期望：

- 系统返回稳定错误，或输出可解释结果
- 不出现 silent corruption
- 指标口径不因输入顺序而漂移

### 2. 交易事件扰动

至少覆盖：

- 连续买入未卖出
- 卖出数量大于持仓
- `quantity <= 0`
- 同一根 bar 内多次下单
- trade 缺少 `side` / `timestamp` / `price`

期望：

- 非法 trade 被过滤时行为可预测
- 合法 trade 的 FIFO 配对结果稳定
- `maxConsecutiveLosses`、`avgHoldingDays`、`winRate` 没有隐式偏差

### 3. 存储与恢复

至少覆盖：

- `equity_curve.json` 或 `trades.json` 缺失
- 存储目录存在但内容损坏
- 异步任务完成后报告可重复读取

期望：

- API 返回明确错误码
- 不把坏报告误当成空报告

### P2：回测可信度验证

P2 不是为了证明 API 没 bug，而是为了判断“这个策略是否值得继续研究”。这部分最符合回测工作本身，也最容易被忽略。

### 1. 样本内 / 样本外

建议最少拆成：

- 训练集：用于确定基础参数
- 验证集：用于第一轮样本外检查
- 保留集：只在最终复核时运行一次

通过条件建议：

- 样本外收益方向与样本内一致
- 样本外回撤没有明显失控
- 样本外表现不能跌到样本内的 50% 以下太多，否则要重点怀疑过拟合

### 2. 参数敏感性

对每个关键参数至少测试：

- 基线值的 50%
- 基线值的 75%
- 基线值的 100%
- 基线值的 125%
- 基线值的 150%

观察重点：

- 是否存在宽平台
- 是否只在单点最优
- 交易数是否因为微调参数而急剧塌缩

### 3. 市场状态切片

至少按以下状态分别跑：

- 单边上涨
- 单边下跌
- 震荡
- 高波动
- 低波动

如果同一策略只在单一 regime 有效，应在报告中明确标注“状态依赖”，而不是给出统一结论。

### 4. 摩擦与悲观假设

即使当前系统未原生支持，也建议在测试计划里保留三档摩擦场景：

- 基线：0 手续费 / 0 滑点，仅用于引擎对账
- 保守：加入 1x 预估手续费与滑点
- 悲观：加入 1.5x 到 2x 的手续费与滑点

如果一个策略只在“零摩擦”下盈利，不应进入下一阶段。

## 基准数据与策略夹具

建议在 `backend/tests/fixtures/backtest/` 维护最小可复核夹具。

### 数据夹具

- `bull_trend_1m.json`：持续上涨分钟线，用于验证趋势持仓与 summary
- `range_chop_1m.json`：来回震荡，用于验证频繁交易与假突破
- `gap_down_1d.json`：含跳空缺口，用于验证回撤与权益断层
- `missing_bars_1d.json`：有缺口与乱序数据，用于验证归一化
- `gold_daily_joinquant.json`：黄金日线样本，用于验证 `joinquant/freegold` 路由

### 策略夹具

- `no_trade_strategy.qys`：从不下单，验证空报告
- `single_long_strategy.qys`：单次开平仓，验证最小闭环
- `alternating_strategy.qys`：交替买卖，验证 FIFO 配对
- `bad_import_strategy.qys`：触发沙箱拒绝
- `timeout_strategy.qys`：触发超时
- `invalid_param_strategy.qys`：触发参数校验错误

## 推荐测试文件布局

- `backend/tests/test_backtests.py`
- `backend/tests/test_strategy_runtime.py`
- `backend/tests/test_backtest_summary.py`
- `backend/tests/test_backtest_providers.py`
- `backend/tests/test_backtest_metrics.py`
- `backend/tests/test_strategy_sandbox.py`
- `backend/tests/test_backtest_robustness.py`
- `backend/tests/fixtures/backtest/*.json`

其中：

- `test_backtests.py` 保持接口、任务、权限、报告链路
- `test_strategy_runtime.py` 保持策略包、参数、加载与预检查
- 新增的 `test_backtest_metrics.py` 负责黄金样本的数值对账
- 新增的 `test_backtest_robustness.py` 负责脏数据、异常成交、边界样本

## 执行顺序

### 每次提交必跑

```bash
uv run --project backend pytest backend/tests/test_backtests.py -q
uv run --project backend pytest backend/tests/test_strategy_runtime.py -q
uv run --project backend pytest backend/tests/test_backtest_summary.py -q
```

当前环境注意事项：

- 我在仓库当前状态下执行这组回归时，`test_backtests.py` 中多条 `/api/backtests/run` 用例因 Celery result backend 访问 Redis 时触发 `redis.exceptions.AuthenticationError: Authentication required` 而失败。
- 另有至少两条断言已经与现状不一致：`test_get_backtest_quota_returns_plan_snapshot` 与 `test_missing_strategy_version_returns_400`。
- 因此在把 P0 作为强门禁之前，建议先稳定测试环境：要么为测试环境提供可认证的 Redis/Celery backend，要么在测试中显式 mock/隔离结果后端。

### 回测核心变更必跑

适用于修改以下模块：

- `backend/app/backtest/*`
- `backend/app/strategy_runtime/*`
- `backend/app/tasks/backtests.py`
- `backend/app/services/metrics.py`
- `backend/app/services/sandbox.py`

当前仓库还没有本文建议新增的 `test_backtest_metrics.py` 和 `test_backtest_providers.py`。在这些文件补齐之前，先执行现有核心用例：

```bash
uv run --project backend pytest backend/tests/test_backtests.py backend/tests/test_strategy_runtime.py backend/tests/test_backtest_summary.py -q
```

补齐新增测试文件后，再升级为：

```bash
uv run --project backend pytest backend/tests/test_backtests.py backend/tests/test_strategy_runtime.py backend/tests/test_backtest_summary.py backend/tests/test_backtest_metrics.py backend/tests/test_backtest_providers.py -q
```

### 上线前必跑

上线前除了 P0 / P1 自动化测试，还要至少补 1 轮人工复核：

1. 用固定夹具跑同步接口与异步任务，确认 trade 和 summary 一致。
2. 用失败策略确认结构化错误可读、可定位。
3. 用 owner / non-owner 两个账号确认权限隔离。
4. 用一组真实市场样本做参数扰动，确认不存在极窄最优点。

## 通过标准

满足以下条件，才可以说“回测测试通过”：

- P0 全部通过
- 指标测试没有 `NaN` / `inf` / 时间顺序依赖
- 同步与异步结果对齐
- 报告文件可重复读取
- 至少一组样本外测试通过
- 至少一轮参数敏感性检查完成并确认不是尖峰最优

如果只是 API 通过，但没有做样本外、参数敏感性和摩擦测试，只能说“回测引擎可运行”，不能说“策略已验证”。

## 当前仓库的优先补测项

按收益/风险比排序，建议优先补这 8 项：

1. `providers.py` 的 provider alias、`auto` 路由与 JoinQuant 日线限制。
2. `loader.py` 的 manifest mismatch、源码 hash 不一致、坏归档。
3. `params.py` 的 `required`、`enum`、`unknown`、`params_not_object`。
4. `sandbox.py` 的 forbidden builtin、入口不存在、语法错误、确定性。
5. `metrics.py` 的部分平仓、未平仓、乱序 trade、极短窗口年化收益。
6. `/api/backtests/latest` 与异步任务结果一致性。
7. 报告文件缺失/损坏时的 API 行为。
8. 一组最小样本外 + 参数扰动回归，用于防止“功能没坏但策略验证标准退化”。

## 结论

QYQuant 当前已经具备“策略包 -> 预检查 -> 沙箱执行 -> 异步回测 -> 报告落盘”的完整闭环，因此测试策略不能只停留在接口层。建议把回测测试正式拆成两条线并长期执行：

- 工程线：保证链路正确、状态可控、指标稳定。
- 研究线：保证结果不是样本幻觉、参数尖峰或零摩擦幻觉。

只有两条线同时通过，回测结果才值得继续用于策略筛选与研究决策。

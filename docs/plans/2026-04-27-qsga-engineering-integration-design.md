# QSGA 论文方案工程化接入 QYQuant 设计

资料基线日期：2026-04-27。

本文目标是把 `docs/QSGA论文思路v7Plus_最终稿.md` 中的 QSGA / QYIR 论文方案落到当前 QYQuant 系统，而不是另做一个孤立的论文 demo。结论先行：

> QSGA 应工程化为 QYQuant 现有 AI 策略生成链路之上的“受约束策略合成与验证层”；QYIR 是生成过程中的可审计中间表示，最终产物仍应编译为当前系统的 QYSP v1 策略包，并继续经过现有导入、验证、沙箱、回测、报告、审核和用户确认链路。

这意味着工程目标不是“让 LLM 直接写更好的策略代码”，而是把自然语言策略生成拆成可观测、可验证、可拒绝、可修复、可回退的确定性流水线。

## 1. 当前系统可复用基础

当前仓库已经具备落地 QSGA 的主要底座。

| 能力 | 现有位置 | 可复用方式 |
|---|---|---|
| QYSP 策略包协议 | `docs/strategy-format/README.md`, `packages/qysp/src/qysp/schema/qysp.schema.json` | QSGA 的最终编译目标，不另造运行时格式 |
| QYSP 校验与打包 | `packages/qysp/src/qysp/validator.py`, `packages/qysp/src/qysp/builder.py` | 作为 `compiler_verifier` 和 package integrity verifier |
| 策略导入分析 | `backend/app/services/strategy_import_analysis.py` | 可复用 AST 入口检测、语法检测、import draft 机制 |
| 策略确认入库 | `backend/app/services/strategy_import_confirm.py` | QSGA 生成草稿后仍通过用户确认进入正式策略 |
| 运行时预检与沙箱 | `backend/app/strategy_runtime/`, `backend/app/services/sandbox.py` | 作为 execution verifier 和安全边界 |
| 回测执行 | `backend/app/backtest/engine.py`, `backend/app/tasks/backtests.py` | 作为 backtest verifier 和 risk auditor 数据来源 |
| 风险画像 | `backend/app/services/risk_profile.py`, `frontend/src/components/strategy/RiskProfileForm.vue` | 作为模糊风险偏好到结构化约束的产品侧归一化入口 |
| AI 策略生成入口 | `backend/app/services/ai_strategy_generation.py` | 当前 Direct LLM-to-Code 路径，可渐进替换为 QSGA pipeline |
| AI Strategy Lab | `frontend/src/views/AiStrategyLabView.vue` | 展示 QYIR、验证链、修复建议和最终草稿 |
| AI 生成历史 | `backend/app/models.py::AiGenerationSession`, `docs/plans/2026-04-26-ai-generation-history-design.md` | 保存 QSGA run、候选 QYIR、验证结果和用户采纳记录 |
| 报告 Agent 雏形 | `backend/app/report_agent/`, `docs/openai-agents-full-integration.md` | 复用“Agent 只编排、确定性服务执行”的原则 |
| 策略自动审核 | `docs/plans/2026-04-26-strategy-auto-review-design.md` | 复用 code safety、metadata、metrics threshold 思路 |

工程落地时不建议照论文稿新建独立 `qsga/` 根目录并复制一套 backtest/runtime。正确方向是新增后端领域模块，调用现有 QYSP、strategy_runtime、backtest、report_agent 能力。

建议模块边界：

```text
backend/app/qsga/
  schemas.py              # QYIR v1 Pydantic/dataclass schema
  pipeline.py             # QSGA 主流水线
  models.py               # run/step/artifact 序列化结构，不直接替代 DB model
  intent/
    normalize.py          # 自然语言到明确槽位的归一化
    safety.py             # unsupported/unsafe/ambiguous 判定
  verifiers/
    schema_verifier.py
    semantic_verifier.py
    qysp_verifier.py
    execution_verifier.py
    risk_auditor.py
  compiler/
    qyir_to_qysp.py       # QYIR -> strategy.json + src/strategy.py
    templates.py          # 受支持策略族模板
  repair/
    actions.py            # Error-Location-Action 映射
    operators.py          # 结构化修复算子
    loop.py
  evals/
    bench_loader.py
    metrics.py
```

## 2. 论文方案中必须工程化收敛的部分

### 2.1 QYIR 不能成为第二套生产策略协议

论文稿把 QYIR 描述为完整策略中间表示，这是研究叙事上成立的。但在当前系统中，生产协议已经是 QYSP v1。工程上应明确：

- QYIR 是策略生成过程中的中间计划、验证接口和修复定位结构。
- QYSP 是系统持久化、导入、回测、审核和分享的唯一策略包协议。
- QYIR 字段不能和 QYSP 长期分叉；每个 QYIR v1 字段必须定义到 QYSP manifest、参数、模板代码或解释报告的映射。

工程修改：

```text
Natural Language
  -> QYIR candidate
  -> QYIR validation
  -> QYSP project directory
  -> qys validate/build
  -> StrategyImportDraft
  -> user confirmation
  -> Strategy/StrategyVersion
```

### 2.2 不应再让 LLM 直接输出最终 Python 代码作为主路径

当前 `ai_strategy_generation.py` 要求模型返回 `{reply, strategy: {code, parameters, ...}}`，然后导入分析。这是 Direct LLM-to-Code 路径，适合作为 baseline，不适合作为高可靠主路径。

QSGA 主路径应改为：

1. LLM 只生成受限 QYIR JSON 候选，或者生成“槽位归一化建议”。
2. 后端用确定性 schema/domain verifier 检查 QYIR。
3. 后端用模板编译器生成 QYSP 策略项目。
4. 生成代码只来自受控模板和参数注入，不允许模型任意拼接代码。

LLM 可以参与解释、澄清问题、候选修复建议，但不能拥有最终代码写入权限。

### 2.3 “风险约束满足”必须改成历史回测条件下的可检测目标

论文稿里的 `max_drawdown <= 10%` 容易被产品用户理解为承诺未来风险。工程文档、接口和 UI 必须统一措辞：

- 只能说“在指定历史数据窗口的回测结果中满足/不满足风险阈值”。
- 不能说“保证最大回撤不超过 10%”。
- 风险修复是“降低历史回测中的风险暴露”，不是收益承诺。

Risk Auditor 应输出结构化结论：

```json
{
  "constraint": "max_drawdown",
  "target": -10.0,
  "observed": -14.8,
  "status": "violation",
  "scope": "historical_backtest",
  "data_range": {"start": "...", "end": "..."},
  "repairable": true,
  "recommended_actions": ["add_stop_loss", "reduce_position_weight"]
}
```

### 2.4 Semantic Verifier 只能验证显式和可归一化槽位

论文稿已经强调边界，但工程实现还要更硬：

- “稳一点”“不要太激进”不能被默认翻译成固定数值，除非产品明确提供默认风险画像。
- 如果没有可归一化规则，应返回 `clarification_required`。
- Semantic Slot F1 只用于 QSI-Bench / evaluation，不应该在生产环境展示为“语义准确率”。

当前系统已有 `build_risk_profile()`，可以作为“用户明确填写风险偏好”到 QYIR risk slots 的桥梁。但它不能替代澄清机制：只有当用户显式选择了风险等级、回撤容忍度、持仓比例等字段时，才允许把这些字段注入 QYIR。

生产输出建议：

```json
{
  "semantic_status": "clarification_required",
  "missing_slots": ["risk.max_drawdown_pct", "position.max_position_pct"],
  "question": "你希望最大历史回撤阈值设置为多少？例如 10%、15% 或 20%。"
}
```

### 2.5 Safe Rejection 不能只是关键词表

论文中 unsafe / unsupported intent 很重要，但生产上只靠关键词会误杀或漏放。应分层处理：

| 类型 | 判定来源 | 动作 |
|---|---|---|
| unsafe | 收益保证、内幕交易、规避监管、超高杠杆、确定性荐股 | 拒绝生成策略，给风险解释 |
| unsupported | 高频盘口、期权组合、分钟级订单簿、外部新闻实时交易等超出 QYIR v1 | 拒绝或转为“暂不支持” |
| ambiguous | 缺少市场、标的、周期、风险阈值等关键槽位 | 澄清 |
| supported | 可落入 QYIR v1 策略族和约束范围 | 继续生成 |

Safe Rejection 结果需要进入审计日志，后续作为 red-team eval 数据。

### 2.6 Repair Loop 必须是带前置条件和后置验证的确定性循环

论文中的修复算子需要工程化为有约束的结构变换，而不是“让 LLM 再改一次”。

每个 repair operator 必须定义：

- `trigger`: 触发错误类型和字段位置。
- `precondition`: 策略族、参数范围、当前 QYIR 状态是否允许。
- `patch`: 对 QYIR 的结构化变更。
- `postcondition`: 重新编译、预检、回测和风险审计必须通过。
- `max_attempts`: 防止无限修复。
- `semantic_drift_check`: 修复不能改变用户核心策略意图。

示例：

```text
risk_violation:/risk/max_drawdown
  -> AddStopLoss
  -> patch qyir.exit_rules.stop_loss_pct
  -> compile QYSP
  -> run historical backtest
  -> re-audit max_drawdown
```

### 2.7 QSI-Bench 是评测资产，不是线上业务数据

QSI-Bench-80 应独立维护在 `backend/tests/fixtures/` 或 `docs/research/` 下，作为 CI 或离线实验集。不要把它混入生产数据库。

建议拆成两套数据：

- Research benchmark：用于论文主结果、baseline、ablation。
- Production eval set：从脱敏真实失败样本、拒绝样本、用户修复样本沉淀，进入回归测试。

## 3. 目标工程架构

### 3.1 主流程

```text
Frontend AI Strategy Lab
  |
POST /api/strategy-ai/generate
  |
QSGA Pipeline
  |
  |-- Input Guardrails
  |     - auth / quota / provider capability
  |     - unsafe / unsupported / ambiguous detection
  |
  |-- Intent Normalization
  |     - natural language -> explicit slots
  |     - missing slot detection
  |
  |-- QYIR Candidate Generation
  |     - LLM structured output or constrained JSON
  |
  |-- Verification Chain
  |     - schema/type verifier
  |     - semantic slot verifier
  |     - domain constraint verifier
  |
  |-- Deterministic Compiler
  |     - QYIR -> QYSP strategy.json
  |     - QYIR -> src/strategy.py from approved templates
  |
  |-- QYSP/Runtime Verification
  |     - qysp validate_schema
  |     - import analysis
  |     - sandbox source guard
  |
  |-- Optional Backtest Verification
  |     - Celery backtest job
  |     - metrics extraction
  |     - risk audit
  |
  |-- Repair Loop
  |     - deterministic QYIR patch
  |     - recompile and reverify
  |
  |-- Draft Packaging
        - StrategyImportDraft
        - analysis payload
        - user-facing explanation
```

### 3.2 关键设计原则

1. Agent 只做编排与解释，不直接执行写入动作。
2. QYIR 只作为中间表示，不能绕过 QYSP。
3. 任何可保存策略必须通过 QYSP schema、AST guard、沙箱预检。
4. 回测和风险审计必须异步化，避免 API 请求线程阻塞。
5. 任何失败都要结构化：错误类型、位置、可修复性、下一步动作。
6. 每次生成必须可审计：输入摘要、模型、QYIR、验证链、修复链、最终产物 hash。

### 3.3 建议 API

第一阶段可保持现有 `POST /api/strategy-ai/generate`，新增可选模式：

```json
{
  "integrationId": "...",
  "sessionId": "...",
  "messages": [{"role": "user", "content": "..."}],
  "mode": "qsga",
  "options": {
    "runBacktest": false,
    "maxRepairAttempts": 2
  }
}
```

响应建议：

```json
{
  "sessionId": "...",
  "runId": "...",
  "status": "draft_ready|clarification_required|rejected|blocked|running",
  "reply": "...",
  "qyir": {"...": "..."},
  "verification": {
    "schema": {"status": "pass"},
    "semantic": {"status": "pass"},
    "qysp": {"status": "pass"},
    "execution": {"status": "not_run"},
    "risk": {"status": "not_run"}
  },
  "repairHistory": [],
  "analysis": {
    "draftImportId": "..."
  }
}
```

如启用回测验证，应返回 `running` 和 `runId`，由前端轮询或 SSE 订阅。

## 4. QYIR v1 应对齐当前 QYSP 能力

论文稿中的 QYIR v1 建议范围是均线交叉、动量轮动、低波动过滤。当前 QYSP 模板已有 trend following、momentum、mean reversion、multi indicator。工程上建议先收敛为四类受支持策略族：

| QYIR strategy_family | QYSP template | 说明 |
|---|---|---|
| `trend_following` | `packages/qysp/src/qysp/templates/trend_following` | 均线/趋势跟随 |
| `momentum` | `packages/qysp/src/qysp/templates/momentum` | 动量轮动或单标的动量 |
| `mean_reversion` | `packages/qysp/src/qysp/templates/mean_reversion` | 超买超卖/回归 |
| `multi_indicator` | `packages/qysp/src/qysp/templates/multi_indicator` | 多指标组合，但只开放白名单指标 |

QYIR v1 最小字段：

```json
{
  "version": "1.0",
  "intent": {
    "raw_text": "...",
    "language": "zh-CN",
    "intent_type": "supported|ambiguous|unsupported|unsafe"
  },
  "strategy": {
    "family": "trend_following|momentum|mean_reversion|multi_indicator",
    "direction": "long_only|flat_or_long",
    "timeframe": "1d|4h|1h|15m"
  },
  "universe": {
    "market": "crypto|gold|stock|futures",
    "symbols": ["BTCUSDT"]
  },
  "signals": [
    {
      "name": "fast_ma",
      "indicator": "ma|return|volatility|rsi",
      "window": 20,
      "operator": "cross_up|cross_down|gt|lt|rank_top_k",
      "threshold": null
    }
  ],
  "risk": {
    "max_drawdown_pct": 15,
    "stop_loss_pct": 5,
    "take_profit_pct": 10,
    "max_position_pct": 30
  },
  "execution": {
    "rebalance": "on_signal|daily|weekly|monthly",
    "max_orders_per_day": 2
  },
  "explanation": {
    "audience": "beginner",
    "include_risk_warning": true
  }
}
```

所有字段必须有：

- schema 类型约束；
- 支持范围；
- 默认值策略；
- QYSP manifest 映射；
- strategy template 参数映射；
- verifier 规则；
- 是否允许 repair operator 修改。

## 5. 高可靠落地所需能力

### 5.1 Guardrails

输入侧：

- 用户只能使用自己的 AI integration。
- provider 必须具备结构化输出或至少稳定 JSON 输出能力。
- prompt 中不能包含 API key、券商密钥等 secret。
- 超出支持范围的市场/频率/策略族直接 blocked 或 clarification。
- unsafe 请求拒绝并记录。

工具侧：

- 编译器只允许使用白名单模板。
- 禁止模型产生任意 import、文件访问、网络访问。
- 每次 backtest 设置最大 bars、最大 timeout、最大任务数。
- 高成本回测必须消耗额度或走用户确认。

输出侧：

- 禁止收益保证、确定性荐股、未来收益承诺。
- 所有风险结论都标明“历史回测窗口”。
- 生成草稿默认不是正式策略，必须用户确认。
- 策略发布仍走 marketplace review。

### 5.2 可观测性

建议新增 QSGA run 级审计结构，可先落到 `AiGenerationSession.analysis`，后续再建独立表：

```text
qsga_runs
  id
  owner_id
  session_id
  status
  model_name
  provider_key
  input_hash
  qyir_hash
  qysp_package_hash
  started_at
  completed_at
  error_code

qsga_steps
  run_id
  step_name
  status
  latency_ms
  input_summary
  output_summary
  error_code

qsga_repairs
  run_id
  operator
  trigger
  before_hash
  after_hash
  status
```

日志原则：

- 记录摘要和 hash，不记录 secret。
- 原始 prompt 若保存，必须可配置、可脱敏、可删除。
- 每个 run 可重放到相同 QYIR 和 QYSP package。

### 5.3 测试矩阵

| 层级 | 必测内容 |
|---|---|
| Unit | QYIR schema、intent safety、semantic verifier、compiler mapping、repair operator |
| Contract | `POST /strategy-ai/generate` 响应状态、错误码、analysis payload 兼容性 |
| Integration | QYIR -> QYSP -> validate -> import draft -> confirm -> backtest |
| Sandbox | forbidden import/builtin、timeout、无入口、错误返回 |
| Risk | max drawdown、position pct、turnover 等阈值判断 |
| Eval | QSI-Bench-80 主指标、unsafe/unsupported red-team 集 |
| Frontend | AI Lab 展示 QYIR 状态、验证链、clarification、rejection、draft adoption |
| Regression | 历史失败样本必须进入 fixture，防止修复后回退 |

最低 CI 门槛：

- QYIR schema golden tests。
- 每个策略族至少 3 个从自然语言到 QYSP 的编译样本。
- 每个 safe rejection 类型至少 5 个 red-team 样本。
- 每个 repair operator 至少覆盖 pass、not_applicable、failed 三种结果。

### 5.4 灰度与回退

新增 feature flag：

```text
QYQUANT_QSGA_ENABLED=false
QYQUANT_QSGA_BACKTEST_VERIFY_ENABLED=false
QYQUANT_QSGA_REPAIR_ENABLED=false
QYQUANT_QSGA_MAX_REPAIR_ATTEMPTS=2
QYQUANT_QSGA_RUN_TIMEOUT_SECONDS=120
QYQUANT_QSGA_TOOL_TIMEOUT_SECONDS=30
```

灰度顺序：

1. 开发环境只跑 QYIR schema 和 compiler。
2. 测试环境开启 QSGA dry-run，不替换现有生成结果。
3. 小流量用户开启 QSGA draft-only，不自动回测。
4. Pro/Ultra 用户开启 backtest verification。
5. 稳定后将 Direct LLM-to-Code 降为 fallback/baseline。

回退策略：

- QSGA pipeline 失败时返回结构化错误，不自动切回 Direct LLM-to-Code 保存草稿。
- 如需要 fallback，只能以“普通 AI 草稿，未经 QSGA 验证”明确标记。
- feature flag 关闭后，现有 AI Strategy Lab 和 import 流程仍可工作。

## 6. 分阶段实施计划

### Phase 0：设计冻结与范围收敛

产物：

- 本文档评审通过。
- QYIR v1 schema 草案。
- QYIR -> QYSP 字段映射表。
- 支持策略族、指标、市场、频率、风险约束白名单。

验收：

- 不再把 QYIR 当生产策略包格式。
- 明确 Direct LLM-to-Code 是 baseline/fallback，不是高可靠主路径。

### Phase 1：QYIR Schema 与确定性编译器

产物：

- `backend/app/qsga/schemas.py`
- `backend/app/qsga/compiler/qyir_to_qysp.py`
- 每个策略族的模板映射。
- QYSP validate/build 集成测试。

验收：

- 4 类策略族可从手写 QYIR 编译为 QYSP 项目。
- 编译产物通过 `qysp.validator.validate_schema`。
- 不调用 LLM 也能完成 QYIR -> QYSP。

### Phase 2：Guardrails 与验证链

产物：

- intent safety classifier/rules。
- schema/domain/semantic verifier。
- qysp/runtime verifier。
- 结构化错误类型。

验收：

- ambiguous 返回澄清。
- unsupported/unsafe 返回拒绝。
- supported 才进入编译。
- 错误定位到 QYIR JSON pointer 或 QYSP 字段。

### Phase 3：接入 AI Strategy Lab 的 QSGA dry-run

产物：

- `generate_strategy_draft(..., mode="qsga")`。
- AI Lab 展示 QYIR、验证链、draft 状态。
- `AiGenerationSession` 保存 run 摘要。

验收：

- 不破坏现有 AI Lab。
- QSGA 失败时 UI 能解释 blocked/clarification/rejected。
- 用户只能采纳通过验证的 draft。

### Phase 4：Backtest Verifier 与 Risk Auditor

产物：

- 异步 backtest verification。
- risk auditor 结构化结果。
- 历史数据范围和数据源记录。

验收：

- 风险判断不阻塞 API 请求线程。
- 最大回撤、仓位、换手至少三类约束可审计。
- UI 明确“历史回测结果”，不暗示未来保证。

### Phase 5：Repair Loop

产物：

- AddStopLoss。
- ReducePositionWeight。
- LowerRebalanceFrequency。
- repair history。

验收：

- 每个 operator 有 pre/postcondition。
- 修复后必须重新编译、验证、回测、风险审计。
- 超过最大尝试次数返回 blocked，不无限循环。

### Phase 6：论文实验与生产 eval

产物：

- QSI-Bench-80。
- Direct LLM-to-Code、JSON Schema、Agent without QYIR baseline。
- 主指标和消融脚本。
- 生产 red-team regression set。

验收：

- 论文指标可复现。
- CI 能跑小型 smoke eval。
- 线上失败样本可沉淀为回归集。

## 7. 完备落地的完成定义

可以认为 QSGA 工程化完成，需要同时满足：

- 自然语言输入不会直接变成可保存 Python 策略代码。
- 所有正式草稿都经过 QYIR、QYSP、sandbox、runtime 或 backtest verifier。
- unsafe/unsupported/ambiguous 三类边界有独立处理和测试。
- 修复是确定性 QYIR patch，不是模型自由重写。
- 风险输出只描述历史回测约束满足情况。
- 每次生成有 run/step/artifact 审计记录。
- 用户采纳前能看到策略逻辑、参数、验证状态、风险提示。
- feature flag 可一键关闭 QSGA，旧流程不受影响。
- 论文 benchmark 与生产 eval 分离管理。

## 8. 不建议做的事

- 不建议新建一套独立策略运行时绕过 QYSP。
- 不建议把 QYIR 直接暴露为用户可上传格式。
- 不建议让 LLM 任意输出 `src/strategy.py` 作为主路径。
- 不建议把“最大回撤阈值”描述成未来风险承诺。
- 不建议一开始就做多 Agent 全量编排；Strategy Agent 应在 QSGA deterministic service 稳定后再接入。
- 不建议把 QSI-Bench 的论文实验数据和线上用户数据混用。

## 9. 下一步建议

最小可执行下一步不是改 UI，也不是先写 Agent，而是先做一个后端竖切：

1. 固定 QYIR v1 schema。
2. 选定 `trend_following` 和 `momentum` 两个策略族做最小编译器。
3. 手写 10 条 supported QYIR fixture。
4. 验证 QYIR -> QYSP -> validate -> import draft 全链路。
5. 再把 LLM 接到 QYIR candidate generation。

这条路径最短，也最能证明论文方案对当前系统的工程价值。

后续文档可按主题拆分到 `docs/qsga/`：

```text
docs/qsga/
  README.md
  qyir-v1-spec.md
  qyir-to-qysp-compiler.md
  verification-chain.md
  repair-operators.md
  safety-and-guardrails.md
  ai-lab-product-flow.md
  eval-and-qsi-bench.md
  rollout-observability.md
```

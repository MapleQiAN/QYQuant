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
    "classification": "supported|ambiguous|unsupported|unsafe"
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

当前完成基线：

- 已建立 `backend/app/qsga/` 后端领域模块，包含 `schemas.py`、`result.py`、`pipeline.py`、`compiler/qyir_to_qysp.py`、`compiler/template_registry.py`、`verifiers/schema_verifier.py`。
- 已定义 QYIR v1 的基础枚举、必需顶层字段、结构化 `VerificationResult` / `VerificationError`。
- 已实现 schema verifier，覆盖必需字段、版本、intent classification、策略族、方向、周期、市场、标的列表、signal 引用、指标白名单、窗口范围、风险百分比、执行频率等基础约束。
- 已实现 `trend_following` 与 `momentum` 两个策略族到现有 QYSP 模板的确定性映射，编译产物写入 `strategy.json` 与 `src/strategy.py`。
- 已通过 `qysp.validator.validate` 验证编译产物，并在 `build_qsga_draft()` 中打包为 `.qys` 后复用 `analyze_strategy_import()` 生成 `StrategyImportDraft`。
- 已建立 `backend/tests/fixtures/qsga/` golden fixtures，覆盖 `trend_following_basic.json`、`momentum_basic.json` 与 invalid cases。
- 已建立 `backend/tests/test_qsga_schema.py`、`backend/tests/test_qsga_compiler.py`、`backend/tests/test_qsga_pipeline.py`，覆盖 schema、compiler、pipeline draft 竖切。

Phase 1 剩余偏差：

- 原目标写到“4 类策略族”，当前完成的是 2 类：`trend_following`、`momentum`。`mean_reversion` 与 `multi_indicator` 应降级为 Phase 2/3 后续扩展，不阻塞验证链建设。
- 当前 schema verifier 仍是轻量结构校验，尚未实现 semantic/domain/runtime guardrails。
- 当前 `build_qsga_draft()` 的入口假设输入已经是 supported QYIR；Phase 2 需要在进入编译前增加分类、拒绝、澄清与结构化阻断。

原计划验收：

- 4 类策略族可从手写 QYIR 编译为 QYSP 项目。
- 编译产物通过 `qysp.validator.validate_schema`。
- 不调用 LLM 也能完成 QYIR -> QYSP。

进入 Phase 2 的实际准入条件：

- `trend_following` 与 `momentum` 两条 supported fixture 能完成 QYIR -> QYSP -> validate -> import draft。
- schema verifier 能对 invalid fixtures 返回结构化错误。
- QSGA pipeline 不依赖 LLM，后续 guardrails 可以直接插入编译前。

### Phase 2：Guardrails 与验证链

目标：

在 Phase 1 已能“手写 supported QYIR -> QYSP draft”的基础上，补齐进入编译前后的验证链，使 QSGA pipeline 能明确区分 `draft_ready`、`clarification_required`、`rejected`、`blocked`、`failed`，并保证只有 supported 且验证通过的 QYIR 才能进入确定性编译器。

范围：

- 包含：intent safety classifier/rules、classification gate、semantic/domain verifier、qysp/runtime verifier、统一 verification chain 输出、red-team/golden fixtures。
- 不包含：LLM 自然语言生成 QYIR、AI Lab UI 接入、异步 backtest verifier、risk auditor、repair loop。
- Phase 2 不输出历史回测风险结论；历史回测、风险审计和风险修复仍归属 Phase 4/5。
- `mean_reversion` / `multi_indicator` 可作为 Phase 1 gap closure 或 Phase 2 独立子任务扩展，但不能阻塞 Guardrails 主线。

产物：

- intent safety classifier/rules。
- schema/domain/semantic verifier。
- qysp/runtime verifier。
- 结构化错误类型。

建议文件边界：

```text
backend/app/qsga/
  guardrails/
    __init__.py
    intent_classifier.py       # supported / ambiguous / unsupported / unsafe
    policies.py                # 硬拒绝、暂不支持、澄清规则与策略空间
  verifiers/
    domain_verifier.py         # QYIR 字段组合、策略族能力、参数范围二次校验
    semantic_verifier.py       # 用户显式槽位是否被覆盖、是否被弱化
    qysp_verifier.py           # QYSP validate/build/import analysis 包装
    runtime_verifier.py        # runtime/sandbox 预检接口占位，Phase 4 再接回测
  errors.py                    # 统一错误码、状态、JSON pointer/path 约定
  pipeline.py                  # 串联 guardrails -> verifiers -> compiler

backend/tests/fixtures/qsga/
  guardrails_cases.json
  semantic_cases.json
  domain_invalid_cases.json

backend/tests/
  test_qsga_guardrails.py
  test_qsga_verification_chain.py
  test_qsga_semantic_verifier.py
  test_qsga_domain_verifier.py
  test_qsga_pipeline_guardrails.py
```

任务拆分：

1. 输入与意图安全门禁：新增 guardrails 规则、unsafe/unsupported/ambiguous fixtures，并证明这些分支不会调用 compiler、build package 或 import draft。
2. 验证链编排与结构化错误：复用 `verify_qyir_schema()`，新增 domain/semantic/qysp/runtime verifier 包装，并统一每层返回的 `status`、`errors`、`questions`。
3. Pipeline gate 接入：让 pipeline 只在 guardrails/schema/domain/semantic/qysp/runtime 预检通过后进入 `compile_qyir_to_qysp_project()` 与 `analyze_strategy_import()`。
4. 测试矩阵补齐：覆盖 supported trend/momentum、ambiguous missing slot、unsupported strategy family/market、unsafe request、semantic constraint weakening、QYSP validation failure、runtime guard failure。

#### Phase 2.1：结构化错误与状态协议

先把错误协议固定，否则后续 verifier 会各写各的返回格式。

新增/扩展约定：

```json
{
  "status": "pass|fail|blocked|clarification_required|rejected",
  "errors": [
    {
      "code": "UNSAFE_INTENT",
      "path": "$.intent.raw_text",
      "message": "请求包含保证收益或违法违规意图，不能生成策略草案",
      "severity": "error",
      "category": "safety",
      "repairable": false
    }
  ],
  "questions": [
    {
      "id": "risk.max_drawdown_pct",
      "path": "$.risk.max_drawdown_pct",
      "message": "你希望历史回测最大回撤阈值设置为多少？",
      "options": [10, 15, 20]
    }
  ]
}
```

实现要求：

- 保留现有 `VerificationResult.to_dict()` 兼容形态，但扩展 `category`、`repairable`、`questions` 时不能破坏已有 schema 测试。
- 所有错误必须有稳定 `code` 和 JSON pointer 风格 `path`。
- pipeline 只根据结构化 `status` 分支，不解析中文 message。

#### Phase 2.2：Intent Safety Classifier / Guardrails

第一版采用确定性规则优先，不把最终裁决交给 LLM。

分类规则：

| 分类 | 触发示例 | Pipeline 状态 | 下一步 |
|---|---|---|---|
| `supported` | “做一个黄金日线双均线策略，仓位不超过 30%” | 继续验证 | schema/domain/semantic |
| `ambiguous` | “稳一点”“不要亏太多”“最近表现好”但缺少可归一化风险/窗口 | `clarification_required` | 返回问题，不编译 |
| `unsupported` | 高频盘口、期权复杂组合、外部新闻实时交易、未接入市场 | `rejected` 或 `blocked` | 说明暂不支持 |
| `unsafe` | 保证收益、稳赚不亏、内幕消息、规避监管、超高杠杆 | `rejected` | 拒绝生成并记录 |

最低规则集：

- `unsafe`: `稳赚`、`保证收益`、`必赚`、`内幕`、`规避监管`、`无风险高收益`、`满仓杠杆`、`借钱炒`。
- `unsupported`: `期权`、`期货套利`、`盘口`、`高频`、`秒级`、`新闻实时`、`自动实盘`。
- `ambiguous`: `稳一点`、`别太激进`、`不要亏太多`、`最近`、`长期`、`低风险` 且未提供明确风险画像或数值槽位。

验收用例：

- unsafe case 不得进入 `compile_qyir_to_qysp_project()`。
- unsupported case 不得生成 `.qys` 或 `StrategyImportDraft`。
- ambiguous case 返回至少一个 `questions[]`，且问题必须绑定缺失槽位 path。
- supported case 在 Phase 1 fixtures 上保持 `draft_ready`。

#### Phase 2.3：Domain Verifier

Domain verifier 负责检查 QYIR 字段之间的组合约束，不重复 schema verifier 的类型检查。

首批规则：

- `intent.classification` 必须是 `supported` 才允许进入编译。
- `strategy.family` 必须存在于 `template_registry.TEMPLATE_REGISTRY`。
- signal `operator` 与 strategy family 必须匹配：`trend_following` 至少需要一个 cross/reference 组合；`momentum` 允许 `ema`、`ma`、`return`，但必须有可映射的快慢窗口。
- `risk.max_position_pct` 不得高于新手默认上限；如果 intent/user profile 标记 novice，建议上限为 50。
- `execution.max_orders_per_day` 与 `execution.rebalance` 不能矛盾：`daily/monthly` 不能设置异常高频订单上限。
- `universe.market` 与 symbols 做轻量格式检查：`gold` 支持 `XAUUSD`；`crypto` 支持 `*USDT`；其余市场先只做非空占位。

输出示例：

```json
{
  "status": "fail",
  "errors": [
    {
      "code": "DOMAIN_STRATEGY_SIGNAL_MISMATCH",
      "path": "$.signals",
      "message": "trend_following 策略需要可编译的快慢均线交叉信号",
      "severity": "error",
      "category": "domain",
      "repairable": false
    }
  ]
}
```

#### Phase 2.4：Semantic Verifier

Semantic verifier 不做“自然语言全理解”，只验证显式槽位没有被遗漏或弱化。

输入建议：

```python
verify_semantic_slots(qyir: dict, expected_slots: dict | None = None) -> VerificationResult
```

第一版可先从 QYIR 自带字段中验证明确约束：

- `intent.raw_text` 或 `intent.normalized_summary` 明确出现“仓位不超过 N%”，则 `risk.max_position_pct <= N`。
- 明确出现“最大回撤 N%”，则 `risk.max_drawdown_pct <= N`。
- 明确出现“止损 N%”，则 `risk.stop_loss_pct <= N` 或等于用户给定阈值。
- 明确出现“不要频繁交易/月度/每月”，则 `execution.rebalance` 不得高于 `monthly`。
- 明确出现“不加杠杆/低风险”，不得出现高仓位、做空、杠杆方向；当前 QYIR v1 没有 leverage 字段时，先要求 `direction` 为 `long_only|flat_or_long` 且 `max_position_pct <= 50`。

不做的事：

- 不把“稳一点”静默翻译成 10% 回撤。
- 不在生产响应中输出 Semantic Slot F1。
- 不让 LLM 判定 verifier 是否通过。

#### Phase 2.5：QYSP / Runtime Verifier 包装

当前 `pipeline.py` 已直接调用 `qysp.validator.validate()` 与 `analyze_strategy_import()`。Phase 2 应把这部分封装为 verifier，统一返回结构化结果：

```text
schema verifier
  -> guardrails
  -> domain verifier
  -> semantic verifier
  -> compiler
  -> qysp verifier
  -> import analysis verifier
  -> draft packaging
```

QYSP verifier 至少检查：

- `qysp.validator.validate(project_dir)["valid"]`。
- `build_package(project_dir, ...)` 可成功生成 `.qys`。
- `analyze_strategy_import()` 返回 entrypoint candidate，且 `callable == "on_bar"`。
- analysis payload 不包含 fatal error。

Runtime verifier 在 Phase 2 只保留接口和非执行预检，不启动真实回测：

- 检查 entrypoint、manifest、参数默认值、risk 字段是否可传入现有 runtime。
- 输出 `status: "not_run"` 或 `status: "pass"`，为 Phase 4 接 backtest verifier 留出契约。

#### Phase 2.6：Pipeline 改造

Phase 2 的 pipeline 应从“只接受已验证 QYIR 并生成 draft”升级为“可拒绝、可澄清、可阻断”的状态机。

建议响应：

```json
{
  "status": "clarification_required|rejected|blocked|draft_ready",
  "verification": {
    "guardrails": {"status": "pass", "errors": []},
    "schema": {"status": "pass", "errors": []},
    "domain": {"status": "pass", "errors": []},
    "semantic": {"status": "pass", "errors": []},
    "qysp": {"status": "pass", "errors": []},
    "runtime": {"status": "not_run", "errors": []}
  },
  "analysis": {
    "draftImportId": "..."
  }
}
```

分支要求：

- `clarification_required`: 不编译、不建 draft。
- `rejected`: 不编译、不建 draft，返回拒绝原因。
- `blocked`: 输入原则上支持，但当前 verifier 或配置缺口阻止继续，返回可修复工程原因。
- `draft_ready`: 才能包含 `draftImportId`。

#### Phase 2.7：测试与验收清单

单元测试：

- `test_qsga_guardrails.py`
  - unsafe: 保证收益、内幕、规避监管全部 rejected。
  - unsupported: 期权、高频、自动实盘全部 blocked/rejected。
  - ambiguous: 模糊风险表达返回 questions。
  - supported: Phase 1 两个 fixture 通过。
- `test_qsga_domain_verifier.py`
  - strategy family 与 signal/operator 不匹配时报 `DOMAIN_STRATEGY_SIGNAL_MISMATCH`。
  - novice 高仓位时报 `DOMAIN_RISK_TOO_AGGRESSIVE`。
  - market/symbol 格式不匹配时报结构化错误。
- `test_qsga_semantic_verifier.py`
  - 用户要求仓位不超过 30%，QYIR 写 50% 时失败。
  - 用户要求月度调仓，QYIR 写 daily 时失败。
  - 用户要求最大回撤 10%，QYIR 写 20% 时失败。
- `test_qsga_pipeline_guardrails.py`
  - rejected/clarification case 不产生 `StrategyImportDraft`。
  - supported fixture 仍能产生 `draft_ready`。

集成验收：

- Phase 1 既有测试全部保持通过。
- supported fixtures 仍能完成 QYIR -> QYSP -> `.qys` -> import draft。
- ambiguous / unsupported / unsafe 三类输入不会触发编译器和打包器。
- 每个失败结果都包含稳定错误码、path、category、repairable。
- 文档中的状态枚举与 pipeline 响应保持一致。

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

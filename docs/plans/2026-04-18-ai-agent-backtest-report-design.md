# AI Agent-Driven Backtest Report Design

> Date: 2026-04-18
> Status: Design Approved
> Covers: Report architecture, AI Agent system, tiered access, technical implementation

## 1. Overview

Backtest report system powered by AI Agents. Replaces static metrics display with dynamic, layered reports that include AI narration, deep diagnostics, strategy comparison, and conversational Q&A.

### 1.1 Goals

- Transform raw backtest results into professional tearsheet-grade reports
- AI-driven narration that adapts to user's subscription tier
- Conversational interface for follow-up questions on report data
- Proactive alerts for strategy weaknesses and optimization opportunities

### 1.2 Design Principles

- **Tiered depth**: Report richness scales with subscription plan (free/go → plus → pro → ultra)
- **Separation of computation and narration**: Quant Engine (pure Python) handles calculations; LLM handles natural language
- **3-Agent architecture**: Narrator, Diagnostician, Advisor — specialized but manageable
- **Post-compute trigger**: Reports auto-generate after backtest completion via Celery

## 2. Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Frontend (Vue 3)                    │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐ │
│  │ Report   │  │ Chat     │  │ Visualization     │ │
│  │ Viewer   │  │ Panel    │  │ (Charts/Tables)   │ │
│  └────┬─────┘  └────┬─────┘  └───────┬───────────┘ │
└───────┼──────────────┼────────────────┼─────────────┘
        │ REST/SSE     │ WebSocket      │ REST
┌───────┼──────────────┼────────────────┼─────────────┐
│       ▼              ▼                ▼              │
│  ┌────────────────────────────────────────────────┐ │
│  │       Backtest Report Agent (Flask)            │ │
│  │                                                │ │
│  │  ┌──────────────┐     ┌─────────────────────┐  │ │
│  │  │ Quant Engine │     │ LLM Narrator        │  │ │
│  │  │ (Python)     │     │ (Claude/GPT)        │  │ │
│  │  │              │     │                     │  │ │
│  │  │ · 30+ metrics│     │ · Narrator Agent    │  │ │
│  │  │ · Chart data │     │ · Diagnostician     │  │ │
│  │  │ · Anomaly    │     │ · Advisor Agent     │  │ │
│  │  │ · Monte Carlo│     │                     │  │ │
│  │  │ · Regime     │     │                     │  │ │
│  │  └──────┬───────┘     └──────────┬──────────┘  │ │
│  │         │                        │              │ │
│  │         ▼                        ▼              │ │
│  │  ┌──────────────────────────────────────────┐   │ │
│  │  │         Report Orchestrator               │   │ │
│  │  │  · Tier-based output filtering            │   │ │
│  │  │  · Chat context management                │   │ │
│  │  │  · Proactive alert triggering             │   │ │
│  │  └──────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### 2.1 Component Responsibilities

| Component | Role | Model |
|-----------|------|-------|
| **Quant Engine** | Pure Python computation: metrics, chart data, anomaly detection, Monte Carlo, regime analysis | N/A (code) |
| **Narrator Agent** | Executive summaries, metric explanations, chat Q&A for basic queries | Haiku (fast, cheap) |
| **Diagnostician Agent** | Anomaly narration, overfitting explanation, MC interpretation, regime analysis narration | Sonnet (deep reasoning) |
| **Advisor Agent** | Strategy comparison, optimization suggestions, proactive alerts, portfolio advice | Sonnet/Opus |
| **Report Orchestrator** | Schedules phases, filters by tier, manages chat routing | N/A (code) |

## 3. Report Modules

### 3.1 Module 1: Basic Report Layer (Quant Engine)

**Metrics (30+)**:

```
Performance             Risk                    Trade Stats           Period Analysis
──────────────          ──────────────          ─────────────         ────────────────
Total Return            Annual Volatility       Total Trades          Monthly Returns
CAGR                    Downside Deviation      Win Rate              Yearly Returns
Alpha                   Max Drawdown            Loss Rate             Best/Worst Day
Beta                    Avg Drawdown            Profit Factor         Best/Worst Month
Sharpe Ratio            Max DD Duration         Avg Win/Loss          Best/Worst Year
Sortino Ratio           VaR (95%, 99%)          Payoff Ratio          Rolling Returns
Calmar Ratio            CVaR                    Max Consec Win/Loss   Crisis Performance
Omega Ratio             Skewness                Avg Trade Duration
Information Ratio       Kurtosis                Trade Frequency
Up/Down Capture         Tracking Error
                        Correlation
```

**Visualizations**:

| Chart | Data Source | Interaction |
|-------|------------|-------------|
| Equity curve (strategy vs benchmark) | Cumulative daily returns | Zoom, range select |
| Drawdown underwater plot | Peak-to-trough series | Hover for date/depth |
| Rolling Sharpe (6M) | Rolling window computation | Adjustable range |
| Monthly returns heatmap | Monthly return matrix | Year filter |
| Return distribution histogram | Daily returns + normal fit | Interval stats |
| Top 10 drawdowns table | Sorted drawdown list | Click to locate on equity curve |

### 3.2 Module 2: AI Narration Layer (Narrator Agent)

**a) Executive Summary** (auto-generated on report creation)

```
Input:  Full metrics + equity curve key points + drawdown events
Output: 2-3 paragraph natural language summary
Example: "This moving average crossover strategy returned 47.2% cumulatively
         over 2023-01 to 2025-12, with 18.6% annualized return and Sharpe of
         1.42. Maximum drawdown of -12.3% occurred during the April 2024 Fed
         rate hike period. Strategy excels in range-bound markets but reacts
         slowly to trend reversals, lagging an average of 8 trading days."
```

**b) Metric Card Annotations** (per-metric AI commentary)

```
Input:  Single metric value + industry percentile + strategy type
Output: One-sentence contextual explanation
Example: "Sharpe 1.42 — ranks in the top 30% of trend-following strategies,
         indicating strong risk-adjusted returns"
```

**c) Conversational Q&A** (user-initiated)

```
Context: Full backtest data + chat history
Capabilities:
  - "Why did March perform poorly?" → Agent locates trades in period, explains
  - "How does it compare to buy-and-hold?" → Computes benchmark comparison
  - "What was held during max drawdown?" → Locates positions, analyzes concentration
```

### 3.3 Module 3: Deep Diagnostics Layer (Diagnostician Agent)

**a) Anomaly Detection**

```
Detection items:
  · Return outliers (> 3σ) — flag and explain
  · Abnormal drawdown depth — compare against strategy-type percentiles
  · Trade frequency regime change — detect shift points
  · Consecutive loss streaks — flag strategy failure signals
Output: Anomaly list + natural language explanation per item
```

**b) Overfitting Detection**

```
Methods:
  · Parameter sensitivity scan — ±20% per parameter, compute Sharpe change rate
  · Stability score — standard deviation of Sharpe change rates (lower = more stable)
  · Out-of-sample decay — In-sample vs OOS Sharpe ratio
  · Trade concentration — Top N trades as % of total profit
Output: Overfitting risk rating (low/medium/high) + evidence narration
```

**c) Monte Carlo Simulation**

```
Method: Resample from historical trade distribution, 1000 iterations
Output:
  · Return distribution (5th, 25th, 50th, 75th, 95th percentile)
  · Max drawdown probability distribution
  · Ruin probability (>50% drawdown)
  · AI narration: "Across 1000 simulations, 87% achieved >10% annualized return,
    with a 12% probability of >30% drawdown"
```

**d) Market Regime Analysis**

```
Method: Classify based on volatility + trend strength (bull/bear/range/crisis)
Output:
  · Strategy performance per regime (Return, Sharpe, DD per regime)
  · Regime transition points marked
  · AI narration: "Strategy performs best in bull markets (R²=0.82), Sharpe drops
    to 0.3 in bear markets — consider pairing with a defensive strategy"
```

### 3.4 Module 4: Comparison & Recommendation Layer (Advisor Agent)

**a) Strategy Comparison**

```
Data source: Historical backtest results of similar strategies in the library
Comparison dimensions:
  · Risk-adjusted return ranking
  · Factor exposure similarity
  · Drawdown characteristics
Output: Top 5 similar strategies + differential analysis narration
```

**b) Optimization Suggestions**

```
Trigger conditions:
  · Overfitting detection = "medium" or "high"
  · Sharpe < 0.5
  · Max DD > 30%
  · Trade concentration > 50%

Output:
  · Parameter adjustment suggestions + expected impact
  · Risk management rules (stop-loss, position sizing, filters)
  · Portfolio pairing suggestions (complementary strategy types)
```

**c) Proactive Alerts**

```
Auto-checked on report generation:
  ⚠️ "73% of profit from 3 trades — strategy stability is questionable"
  ⚠️ "OOS Sharpe decay of 62% — high overfitting risk"
  ⚠️ "Bear market losses exceed benchmark — lacks downside protection"
  💡 "Pairing with an RSI strategy could reduce bear market drawdown — suggest backtest verification"
```

## 4. Tiered Access

Report depth maps directly to subscription plan levels.

### 4.1 Tier Configuration

| Feature | free/go | plus | pro | ultra |
|---------|---------|------|-----|-------|
| **Metrics count** | 6 core | 15+ | 30+ (full) | 30+ (full) |
| **Charts** | equity, drawdown | all | all | all |
| **AI Summary** | Narrator | Narrator | Narrator | Narrator |
| **Metric annotations** | - | Narrator | Narrator | Narrator |
| **Diagnostics** | - | overfitting, sensitivity | full (MC, regime, anomaly) | full |
| **Strategy comparison** | - | - | Advisor | Advisor |
| **Optimization tips** | - | - | Advisor | Advisor |
| **Chat Q&A** | - | 5 rounds/report | 20 rounds/report | unlimited |
| **Proactive alerts** | - | - | - | yes |
| **Raw data export** | - | - | - | CSV/JSON |
| **Custom templates** | - | - | - | yes |

### 4.2 Tier Filtering Logic

```python
TIER_CONFIG = {
    "free": {
        "metrics": 6,
        "charts": ["equity", "drawdown"],
        "agents": ["narrator"],
        "chat": False,
        "chat_limit": 0,
    },
    "go": {
        "metrics": 6,
        "charts": ["equity", "drawdown"],
        "agents": ["narrator"],
        "chat": False,
        "chat_limit": 0,
    },
    "basic": {
        "metrics": 10,
        "charts": ["equity", "drawdown", "rolling_sharpe"],
        "agents": ["narrator"],
        "chat": False,
        "chat_limit": 0,
    },
    "plus": {
        "metrics": 15,
        "charts": "all",
        "agents": ["narrator", "diagnostician"],
        "chat": True,
        "chat_limit": 5,
        "diagnostics": ["overfitting", "sensitivity"],
    },
    "pro": {
        "metrics": None,  # all
        "charts": "all",
        "agents": "all",
        "chat": True,
        "chat_limit": 20,
        "diagnostics": "all",
        "mc": True,
        "regime": True,
        "compare": True,
    },
    "ultra": {
        "metrics": None,  # all
        "charts": "all",
        "agents": "all",
        "chat": True,
        "chat_limit": None,  # unlimited
        "diagnostics": "all",
        "mc": True,
        "regime": True,
        "compare": True,
        "export": True,
        "alerts": True,
    },
}
```

## 5. Data Model

### 5.1 New Tables

```sql
-- Backtest Report (stores computed report data)
CREATE TABLE backtest_reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    backtest_job_id UUID NOT NULL REFERENCES backtest_jobs(id),
    user_id         UUID NOT NULL REFERENCES users(id),
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
                    -- pending | computing | narrating | ready | failed

    -- Quant Engine results (JSONB)
    metrics             JSONB,        -- all 30+ metrics
    equity_curve        JSONB,        -- daily NAV series
    drawdown_series     JSONB,        -- drawdown series
    monthly_returns     JSONB,        -- monthly return matrix
    trade_details       JSONB,        -- trade-level details

    -- Diagnostic results (JSONB)
    anomalies               JSONB,    -- anomaly detection list
    overfitting_score        FLOAT,    -- 0.0-1.0
    parameter_sensitivity    JSONB,    -- parameter sensitivity matrix
    monte_carlo              JSONB,    -- MC simulation results
    regime_analysis          JSONB,    -- market regime analysis

    -- AI Narrations
    executive_summary    TEXT,          -- Narrator summary
    metric_narrations    JSONB,         -- per-metric AI commentary
    diagnosis_narration  TEXT,          -- Diagnostician output
    advisor_narration    TEXT,          -- Advisor output

    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_report_job UNIQUE (backtest_job_id)
);

-- Chat message history for conversational Q&A
CREATE TABLE report_chat_messages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id   UUID NOT NULL REFERENCES backtest_reports(id),
    role        VARCHAR(10) NOT NULL,  -- user | assistant
    content     TEXT NOT NULL,
    agent_type  VARCHAR(20),           -- narrator | diagnostician | advisor
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Proactive alerts
CREATE TABLE report_alerts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id   UUID NOT NULL REFERENCES backtest_reports(id),
    severity    VARCHAR(10) NOT NULL,  -- warning | danger | info | tip
    title       TEXT NOT NULL,
    content     TEXT NOT NULL,          -- AI-generated alert text
    dismissed   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reports_user ON backtest_reports(user_id);
CREATE INDEX idx_reports_status ON backtest_reports(status);
CREATE INDEX idx_chat_report ON report_chat_messages(report_id);
CREATE INDEX idx_alerts_report ON report_alerts(report_id);
```

## 6. API Design

### 6.1 Report Generation & Retrieval

```
POST   /api/backtests/{job_id}/report
       → Triggers Report Agent (Celery async task)
       → Returns: { report_id, status: "pending" }

GET    /api/reports/{report_id}
       → Gets report data (filtered by user's plan_level)
       → Returns: metrics, chart data, AI narrations (tier-filtered)

GET    /api/reports/{report_id}/status
       → SSE stream: computing → narrating → ready
```

### 6.2 Conversational Q&A

```
POST   /api/reports/{report_id}/chat
       body: { "message": "Why did March perform poorly?" }
       → Routes to appropriate Agent based on question type
       → Checks chat_limit against user's tier
       → Returns: { "reply": "...", "agent_type": "narrator" }

GET    /api/reports/{report_id}/chat/history
       → Returns chat message history for this report
```

### 6.3 Alerts

```
GET    /api/reports/{report_id}/alerts
       → Returns list of proactive alerts (ultra only)

POST   /api/reports/{report_id}/alerts/{alert_id}/dismiss
       → Marks alert as dismissed
```

### 6.4 Export

```
GET    /api/reports/{report_id}/export?format=html|pdf|csv
       → Exports report (ultra only)
```

## 7. Backend Structure

```
backend/app/report_agent/
├── __init__.py
├── orchestrator.py          # Report Orchestrator - main entry point
├── quant_engine.py          # Pure Python computation layer
├── narrator.py              # Narrator Agent (Haiku)
├── diagnostician.py         # Diagnostician Agent (Sonnet)
├── advisor.py               # Advisor Agent (Sonnet/Opus)
├── tier_filter.py           # Filter output by plan_level
├── chat_router.py           # Route chat questions to correct Agent
└── prompts/
    ├── narrator_system.md          # Narrator system prompt
    ├── diagnostician_system.md     # Diagnostician system prompt
    ├── advisor_system.md           # Advisor system prompt
    └── metric_context.md           # Industry benchmark data for context
```

### 7.1 Orchestrator Flow

```python
async def generate_report(backtest_job_id: str, user_id: str) -> BacktestReport:
    job = get_backtest_job(backtest_job_id)
    plan = get_user_plan(user_id)
    tier = TIER_CONFIG[plan]

    report = BacktestReport(
        backtest_job_id=job.id,
        user_id=user_id,
        status="computing",
    )

    # Phase 1: Quant Engine (pure Python, no LLM)
    report.metrics = quant_engine.compute_all_metrics(job.results)
    report.equity_curve = quant_engine.equity_curve(job.results)
    report.drawdown_series = quant_engine.drawdown_series(job.results)
    report.monthly_returns = quant_engine.monthly_returns(job.results)
    report.trade_details = quant_engine.trade_details(job.results)
    report.status = "narrating"

    # Phase 2: Narrator (always runs)
    report.executive_summary = narrator.generate_summary(report.metrics, tier)
    if tier.get("metrics", 0) > 6:
        report.metric_narrations = narrator.annotate_metrics(report.metrics)

    # Phase 3: Diagnostics (plus and above)
    if "diagnostician" in tier.get("agents", []):
        report.anomalies = quant_engine.detect_anomalies(job.results)
        report.overfitting_score = quant_engine.overfitting_check(
            job.results, job.strategy_params
        )
        report.parameter_sensitivity = quant_engine.parameter_sensitivity(
            job.results, job.strategy_params
        )

        if tier.get("mc"):
            report.monte_carlo = quant_engine.monte_carlo_simulation(job.results)
        if tier.get("regime"):
            report.regime_analysis = quant_engine.regime_analysis(
                job.results, job.market_data
            )

        report.diagnosis_narration = diagnostician.generate_diagnosis(
            anomalies=report.anomalies,
            overfitting_score=report.overfitting_score,
            monte_carlo=report.monte_carlo,
            regime=report.regime_analysis,
            tier=tier,
        )

    # Phase 4: Advisor (pro and above)
    if "advisor" in tier.get("agents", []):
        similar = advisor.find_similar_strategies(job.strategy_id)
        suggestions = advisor.generate_suggestions(report)
        alerts = advisor.generate_alerts(report)

        report.advisor_narration = advisor.narrate(similar, suggestions)

        if tier.get("alerts"):
            for alert in alerts:
                db.session.add(ReportAlert(report_id=report.id, **alert))

    report.status = "ready"
    db.session.commit()

    # Notify frontend via SSE
    notify_report_ready(user_id, report.id)

    return report
```

### 7.2 Chat Router Logic

```python
def route_chat_question(message: str, report: BacktestReport) -> str:
    """Route question to appropriate Agent based on content."""
    prompt = f"""
    Classify this user question about a backtest report:
    "{message}"

    Categories:
    - "narrator": Simple metric questions, strategy overview, basic what/when questions
    - "diagnostician": Why something happened, anomaly explanation, risk analysis
    - "advisor": Optimization suggestions, strategy comparison, portfolio recommendations

    Respond with only the category name.
    """

    category = llm_call(prompt, model="haiku")  # Fast classification

    if category == "narrator":
        return narrator.chat(message, report)
    elif category == "diagnostician":
        return diagnostician.chat(message, report)
    elif category == "advisor":
        return advisor.chat(message, report)
    else:
        return narrator.chat(message, report)  # Default fallback
```

## 8. Frontend Components

```
src/views/backtest/
├── BacktestResultView.vue       # Existing — refactor as report container
├── report/
│   ├── ReportHeader.vue         # Strategy name + time range + overall score
│   ├── MetricsPanel.vue         # Metric cards grid (tier-filtered)
│   ├── MetricCard.vue           # Single metric + AI annotation tooltip
│   ├── ChartPanel.vue           # Chart area
│   ├── AISummaryPanel.vue       # AI executive summary
│   ├── DiagnosisPanel.vue       # Deep diagnostics (plus+)
│   ├── ComparisonPanel.vue      # Strategy comparison (pro+)
│   ├── AlertsPanel.vue          # Proactive alerts (ultra)
│   └── ChatPanel.vue            # Conversational Q&A panel
└── components/
    ├── EquityCurveChart.vue     # Equity curve
    ├── DrawdownChart.vue        # Underwater plot
    ├── MonthlyHeatmap.vue       # Monthly returns heatmap
    ├── RollingMetricChart.vue   # Rolling Sharpe/Vol/Beta
    └── ReturnHistogram.vue      # Return distribution
```

## 9. Integration with Existing Backtest Flow

```
Current flow:
  User clicks backtest → Celery task executes → Result stored in DB → Frontend polls

New flow:
  User clicks backtest → Celery task executes → Result stored in DB
    ↓ (auto-trigger via signal)
  → Report Agent Celery task starts
    → Phase 1: Quant Engine computes (status: computing)
    → Phase 2: LLM narrates (status: narrating)
    → Phase 3: Diagnoses (status: narrating, plus+)
    → Report stored in DB (status: ready)
    → SSE notification to frontend
  Frontend receives notification → Renders report → User can chat
```

### 9.1 Trigger Mechanism

In the existing backtest Celery task, after successful completion:

```python
# In backend/app/tasks/backtests.py
@celery_app.task
def run_backtest(job_id):
    # ... existing backtest execution ...

    # After backtest completes successfully:
    if result.success:
        generate_report.delay(job_id, user_id)  # Trigger report generation
```

## 10. Implementation Phases

### Phase 1: Quant Engine + Basic Report (Priority: HIGH)
- Implement `quant_engine.py` with all 30+ metric calculations
- Create `BacktestReport` model and migration
- Build `tier_filter.py` for plan-based filtering
- Frontend: `ReportHeader`, `MetricsPanel`, `MetricCard`, chart components
- API: report generation + retrieval endpoints

### Phase 2: AI Narration + Chat (Priority: HIGH)
- Implement `narrator.py` with system prompts
- Build `ChatPanel.vue` frontend component
- API: chat endpoint with rate limiting per tier
- Chat history persistence

### Phase 3: Deep Diagnostics (Priority: MEDIUM)
- Implement `diagnostician.py`
- Anomaly detection, overfitting check, parameter sensitivity
- Monte Carlo simulation engine
- Regime analysis engine
- Frontend: `DiagnosisPanel.vue`

### Phase 4: Comparison & Recommendations (Priority: MEDIUM)
- Implement `advisor.py`
- Strategy similarity matching
- Optimization suggestion generation
- Proactive alert system
- Frontend: `ComparisonPanel.vue`, `AlertsPanel.vue`

### Phase 5: Export & Polish (Priority: LOW)
- HTML/PDF report export
- CSV/JSON raw data export (ultra)
- Report template customization (ultra)
- Performance optimization for large datasets

## 11. Dependencies

### 11.1 New Python Packages

| Package | Purpose |
|---------|---------|
| `quantstats` | Metrics computation reference, tearsheet generation |
| `numpy` | Array operations for Monte Carlo, regime analysis |
| `scipy` | Statistical functions, distribution fitting |

### 11.2 LLM API

- Claude API (Anthropic) or OpenAI API for narration
- Model selection: Haiku for Narrator, Sonnet for Diagnostician/Advisor
- Estimated token usage: ~2K input + ~1K output per report (Narrator only)
- ~5K input + ~2K output per report with full diagnostics

### 11.3 Infrastructure

- Redis for SSE notification channels
- Celery worker for async report generation
- PostgreSQL JSONB for flexible report data storage

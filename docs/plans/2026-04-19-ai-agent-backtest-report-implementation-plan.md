# AI Agent Backtest Report Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a tier-aware AI backtest report system on top of the existing `BacktestJob` pipeline without breaking the current synchronous debug report flow or the existing report viewer route.

**Architecture:** Keep `BacktestJob` as the execution and ownership source of truth, then add a separate `BacktestReport` domain that is generated asynchronously after a completed job. Reuse the current metric/equity/trade artifacts where possible, extract shared computation into `backend/app/report_agent/quant_engine.py`, expose the new report domain through dedicated `/api/reports/*` endpoints, and refactor the existing frontend report page into a container that can render both legacy fields and new tiered AI modules.

**Tech Stack:** Flask, SQLAlchemy, Alembic migrations, Celery, Redis, pytest, Vue 3, Pinia, TypeScript, Vitest, SSE patterned after the existing simulation stream implementation.

---

## Scope Decisions

- Do not delete or repurpose `BacktestJob.result_summary` or the existing `/api/v1/backtest/<job_id>/report` endpoint in Phase 1.
- Keep `/api/backtests/latest` as the synchronous debug endpoint.
- Use a new `backtest_reports` table instead of overloading `backtest_jobs`.
- Auto-trigger report generation after successful backtest completion, but also expose a manual regeneration endpoint for retries and future admin repair flows.
- Reuse the existing plan level system from `backend/app/quota.py` (`free`, `go`, `plus`, `pro`, `ultra`) and treat `basic` only as a backward-compatibility alias if it still appears in old data.
- Reuse the existing SSE implementation style from `backend/app/blueprints/simulation.py` instead of inventing a second streaming pattern.

## Non-Goals

- No replacement of the strategy execution sandbox.
- No new charting library.
- No full report PDF redesign in the first backend integration task.
- No attempt to make AI calls mandatory for the free tier.

## Target File Map

**Backend new files**
- `backend/app/report_agent/__init__.py`
- `backend/app/report_agent/orchestrator.py`
- `backend/app/report_agent/quant_engine.py`
- `backend/app/report_agent/tier_filter.py`
- `backend/app/report_agent/chat_router.py`
- `backend/app/report_agent/narrator.py`
- `backend/app/report_agent/diagnostician.py`
- `backend/app/report_agent/advisor.py`
- `backend/app/report_agent/prompts/narrator_system.md`
- `backend/app/report_agent/prompts/diagnostician_system.md`
- `backend/app/report_agent/prompts/advisor_system.md`
- `backend/app/report_agent/prompts/metric_context.md`
- `backend/app/tasks/report_generation.py`
- `backend/app/blueprints/reports.py`
- `backend/tests/test_report_agent.py`

**Backend modified files**
- `backend/app/models.py`
- `backend/app/celery_app.py`
- `backend/app/tasks/backtests.py`
- `backend/app/blueprints/backtests.py`
- `backend/app/services/metrics.py`
- `backend/app/__init__.py`
- `backend/migrations/versions/<new_revision>_add_backtest_reports.py`

**Frontend new files**
- `frontend/src/api/reports.ts`
- `frontend/src/api/reports.test.ts`
- `frontend/src/views/backtest/report/ReportHeader.vue`
- `frontend/src/views/backtest/report/MetricsPanel.vue`
- `frontend/src/views/backtest/report/MetricCard.vue`
- `frontend/src/views/backtest/report/AISummaryPanel.vue`
- `frontend/src/views/backtest/report/DiagnosisPanel.vue`
- `frontend/src/views/backtest/report/ComparisonPanel.vue`
- `frontend/src/views/backtest/report/AlertsPanel.vue`
- `frontend/src/views/backtest/report/ChatPanel.vue`
- `frontend/src/views/backtest/report/ChartPanel.vue`

**Frontend modified files**
- `frontend/src/types/Backtest.ts`
- `frontend/src/api/backtests.ts`
- `frontend/src/stores/backtests.ts`
- `frontend/src/stores/backtests.test.ts`
- `frontend/src/api/backtests.test.ts`
- `frontend/src/views/BacktestResultView.vue`
- `frontend/src/views/BacktestResultView.test.ts`

---

### Task 1: Add Report Persistence and ORM Layer

**Files:**
- Create: `backend/tests/test_report_agent.py`
- Modify: `backend/app/models.py`
- Create: `backend/migrations/versions/<new_revision>_add_backtest_reports.py`

**Step 1: Write the failing persistence test**

Create `backend/tests/test_report_agent.py` with a first test proving a completed job can own exactly one async report row:

```python
def test_backtest_report_row_belongs_to_completed_job(app):
    from app.extensions import db
    from app.models import BacktestJob, BacktestReport, BacktestJobStatus, User

    with app.app_context():
        user = User(phone="13800138901", nickname="ReportOwner")
        db.session.add(user)
        db.session.flush()
        job = BacktestJob(user_id=user.id, status=BacktestJobStatus.COMPLETED.value, params={"symbol": "BTCUSDT"})
        db.session.add(job)
        db.session.flush()
        report = BacktestReport(backtest_job_id=job.id, user_id=user.id, status="pending")
        db.session.add(report)
        db.session.commit()

        stored = BacktestReport.query.filter_by(backtest_job_id=job.id).one()
        assert stored.user_id == user.id
        assert stored.status == "pending"
```

**Step 2: Run test to verify it fails**

Run:

```bash
uv run --project E:\QYQuant\backend pytest E:\QYQuant\backend\tests\test_report_agent.py -q
```

Expected:

- FAIL with `ImportError` or missing `BacktestReport`.

**Step 3: Add the minimal ORM models**

Modify `backend/app/models.py` to add:

- `BacktestReport`
- `ReportChatMessage`
- `ReportAlert`

Use the existing SQLAlchemy style already present in the file. Include:

- `uq_report_job` uniqueness on `backtest_job_id`
- `status` string field with `pending | computing | narrating | ready | failed`
- JSON columns for `metrics`, `equity_curve`, `drawdown_series`, `monthly_returns`, `trade_details`, `anomalies`, `parameter_sensitivity`, `monte_carlo`, `regime_analysis`, `metric_narrations`
- text fields for `executive_summary`, `diagnosis_narration`, `advisor_narration`
- created/updated timestamps

**Step 4: Add the migration**

Create `backend/migrations/versions/<new_revision>_add_backtest_reports.py` to create the three tables and indexes. Follow the style used in existing migrations under `backend/migrations/versions/`.

**Step 5: Run the persistence test again**

Run:

```bash
uv run --project E:\QYQuant\backend pytest E:\QYQuant\backend\tests\test_report_agent.py -q
```

Expected:

- PASS for the new persistence test.

**Step 6: Commit**

```bash
git add backend/app/models.py backend/migrations/versions backend/tests/test_report_agent.py
git commit -m "feat: add async backtest report persistence models"
```

---

### Task 2: Extract Quant Engine and Tier Filtering

**Files:**
- Create: `backend/app/report_agent/__init__.py`
- Create: `backend/app/report_agent/quant_engine.py`
- Create: `backend/app/report_agent/tier_filter.py`
- Modify: `backend/app/services/metrics.py`
- Modify: `backend/tests/test_backtests.py`
- Modify: `backend/tests/test_report_agent.py`

**Step 1: Write failing quant-engine tests**

Add tests in `backend/tests/test_report_agent.py` for:

- `compute_all_metrics()` returns the current core summary keys plus new report-specific structures.
- `build_report_payload()` preserves `equity_curve`, `drawdown_series`, `monthly_returns`, and normalized `trade_details`.
- `filter_report_for_tier(report, "free")` returns only the core subset.

Example:

```python
def test_filter_report_for_free_tier_hides_ai_and_diagnostics():
    from app.report_agent.tier_filter import filter_report_for_tier

    report = {
        "metrics": {"totalReturn": 10, "sharpeRatio": 1.2, "omegaRatio": 1.7},
        "executive_summary": "summary",
        "metric_narrations": {"sharpeRatio": "good"},
        "anomalies": [{"title": "outlier"}],
        "advisor_narration": "upgrade"
    }

    filtered = filter_report_for_tier(report, "free")
    assert "advisor_narration" not in filtered
    assert "anomalies" not in filtered
    assert "executive_summary" in filtered
```

**Step 2: Run tests to verify failure**

Run:

```bash
uv run --project E:\QYQuant\backend pytest E:\QYQuant\backend\tests\test_report_agent.py -q
```

Expected:

- FAIL because `app.report_agent` modules do not exist yet.

**Step 3: Move shared computation into `quant_engine.py`**

Create `backend/app/report_agent/quant_engine.py` and move reusable logic out of `backend/app/services/metrics.py`:

- bar normalization
- trade normalization
- equity curve construction
- drawdown calculation
- monthly return matrix construction
- existing summary metrics

Keep `backend/app/services/metrics.py` as a compatibility wrapper:

```python
from ..report_agent.quant_engine import build_legacy_backtest_report

def build_backtest_report(bars, trades, initial_capital=INITIAL_CAPITAL):
    return build_legacy_backtest_report(bars, trades, initial_capital=initial_capital)
```

**Step 4: Implement plan-tier filtering**

Create `backend/app/report_agent/tier_filter.py` with:

- a single `TIER_CONFIG` map aligned to `quota.py`
- helper functions:
  - `normalize_report_plan_level(plan_level)`
  - `allowed_metric_keys(plan_level)`
  - `filter_report_for_tier(report_dict, plan_level)`

The first implementation should be strict and explicit. Do not use implicit deep-copy magic; instead build the response shape field by field.

**Step 5: Run focused tests**

Run:

```bash
uv run --project E:\QYQuant\backend pytest E:\QYQuant\backend\tests\test_report_agent.py E:\QYQuant\backend\tests\test_backtests.py -k "report or filter" -q
```

Expected:

- PASS for the new quant engine and filter tests.
- Existing legacy report tests remain green through the wrapper.

**Step 6: Commit**

```bash
git add backend/app/report_agent backend/app/services/metrics.py backend/tests/test_backtests.py backend/tests/test_report_agent.py
git commit -m "feat: extract quant report engine and tier filter"
```

---

### Task 3: Wire Async Report Generation into Celery

**Files:**
- Create: `backend/app/tasks/report_generation.py`
- Create: `backend/app/report_agent/orchestrator.py`
- Modify: `backend/app/celery_app.py`
- Modify: `backend/app/tasks/backtests.py`
- Modify: `backend/app/__init__.py`
- Modify: `backend/tests/test_backtests.py`
- Modify: `backend/tests/test_report_agent.py`

**Step 1: Write the failing task-integration tests**

Add tests proving:

- successful `_run_job(job_id)` queues report generation
- report generation creates or updates the matching `BacktestReport`
- repeat generation regenerates the same row instead of creating duplicates

Example:

```python
def test_completed_backtest_queues_report_generation(monkeypatch, app):
    queued = {}

    def _fake_delay(job_id, user_id):
        queued["job_id"] = job_id
        queued["user_id"] = user_id

    monkeypatch.setattr("app.tasks.report_generation.generate_backtest_report.delay", _fake_delay)
```

**Step 2: Run tests to verify failure**

Run:

```bash
uv run --project E:\QYQuant\backend pytest E:\QYQuant\backend\tests\test_backtests.py E:\QYQuant\backend\tests\test_report_agent.py -k "queues_report_generation or regenerate" -q
```

Expected:

- FAIL because the report task and orchestrator do not exist.

**Step 3: Implement the report task and orchestrator**

Create `backend/app/tasks/report_generation.py` with:

- `@celery_app.task(bind=True, name="app.tasks.report_generation.generate_backtest_report")`
- eager-safe app-context behavior matching `backend/app/tasks/backtests.py`

Create `backend/app/report_agent/orchestrator.py` with:

- `generate_report(backtest_job_id, user_id, force=False)`
- load job and fail fast if job is not completed
- upsert `BacktestReport`
- set status transitions: `pending -> computing -> narrating -> ready` or `failed`
- reuse quant engine output first, then call narrator hooks only when the tier requires them

**Step 4: Hook the task into the existing backtest worker**

Modify `backend/app/tasks/backtests.py` to queue the report task after a successful commit:

```python
job.status = BacktestJobStatus.COMPLETED.value
job.result_storage_key = storage_key
job.result_summary = report["result_summary"]
job.completed_at = now_utc()
db.session.commit()

if job.user_id:
    generate_backtest_report.delay(job.id, job.user_id)
```

Import the task lazily inside the function to avoid circular imports if needed.

**Step 5: Register the new task and blueprint package**

Modify `backend/app/celery_app.py` imports/task routes so `app.tasks.report_generation` loads with the worker. Modify `backend/app/__init__.py` to register the future reports blueprint stub if the app currently centralizes blueprint registration there.

**Step 6: Run focused task tests**

Run:

```bash
uv run --project E:\QYQuant\backend pytest E:\QYQuant\backend\tests\test_backtests.py E:\QYQuant\backend\tests\test_report_agent.py -k "report_generation or worker_generates_report" -q
```

Expected:

- PASS for queuing and upsert behavior.
- Existing backtest worker tests still pass.

**Step 7: Commit**

```bash
git add backend/app/tasks/report_generation.py backend/app/report_agent/orchestrator.py backend/app/celery_app.py backend/app/tasks/backtests.py backend/app/__init__.py backend/tests/test_backtests.py backend/tests/test_report_agent.py
git commit -m "feat: wire async ai report generation into backtest worker"
```

---

### Task 4: Add Report Read APIs and Status Streaming

**Files:**
- Create: `backend/app/blueprints/reports.py`
- Modify: `backend/app/blueprints/backtests.py`
- Modify: `backend/app/__init__.py`
- Modify: `backend/tests/test_report_agent.py`
- Review reference: `backend/app/blueprints/simulation.py`

**Step 1: Write failing API tests**

Add tests covering:

- `POST /api/backtests/<job_id>/report` creates/regenerates a report job response
- `GET /api/reports/<report_id>` returns tier-filtered data for owner
- `GET /api/reports/<report_id>/status` returns report status
- `GET /api/reports/<report_id>/status/stream` emits SSE frames using the simulation blueprint pattern

Example:

```python
def test_get_report_returns_tier_filtered_payload(client):
    response = client.get(f"/api/reports/{report_id}", headers=_auth_headers(token))
    assert response.status_code == 200
    assert "metrics" in response.json["data"]
```

**Step 2: Run tests to verify failure**

Run:

```bash
uv run --project E:\QYQuant\backend pytest E:\QYQuant\backend\tests\test_report_agent.py -k "api/reports or status_stream" -q
```

Expected:

- FAIL with 404 routes or missing blueprint.

**Step 3: Implement the new reports blueprint**

Create `backend/app/blueprints/reports.py` with:

- `POST /api/backtests/<job_id>/report`
- `GET /api/reports/<report_id>`
- `GET /api/reports/<report_id>/status`
- `GET /api/reports/<report_id>/status/stream`

Rules:

- owner-only access
- use `filter_report_for_tier()` before returning payload
- status stream can initially poll the DB in a short loop, but the response format must be proper SSE and the implementation style must mirror `simulation.py`

**Step 4: Keep the legacy report route stable**

Do not delete or silently repoint `/api/v1/backtest/<job_id>/report`. Instead, add a compatibility field there if useful:

- `report_id`
- `report_status`

This lets the old page bootstrap the new async domain without breaking existing callers.

**Step 5: Run focused API tests**

Run:

```bash
uv run --project E:\QYQuant\backend pytest E:\QYQuant\backend\tests\test_report_agent.py -k "reports blueprint or report_status" -q
```

Expected:

- PASS for report create/read/status routes.

**Step 6: Commit**

```bash
git add backend/app/blueprints/reports.py backend/app/blueprints/backtests.py backend/app/__init__.py backend/tests/test_report_agent.py
git commit -m "feat: expose ai backtest report read and status apis"
```

---

### Task 5: Add Frontend Report Contracts and Bootstrap Logic

**Files:**
- Create: `frontend/src/api/reports.ts`
- Create: `frontend/src/api/reports.test.ts`
- Modify: `frontend/src/types/Backtest.ts`
- Modify: `frontend/src/api/backtests.ts`
- Modify: `frontend/src/api/backtests.test.ts`
- Modify: `frontend/src/stores/backtests.ts`
- Modify: `frontend/src/stores/backtests.test.ts`

**Step 1: Write failing frontend contract tests**

Add tests for:

- `fetchReport(reportId)`
- `fetchReportStatus(reportId)`
- `openReportStatusStream(reportId)`
- backtest store bootstrapping from legacy report payload that includes `report_id`

Example:

```ts
it('fetches ai report by report id', async () => {
  await reports.fetchReport('report-1')
  expect(requestMock).toHaveBeenCalledWith({ method: 'get', url: '/api/reports/report-1' })
})
```

**Step 2: Run tests to verify failure**

Run:

```bash
npm test -- src/api/backtests.test.ts src/stores/backtests.test.ts src/api/reports.test.ts
```

Expected:

- FAIL because the new API module and types do not exist.

**Step 3: Add report-specific frontend types**

Extend `frontend/src/types/Backtest.ts` with:

- `BacktestAiReportResponse`
- `BacktestAiReportStatusResponse`
- `BacktestAiChatMessage`
- `BacktestAiAlert`

Do not remove the existing `BacktestReportResponse`; keep it for the legacy endpoint.

**Step 4: Implement API and store wiring**

Create `frontend/src/api/reports.ts` and modify the store so:

- `loadReport(jobId)` still loads legacy bootstrap data from `/v1/backtest/<job_id>/report`
- if `report_id` exists, the store also fetches `/api/reports/<report_id>`
- the store tracks both `legacyReport` and `aiReport` or an equivalent clear split

Use the existing `simulation.ts` `EventSource` pattern if you choose to wire SSE immediately.

**Step 5: Run focused frontend tests**

Run:

```bash
npm test -- src/api/backtests.test.ts src/stores/backtests.test.ts src/api/reports.test.ts
```

Expected:

- PASS for new HTTP contracts and store branching behavior.

**Step 6: Commit**

```bash
git add frontend/src/types/Backtest.ts frontend/src/api/backtests.ts frontend/src/api/backtests.test.ts frontend/src/api/reports.ts frontend/src/api/reports.test.ts frontend/src/stores/backtests.ts frontend/src/stores/backtests.test.ts
git commit -m "feat: add frontend ai report contracts and bootstrap flow"
```

---

### Task 6: Refactor the Report View into Tiered Modules

**Files:**
- Create: `frontend/src/views/backtest/report/ReportHeader.vue`
- Create: `frontend/src/views/backtest/report/MetricsPanel.vue`
- Create: `frontend/src/views/backtest/report/MetricCard.vue`
- Create: `frontend/src/views/backtest/report/ChartPanel.vue`
- Create: `frontend/src/views/backtest/report/AISummaryPanel.vue`
- Create: `frontend/src/views/backtest/report/DiagnosisPanel.vue`
- Create: `frontend/src/views/backtest/report/ComparisonPanel.vue`
- Create: `frontend/src/views/backtest/report/AlertsPanel.vue`
- Modify: `frontend/src/views/BacktestResultView.vue`
- Modify: `frontend/src/views/BacktestResultView.test.ts`

**Step 1: Write failing view tests**

Add tests proving:

- the page still renders legacy metrics and charts when no AI report exists
- the page renders AI summary when `aiReport.executive_summary` exists
- diagnostics, comparison, and alerts panels render only when the tier payload includes them

Example:

```ts
it('renders ai summary when ai report is loaded', async () => {
  // mount with store state containing aiReport.executive_summary
  expect(screen.getByText(/executive summary/i)).toBeTruthy()
})
```

**Step 2: Run tests to verify failure**

Run:

```bash
npm test -- src/views/BacktestResultView.test.ts
```

Expected:

- FAIL because the page is still monolithic and does not know about `aiReport`.

**Step 3: Split the page into report modules**

Refactor `BacktestResultView.vue` so it becomes a container that:

- keeps the existing export root and legacy fallback behavior
- renders `ReportHeader` and `MetricsPanel` from normalized data
- renders `AISummaryPanel`, `DiagnosisPanel`, `ComparisonPanel`, and `AlertsPanel` only when the loaded tier allows them

Do not attempt a full visual redesign here. Preserve the current house style and route behavior.

**Step 4: Keep charts backward-compatible**

`ChartPanel.vue` should wrap the existing chart components:

- `EquityCurveChart.vue`
- `DrawdownChart.vue`
- future `MonthlyHeatmap.vue`
- future `RollingMetricChart.vue`
- future `ReturnHistogram.vue`

If the deeper charts are not implemented yet, render stable placeholders and keep tests honest about it.

**Step 5: Run focused UI tests**

Run:

```bash
npm test -- src/views/BacktestResultView.test.ts
```

Expected:

- PASS for legacy compatibility and AI-module rendering branches.

**Step 6: Commit**

```bash
git add frontend/src/views/BacktestResultView.vue frontend/src/views/BacktestResultView.test.ts frontend/src/views/backtest/report
git commit -m "feat: refactor backtest result page into tiered report modules"
```

---

### Task 7: Add Narrator, Chat, Diagnostics, Advisor, and Final Verification

**Files:**
- Create: `backend/app/report_agent/narrator.py`
- Create: `backend/app/report_agent/diagnostician.py`
- Create: `backend/app/report_agent/advisor.py`
- Create: `backend/app/report_agent/chat_router.py`
- Create: `backend/app/report_agent/prompts/narrator_system.md`
- Create: `backend/app/report_agent/prompts/diagnostician_system.md`
- Create: `backend/app/report_agent/prompts/advisor_system.md`
- Create: `backend/app/report_agent/prompts/metric_context.md`
- Modify: `backend/app/report_agent/orchestrator.py`
- Modify: `backend/app/blueprints/reports.py`
- Modify: `backend/tests/test_report_agent.py`
- Create: `frontend/src/views/backtest/report/ChatPanel.vue`
- Modify: `frontend/src/views/BacktestResultView.vue`
- Modify: `frontend/src/views/BacktestResultView.test.ts`

**Step 1: Write failing backend tests for narration and chat routing**

Add tests for:

- narrator-only summary generation for `free/go`
- diagnostician generation for `plus/pro/ultra`
- advisor generation and alert creation for `pro/ultra`
- chat messages persisted to `report_chat_messages`

Stub the LLM boundary. Do not call real APIs in tests.

Example:

```python
def test_generate_report_uses_narrator_stub(monkeypatch):
    monkeypatch.setattr("app.report_agent.narrator.generate_summary", lambda metrics, tier: "stub summary")
```

**Step 2: Run tests to verify failure**

Run:

```bash
uv run --project E:\QYQuant\backend pytest E:\QYQuant\backend\tests\test_report_agent.py -k "narrator or chat or alerts" -q
```

Expected:

- FAIL because the agent modules and chat endpoints do not exist.

**Step 3: Implement the agent boundaries**

Create simple service modules with pure functions:

- `narrator.generate_summary(metrics, tier)`
- `narrator.annotate_metrics(metrics)`
- `diagnostician.generate_diagnosis(...)`
- `advisor.generate_suggestions(report)`
- `advisor.generate_alerts(report)`
- `chat_router.route_chat_question(message, report)`

The first implementation should support a deterministic stub mode via configuration or monkeypatching so tests stay local and repeatable.

**Step 4: Add chat endpoints**

Extend `backend/app/blueprints/reports.py` with:

- `POST /api/reports/<report_id>/chat`
- `GET /api/reports/<report_id>/chat/history`
- `GET /api/reports/<report_id>/alerts`
- `POST /api/reports/<report_id>/alerts/<alert_id>/dismiss`

Enforce plan-level chat limits with the existing `quota.py` plan semantics rather than inventing a second subscription source.

**Step 5: Add the frontend chat panel**

Create `frontend/src/views/backtest/report/ChatPanel.vue` and wire it into `BacktestResultView.vue`.

Minimum first pass:

- input box
- send button
- message list
- loading state
- tier-gated disabled state when chat is unavailable

**Step 6: Run focused backend and frontend tests**

Run:

```bash
uv run --project E:\QYQuant\backend pytest E:\QYQuant\backend\tests\test_report_agent.py -q
```

Run:

```bash
npm test -- src/views/BacktestResultView.test.ts src/api/reports.test.ts src/stores/backtests.test.ts
```

Expected:

- PASS for narration stubs, chat persistence, alerts, and frontend rendering.

**Step 7: Run final regression checks**

Run:

```bash
uv run --project E:\QYQuant\backend pytest E:\QYQuant\backend\tests\test_backtests.py E:\QYQuant\backend\tests\test_report_agent.py -q
```

Run:

```bash
npm test -- src/api/backtests.test.ts src/api/reports.test.ts src/stores/backtests.test.ts src/views/BacktestResultView.test.ts
```

Run:

```bash
npm run build
```

Expected:

- PASS on targeted backend regression tests
- PASS on targeted frontend regression tests
- successful frontend production build

**Step 8: Commit**

```bash
git add backend/app/report_agent backend/app/blueprints/reports.py backend/tests/test_report_agent.py frontend/src/views/backtest/report/ChatPanel.vue frontend/src/views/BacktestResultView.vue frontend/src/views/BacktestResultView.test.ts
git commit -m "feat: add ai narration chat and diagnostics to backtest reports"
```

---

## Review Checklist

Before execution review these code areas in order:

1. `backend/app/models.py`
2. `backend/app/tasks/backtests.py`
3. `backend/app/report_agent/orchestrator.py`
4. `backend/app/blueprints/reports.py`
5. `backend/app/report_agent/tier_filter.py`
6. `frontend/src/stores/backtests.ts`
7. `frontend/src/views/BacktestResultView.vue`

## Risks to Watch

- Circular imports between Celery task modules and report orchestration.
- Tier config drift between `backend/app/quota.py` and `backend/app/report_agent/tier_filter.py`.
- Breaking the existing `/v1/backtest/<job_id>/report` payload expected by `BacktestResultView.vue`.
- Trying to make real LLM calls inside unit tests.
- Overbuilding Monte Carlo/regime/anomaly math before the base async domain is stable.

## Suggested Execution Order

1. Task 1
2. Task 2
3. Task 3
4. Task 4
5. Task 5
6. Task 6
7. Task 7

Plan complete and saved to `docs/plans/2026-04-19-ai-agent-backtest-report-implementation-plan.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?

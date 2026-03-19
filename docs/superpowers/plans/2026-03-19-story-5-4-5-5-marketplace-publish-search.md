# Story 5.4 + 5.5 Marketplace Publish And Search Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement marketplace strategy publishing with review-state tracking and add PostgreSQL-backed search and filter capabilities to the marketplace list.

**Architecture:** Extend the existing `marketplace.py` blueprint instead of introducing a second marketplace module, but split responsibilities internally into publish, publish-status, and list/search helpers. Keep publish metadata on the existing `strategies` table, add a minimal `notifications` foundation plus audit logging, and make marketplace search a PostgreSQL-only path using `zhparser`, `tsvector`, and SQL-level filter composition.

**Tech Stack:** Flask, SQLAlchemy, Alembic, PostgreSQL 15+, zhparser, Flask-JWT-Extended, Vue 3, TypeScript, Pinia, Vitest, Vue Test Utils, uv, npm

---

## File Structure

### Backend files

- Modify: `backend/app/blueprints/marketplace.py`
  Responsibility: own marketplace list/search, publish submission, publish-status lookup, and shared marketplace query helpers.
- Modify: `backend/app/models.py`
  Responsibility: add `Notification` model and PostgreSQL-aware search columns on `Strategy`.
- Create: `backend/app/services/notifications.py`
  Responsibility: one focused helper for `create_notification(user_id, type, title, content)`.
- Modify: `backend/tests/conftest.py`
  Responsibility: allow PostgreSQL-backed test runs for marketplace search without breaking existing SQLite-oriented tests.
- Modify: `backend/tests/test_marketplace.py`
  Responsibility: cover publish flow, publish-status, notification/audit side effects, Chinese full-text search, and combined filters.
- Create: `backend/migrations/versions/<revision>_marketplace_notifications.py`
  Responsibility: create the `notifications` table and unread index.
- Create: `backend/migrations/versions/<revision>_marketplace_search_zhparser.py`
  Responsibility: create `zhparser`/`chinese` search config, search columns, and indexes.

### Frontend files

- Modify: `frontend/src/api/strategies.ts`
  Responsibility: add publish/publish-status API calls and extend marketplace list params.
- Modify: `frontend/src/api/strategies.test.ts`
  Responsibility: verify new API contract and query serialization.
- Modify: `frontend/src/types/Strategy.ts`
  Responsibility: add publish-status, publish-payload, and filter types.
- Modify: `frontend/src/stores/useMarketplaceStore.ts`
  Responsibility: own marketplace filters, debounced refetch hooks, publish actions, and publish-status state.
- Modify: `frontend/src/stores/useMarketplaceStore.test.ts`
  Responsibility: verify filter state, API param forwarding, publish actions, and reset behavior.
- Create: `frontend/src/components/strategy/StrategyPublishFlow.vue`
  Responsibility: own the 3-step publish drawer UI.
- Create: `frontend/src/components/strategy/StrategyPublishFlow.test.ts`
  Responsibility: verify step transitions, validation, and submit gating.
- Modify: `frontend/src/views/StrategyLibraryView.vue`
  Responsibility: render publish entry buttons, status badges, and host the publish flow component.
- Modify: `frontend/src/views/StrategyLibraryView.test.ts`
  Responsibility: verify row-level publish state and publish refresh behavior.
- Modify: `frontend/src/views/Marketplace.vue`
  Responsibility: render search input, chips, result count, and empty-state actions.
- Modify: `frontend/src/views/Marketplace.test.ts`
  Responsibility: verify debounce-triggered search, chip combinations, empty state, and clear-filters flow.

### Verification references

- Reference: `README.md`
  Responsibility: existing backend/frontend verification commands.
- Reference: `docker-compose.yml`
  Responsibility: PostgreSQL service details for local search verification.
- Reference: `docs/superpowers/specs/2026-03-19-story-5-4-5-5-marketplace-publish-search-design.md`
  Responsibility: approved functional source of truth for implementation.

## Chunk 1: PostgreSQL Test Harness And Notification Foundation

### Task 1: Prepare backend tests to run marketplace search against PostgreSQL

**Files:**
- Modify: `backend/tests/conftest.py`
- Modify: `backend/tests/test_marketplace.py`
- Reference: `docker-compose.yml`
- Reference: `backend/migrations/env.py`

- [ ] **Step 1: Add a failing PostgreSQL-aware fixture path in `backend/tests/conftest.py`**

```python
POSTGRES_TEST_URL = os.getenv("QYQUANT_TEST_DATABASE_URL")

if POSTGRES_TEST_URL:
    monkeypatch.setenv("DATABASE_URL", POSTGRES_TEST_URL)
else:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
```

- [ ] **Step 2: Run `uv run pytest backend/tests/test_marketplace.py::test_marketplace_list_returns_only_public_approved_strategies -v` from `E:\QYQuant`**
Expected: PASS still works with SQLite fallback for existing tests.

- [ ] **Step 3: Add a failing PostgreSQL-only smoke test guard in `backend/tests/test_marketplace.py`**

```python
def test_marketplace_search_suite_requires_postgres(app):
    assert app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgresql")
```

- [ ] **Step 4: Run `set QYQUANT_TEST_DATABASE_URL=postgresql://postgres:1@localhost:5432/qyquant && uv run pytest backend/tests/test_marketplace.py::test_marketplace_search_suite_requires_postgres -v`**
Expected: FAIL now if the local PostgreSQL test database is not wired through correctly.

### Task 2: Add the notifications persistence layer with TDD

**Files:**
- Modify: `backend/app/models.py`
- Create: `backend/app/services/notifications.py`
- Modify: `backend/tests/test_marketplace.py`
- Create: `backend/migrations/versions/<revision>_marketplace_notifications.py`

- [ ] **Step 1: Write a failing notification model side-effect test**

```python
def test_publish_creates_review_submitted_notification(client, app):
    response = client.post("/api/v1/marketplace/strategies", json=payload, headers=_auth_headers(token))
    assert response.status_code == 200
    with app.app_context():
        notification = Notification.query.filter_by(user_id=user_id, type="strategy_review_submitted").first()
        assert notification is not None
```

- [ ] **Step 2: Run `uv run pytest backend/tests/test_marketplace.py::test_publish_creates_review_submitted_notification -v`**
Expected: FAIL because `Notification` and the helper do not exist yet.

- [ ] **Step 3: Add `Notification` to `backend/app/models.py` and create `backend/app/services/notifications.py`**

```python
def create_notification(user_id, type, title, content=None):
    notification = Notification(user_id=user_id, type=type, title=title, content=content)
    db.session.add(notification)
    return notification
```

- [ ] **Step 4: Create the notifications Alembic migration with unread partial index**

```python
op.create_table(
    "notifications",
    sa.Column("id", sa.String(), primary_key=True),
    sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
    ...
)
```

- [ ] **Step 5: Run `uv run pytest backend/tests/test_marketplace.py::test_publish_creates_review_submitted_notification -v`**
Expected: still FAIL, but now only because the publish endpoint does not call the helper yet.

- [ ] **Step 6: Commit the foundation**

```bash
git add backend/tests/conftest.py backend/tests/test_marketplace.py backend/app/models.py backend/app/services/notifications.py backend/migrations/versions/
git commit -m "测试与基础设施：补充策略广场发布所需的 PostgreSQL 测试入口和通知模型" -m "调整 backend 测试夹具以支持通过环境变量切换到 PostgreSQL，用于后续 zhparser 全文检索与 JSON 指标筛选测试；保持现有 SQLite 测试路径不受影响。" -m "新增 notifications 模型、创建通知辅助函数和对应 migration，为策略提交审核通知打通持久化基础。"
```

## Chunk 2: Publish API, Review Status, And Audit Logging

### Task 3: Add failing backend tests for publish submission rules

**Files:**
- Modify: `backend/tests/test_marketplace.py`
- Reference: `backend/app/blueprints/marketplace.py`
- Reference: `backend/app/models.py`

- [ ] **Step 1: Write a failing happy-path publish test**

```python
def test_publish_owned_strategy_sets_pending_without_making_public(client, app):
    response = client.post("/api/v1/marketplace/strategies", json=payload, headers=_auth_headers(token))
    assert response.status_code == 200
    assert response.json["data"] == {"strategy_id": strategy_id, "review_status": "pending"}
```

- [ ] **Step 2: Run `uv run pytest backend/tests/test_marketplace.py::test_publish_owned_strategy_sets_pending_without_making_public -v`**
Expected: FAIL because the endpoint does not exist.

- [ ] **Step 3: Write failing permission and validation tests**

```python
def test_publish_rejects_non_owner_with_403(...): ...
def test_publish_rejects_strategy_without_completed_backtest(...): ...
def test_publish_rejects_missing_required_metrics(...): ...
```

- [ ] **Step 4: Run `uv run pytest backend/tests/test_marketplace.py -k "publish_rejects or publish_owned_strategy" -v`**
Expected: FAIL on missing route or missing validations.

### Task 4: Implement publish submission and publish-status lookup

**Files:**
- Modify: `backend/app/blueprints/marketplace.py`
- Modify: `backend/app/models.py`
- Modify: `backend/tests/test_marketplace.py`
- Reference: `backend/app/services/notifications.py`

- [ ] **Step 1: Add request parsing and validation helpers in `marketplace.py`**

```python
def _validate_publish_payload(payload):
    ...
    required_metric_keys = {"sharpe_ratio", "max_drawdown", "total_return"}
```

- [ ] **Step 2: Add `POST /api/v1/marketplace/strategies` with owner check and successful-backtest check**

```python
@bp.post("/strategies")
@jwt_required()
def publish_marketplace_strategy():
    ...
```

- [ ] **Step 3: Update the owned strategy record without setting `is_public = True`**

```python
strategy.review_status = "pending"
strategy.title = payload["title"]
strategy.description = payload["description"]
```

- [ ] **Step 4: Create the notification and audit-log side effects in the same transaction**

```python
create_notification(...)
db.session.add(AuditLog(...))
```

- [ ] **Step 5: Add `GET /api/v1/marketplace/strategies/<strategy_id>/publish-status`**

```python
@bp.get("/strategies/<strategy_id>/publish-status")
@jwt_required()
def get_marketplace_publish_status(strategy_id):
    ...
```

- [ ] **Step 6: Run `uv run pytest backend/tests/test_marketplace.py -k "publish or publish_status" -v`**
Expected: PASS for happy path, ownership, missing-backtest, and notification side effects.

### Task 5: Pin down audit logging and rejected-resubmission behavior

**Files:**
- Modify: `backend/tests/test_marketplace.py`
- Modify: `backend/app/blueprints/marketplace.py`

- [ ] **Step 1: Write a failing audit-log assertion**

```python
def test_publish_writes_marketplace_audit_log(client, app):
    ...
    assert audit.action == "marketplace_strategy_submitted"
```

- [ ] **Step 2: Write a failing rejected-resubmission test**

```python
def test_publish_allows_rejected_strategy_resubmission(client, app):
    ...
    assert refreshed.review_status == "pending"
```

- [ ] **Step 3: Run `uv run pytest backend/tests/test_marketplace.py -k "audit_log or rejected_strategy_resubmission" -v`**
Expected: FAIL until audit details and resubmission logic are explicit.

- [ ] **Step 4: Implement any minimal missing logic in `marketplace.py`**

```python
if strategy.review_status in {"pending", "approved"}:
    return error_response(...)
```

- [ ] **Step 5: Run `uv run pytest backend/tests/test_marketplace.py -k "publish or publish_status or audit_log" -v`**
Expected: PASS.

- [ ] **Step 6: Commit the publish slice**

```bash
git add backend/tests/test_marketplace.py backend/app/blueprints/marketplace.py backend/app/models.py backend/app/services/notifications.py
git commit -m "功能：实现策略发布审核提交流程与发布状态查询" -m "在 marketplace 蓝图中新增策略发布接口和发布状态接口，补齐所有者校验、成功回测校验、展示字段校验，以及 pending 和 rejected 场景下的状态流转。" -m "发布成功后同步写入站内通知和 audit_logs，明确禁止提交时直接公开策略，为后续管理员审核流程保留边界。"
```

## Chunk 3: PostgreSQL zhparser Search And Combined Filters

### Task 6: Add failing PostgreSQL search and filter tests

**Files:**
- Modify: `backend/tests/test_marketplace.py`
- Modify: `backend/tests/conftest.py`
- Reference: `backend/app/models.py`

- [ ] **Step 1: Write a failing Chinese full-text search test**

```python
def test_marketplace_search_matches_chinese_title_and_description(client, app):
    response = client.get("/api/v1/marketplace/strategies?q=均线")
    assert [item["id"] for item in response.json["data"]] == ["ma-strategy"]
```

- [ ] **Step 2: Run `set QYQUANT_TEST_DATABASE_URL=postgresql://postgres:1@localhost:5432/qyquant && uv run pytest backend/tests/test_marketplace.py::test_marketplace_search_matches_chinese_title_and_description -v`**
Expected: FAIL because search columns/configuration do not exist.

- [ ] **Step 3: Write failing filter tests for category, verified, annual return, and drawdown**

```python
def test_marketplace_filters_combine_with_search(client, app): ...
def test_marketplace_filter_drawdown_uses_absolute_threshold_rule(client, app): ...
```

- [ ] **Step 4: Run `uv run pytest backend/tests/test_marketplace.py -k "search_matches_chinese or filters_combine or drawdown_uses_absolute" -v` with `QYQUANT_TEST_DATABASE_URL` set**
Expected: FAIL until PostgreSQL search infrastructure and filter SQL are implemented.

### Task 7: Implement the PostgreSQL search migration and model fields

**Files:**
- Modify: `backend/app/models.py`
- Create: `backend/migrations/versions/<revision>_marketplace_search_zhparser.py`
- Modify: `backend/tests/test_marketplace.py`

- [ ] **Step 1: Add PostgreSQL-specific `title_tsv` and `description_tsv` fields to `Strategy`**

```python
from sqlalchemy.dialects.postgresql import TSVECTOR

title_tsv = db.Column(TSVECTOR, nullable=True)
description_tsv = db.Column(TSVECTOR, nullable=True)
```

- [ ] **Step 2: Create the migration that installs `zhparser`, defines `chinese`, adds columns, and adds GIN indexes**

```python
op.execute("CREATE EXTENSION IF NOT EXISTS zhparser")
op.execute("CREATE TEXT SEARCH CONFIGURATION chinese (PARSER = zhparser)")
```

- [ ] **Step 3: Include update hooks in migration SQL so insert/update keeps vectors synchronized**

```sql
CREATE FUNCTION strategies_tsv_trigger() RETURNS trigger AS $$
...
$$ LANGUAGE plpgsql;
```

- [ ] **Step 4: Run the focused PostgreSQL test command again**
Expected: still FAIL, but now on list query behavior rather than missing database objects.

### Task 8: Extend `GET /api/v1/marketplace/strategies` for ranking and combined filters

**Files:**
- Modify: `backend/app/blueprints/marketplace.py`
- Modify: `backend/tests/test_marketplace.py`

- [ ] **Step 1: Add query-param parsing helpers for `q`, `category`, `tags`, `verified`, `max_drawdown_lte`, and `annual_return_gte`**

```python
search_term = (request.args.get("q") or "").strip()
category = (request.args.get("category") or "").strip()
```

- [ ] **Step 2: Implement PostgreSQL search predicate and ranking**

```python
query_expr = db.func.plainto_tsquery("chinese", search_term)
query = query.filter(
    db.or_(Strategy.title_tsv.op("@@")(query_expr), Strategy.description_tsv.op("@@")(query_expr))
)
```

- [ ] **Step 3: Implement SQL-level JSON metric filters and tag overlap filtering**

```python
query = query.filter(db.cast(Strategy.display_metrics["annual_return"].astext, db.Float) >= annual_return_gte)
```

- [ ] **Step 4: Encode the drawdown threshold rule as absolute-value semantics and document it in the code comment**

```python
query = query.filter(db.func.abs(db.cast(Strategy.display_metrics["max_drawdown"].astext, db.Float)) <= max_drawdown_lte)
```

- [ ] **Step 5: Preserve current featured and onboarding shortcuts**
- [ ] **Step 6: Run `set QYQUANT_TEST_DATABASE_URL=postgresql://postgres:1@localhost:5432/qyquant && uv run pytest backend/tests/test_marketplace.py -k "search or filter or drawdown or pagination" -v`**
Expected: PASS for PostgreSQL search and filter coverage.

- [ ] **Step 7: Commit the search slice**

```bash
git add backend/tests/conftest.py backend/tests/test_marketplace.py backend/app/models.py backend/app/blueprints/marketplace.py backend/migrations/versions/
git commit -m "功能：实现策略广场 PostgreSQL 中文搜索与条件筛选" -m "为 strategies 增加 zhparser 驱动的 title_tsv 和 description_tsv 检索字段及 GIN 索引，扩展 marketplace 列表接口以支持中文全文检索、分类筛选、标签筛选、平台验证和指标组合筛选。" -m "明确最大回撤阈值按绝对值语义计算，并通过 PostgreSQL 专用测试覆盖搜索排序、组合查询和分页元数据。"
```

## Chunk 4: Frontend Publish Flow, Search UI, And Verification

### Task 9: Add failing frontend API and store tests

**Files:**
- Modify: `frontend/src/api/strategies.test.ts`
- Modify: `frontend/src/stores/useMarketplaceStore.test.ts`
- Modify: `frontend/src/types/Strategy.ts`

- [ ] **Step 1: Write a failing API test for publish submission**

```ts
it('calls marketplace publish endpoint', async () => {
  await strategies.publishMarketplaceStrategy({ strategyId: 'strategy-1', ...payload })
  expect(requestSpy).toHaveBeenCalledWith(expect.objectContaining({ method: 'post', url: '/v1/marketplace/strategies' }))
})
```

- [ ] **Step 2: Run `npm test -- src/api/strategies.test.ts` from `E:\QYQuant\frontend`**
Expected: FAIL because the publish API helper does not exist.

- [ ] **Step 3: Write failing store tests for filters and publish actions**

```ts
it('forwards filters to fetchStrategies', async () => { ... })
it('publishes a strategy and refreshes status', async () => { ... })
```

- [ ] **Step 4: Run `npm test -- src/stores/useMarketplaceStore.test.ts`**
Expected: FAIL until filters and publish actions are implemented.

### Task 10: Build the publish drawer component and strategy-library integration

**Files:**
- Create: `frontend/src/components/strategy/StrategyPublishFlow.vue`
- Create: `frontend/src/components/strategy/StrategyPublishFlow.test.ts`
- Modify: `frontend/src/views/StrategyLibraryView.vue`
- Modify: `frontend/src/views/StrategyLibraryView.test.ts`
- Modify: `frontend/src/api/strategies.ts`
- Modify: `frontend/src/stores/useMarketplaceStore.ts`

- [ ] **Step 1: Write a failing component test for the 3-step publish flow**

```ts
it('blocks submit until the agreement checkbox is checked', async () => {
  const wrapper = mount(StrategyPublishFlow, { props: ... })
  expect(wrapper.get('[data-test="publish-confirm"]').attributes('disabled')).toBeDefined()
})
```

- [ ] **Step 2: Run `npm test -- src/components/strategy/StrategyPublishFlow.test.ts`**
Expected: FAIL because the component does not exist.

- [ ] **Step 3: Implement the publish API helpers and marketplace store actions**

```ts
export async function publishMarketplaceStrategy(payload: MarketplacePublishPayload): Promise<MarketplacePublishResult> { ... }
export async function fetchMarketplacePublishStatus(strategyId: string): Promise<MarketplacePublishStatus> { ... }
```

- [ ] **Step 4: Implement `StrategyPublishFlow.vue` with step state, form validation, and success screen**
- [ ] **Step 5: Add publish buttons, disabled states, and status badges to `StrategyLibraryView.vue`**
- [ ] **Step 6: Refresh row state after a successful publish**
- [ ] **Step 7: Run `npm test -- src/components/strategy/StrategyPublishFlow.test.ts src/views/StrategyLibraryView.test.ts src/stores/useMarketplaceStore.test.ts src/api/strategies.test.ts`**
Expected: PASS for publish UI and store behavior.

### Task 11: Build marketplace search and chip filters

**Files:**
- Modify: `frontend/src/views/Marketplace.vue`
- Modify: `frontend/src/views/Marketplace.test.ts`
- Modify: `frontend/src/stores/useMarketplaceStore.ts`
- Modify: `frontend/src/stores/useMarketplaceStore.test.ts`
- Modify: `frontend/src/api/strategies.ts`
- Modify: `frontend/src/types/Strategy.ts`

- [ ] **Step 1: Write failing view tests for debounced search and chip combinations**

```ts
it('debounces search input before refetching', async () => { ... })
it('clears other filters when the all chip is selected', async () => { ... })
```

- [ ] **Step 2: Run `npm test -- src/views/Marketplace.test.ts`**
Expected: FAIL until the UI and store support filters.

- [ ] **Step 3: Extend marketplace filter types and state**

```ts
filters: { q: '', category: null, tags: [], verified: false, maxDrawdownLte: null, annualReturnGte: null }
```

- [ ] **Step 4: Teach `fetchStrategies()` to serialize filters into request params and reset to page 1 on filter changes**
- [ ] **Step 5: Implement the search input, chips, result count, and clear-filters empty state in `Marketplace.vue`**
- [ ] **Step 6: Run `npm test -- src/views/Marketplace.test.ts src/stores/useMarketplaceStore.test.ts src/api/strategies.test.ts`**
Expected: PASS for search/filter UI wiring and request params.

### Task 12: Run end-to-end verification for the story slice

**Files:**
- Test: `backend/tests/test_marketplace.py`
- Test: `frontend/src/api/strategies.test.ts`
- Test: `frontend/src/stores/useMarketplaceStore.test.ts`
- Test: `frontend/src/components/strategy/StrategyPublishFlow.test.ts`
- Test: `frontend/src/views/StrategyLibraryView.test.ts`
- Test: `frontend/src/views/Marketplace.test.ts`

- [ ] **Step 1: Start PostgreSQL and Redis if needed with `docker compose up -d postgres redis` from `E:\QYQuant`**
- [ ] **Step 2: Run `set QYQUANT_TEST_DATABASE_URL=postgresql://postgres:1@localhost:5432/qyquant && uv run pytest backend/tests/test_marketplace.py -v`**
Expected: PASS for publish, notifications, audit logs, search, and filters.

- [ ] **Step 3: Run `npm test -- src/api/strategies.test.ts src/stores/useMarketplaceStore.test.ts src/components/strategy/StrategyPublishFlow.test.ts src/views/StrategyLibraryView.test.ts src/views/Marketplace.test.ts` from `E:\QYQuant\frontend`**
Expected: PASS.

- [ ] **Step 4: Run `npm run build` from `E:\QYQuant\frontend`**
Expected: successful production build.

- [ ] **Step 5: Re-check acceptance criteria against both stories**
- [ ] **Step 6: Remove or ignore temporary `.superpowers/brainstorm/` artifacts before final delivery if they are still present**

- [ ] **Step 7: Commit the frontend and final verification slice**

```bash
git add frontend/src/api/strategies.ts frontend/src/api/strategies.test.ts frontend/src/types/Strategy.ts frontend/src/stores/useMarketplaceStore.ts frontend/src/stores/useMarketplaceStore.test.ts frontend/src/components/strategy/StrategyPublishFlow.vue frontend/src/components/strategy/StrategyPublishFlow.test.ts frontend/src/views/StrategyLibraryView.vue frontend/src/views/StrategyLibraryView.test.ts frontend/src/views/Marketplace.vue frontend/src/views/Marketplace.test.ts
git commit -m "功能：完成策略发布前端流程与策略广场搜索筛选界面" -m "新增策略库行内发布入口、三步发布抽屉、审核状态展示以及 marketplace store 的发布和筛选状态管理，前端请求参数与后端新接口保持一致。" -m "在 Marketplace 页面补充搜索框、筛选 Chip、结果数量和空状态清除操作，并通过 Vitest 覆盖 debounced 搜索、组合筛选和发布交互流程。"
```

## Local Plan Review

- [ ] Check the plan against `docs/superpowers/specs/2026-03-19-story-5-4-5-5-marketplace-publish-search-design.md` and confirm every approved requirement maps to a task.
- [ ] Confirm no plan step depends on SQLite fallback for search behavior.
- [ ] Confirm commit boundaries match meaningful vertical slices:
  - test harness + notification foundation
  - publish backend
  - PostgreSQL search backend
  - frontend publish/search integration

Plan complete and saved to `docs/superpowers/plans/2026-03-19-story-5-4-5-5-marketplace-publish-search.md`. Ready to execute?

# Architecture

**Analysis Date:** 2026-04-27

## Pattern Overview

**Overall:** Monolithic full-stack application with async task workers

**Key Characteristics:**
- Flask backend following a layered Blueprint-Service-Model architecture
- Vue 3 SPA frontend with Pinia state management
- Celery async task queues for backtesting, report generation, bot execution, and moderation
- PostgreSQL primary database with Redis for caching, session/auth store, and Celery broker
- Shared Python workspace with `qysp` strategy protocol SDK as an internal package
- REST API with JSON envelope pattern (`{ code, message, data }`)

## Layers

**Frontend (SPA):**
- Purpose: User interface for quantitative strategy management, backtesting, trading bots, marketplace, and community
- Location: `frontend/src/`
- Contains: Vue 3 SFC components, Pinia stores, API client modules, router, i18n
- Depends on: Backend REST API via Axios HTTP client
- Used by: End users (browser)

**Backend API Layer (Blueprints):**
- Purpose: HTTP request handling, authentication, input validation, response formatting
- Location: `backend/app/blueprints/`
- Contains: Flask-Smorest Blueprint modules (one per domain: `auth.py`, `backtests.py`, `bots.py`, etc.)
- Depends on: Services layer, Models, Extensions (db, jwt, mail, celery)
- Used by: Frontend via `/api/v1/*` endpoints

**Services Layer:**
- Purpose: Business logic orchestration, domain operations
- Location: `backend/app/services/`
- Contains: Domain-specific service modules (`bots.py`, `market_data.py`, `strategy_import.py`, `moderation.py`, `ai_strategy_generation.py`, etc.)
- Depends on: Models, external integrations, strategy runtime
- Used by: Blueprints and Celery tasks

**Domain Engines:**
- Purpose: Core algorithmic engines for backtesting, strategy execution, report generation
- Location: `backend/app/backtest/`, `backend/app/strategy_runtime/`, `backend/app/report_agent/`
- Contains: `engine.py` (backtest calculation), `executor.py` (strategy sandbox execution), `loader.py` (strategy package loading), report agent with LLM orchestration
- Depends on: Strategy runtime sandbox, data providers, LLM integrations
- Used by: Services and Celery tasks

**Data Access (Models):**
- Purpose: Database schema definition, ORM mappings
- Location: `backend/app/models.py` (single file, ~815 lines)
- Contains: SQLAlchemy model classes (User, Strategy, BacktestJob, BotInstance, Post, Order, etc.)
- Depends on: Flask-SQLAlchemy (`extensions.py`)
- Used by: All backend layers

**Async Task Layer (Celery):**
- Purpose: Long-running and scheduled background jobs
- Location: `backend/app/tasks/`
- Contains: `backtests.py`, `report_generation.py`, `managed_bot_tasks.py`, `simulation_tasks.py`, `moderation_tasks.py`, `notification_tasks.py`, `quota_tasks.py`, `review_tasks.py`
- Depends on: Services, models, Celery configuration
- Used by: Blueprint endpoints dispatch tasks; Celery Beat triggers scheduled tasks

**Integrations Layer:**
- Purpose: External service adapters (brokers, market data, LLM)
- Location: `backend/app/integrations/`
- Contains: Broker adapters (`brokers/longport.py`, `brokers/gmtrade.py`, `brokers/xtquant.py`), LLM adapter (`llm/openai_compatible.py`), market data adapters (`market_data/akshare_like.py`, `market_data/joinquant.py`), provider registry (`registry.py`)
- Depends on: External SDKs, models
- Used by: Services layer and task layer

## Data Flow

**Backtest Execution Flow:**

1. Frontend submits backtest request to `POST /api/backtests` (`backend/app/blueprints/backtests.py`)
2. Blueprint validates quota (`backend/app/quota.py`), creates `BacktestJob` record
3. Celery task `run_backtest_task` dispatched to `backtest` queue (`backend/app/tasks/backtests.py`)
4. Task loads strategy package via `strategy_runtime/loader.py`, resolves data source via `providers/`
5. Strategy code executed in sandbox (`backend/app/services/sandbox.py`) via `strategy_runtime/executor.py`
6. Backtest engine calculates metrics (`backend/app/backtest/engine.py`)
7. Results stored as JSON, `BacktestJob` updated to `completed`
8. Report generation task creates `BacktestReport` with LLM narrations (`backend/app/report_agent/`)

**Strategy Execution Flow:**

1. User uploads strategy file or uses AI generation (`backend/app/services/ai_strategy_generation.py`)
2. Import analysis runs (`backend/app/services/strategy_import_analysis.py`) producing a `StrategyImportDraft`
3. User confirms import (`backend/app/services/strategy_import_confirm.py`), code is encrypted (`backend/app/utils/crypto.py`)
4. Strategy runtime loads encrypted package, validates manifest, executes in sandbox
5. Source code is never exposed to consumers (sealed import mode)

**Bot Trading Flow:**

1. User creates bot linking strategy + broker integration (`backend/app/blueprints/bots.py`)
2. Celery Beat runs `run_managed_bots_dry_run` every 5 minutes (`backend/app/tasks/managed_bot_tasks.py`)
3. Bot execution service (`backend/app/services/managed_bot_execution.py`) runs strategy in sandbox
4. Signals produce orders submitted to broker via integration adapter
5. Equity snapshots recorded daily (`BotEquitySnapshot`)

**Authentication Flow:**

1. Login via phone+SMS code, email+password, or OAuth (WeChat/GitHub/Google)
2. `flask-jwt-extended` issues access token (60min) + refresh token (30 days)
3. Refresh token stored as HTTP-only cookie; access token in `localStorage` on frontend
4. Frontend Axios interceptor auto-refreshes on 401 (`frontend/src/api/http.ts`)
5. Token blacklist stored in Redis (`backend/app/utils/redis_client.py`)

**State Management:**
- Frontend: Pinia stores per domain (`user.ts`, `backtests.ts`, `bots.ts`, `strategies.ts`, `forum.ts`, `useMarketplaceStore.ts`, `useAdminStore.ts`, `useCommunityStore.ts`, `useSimulationStore.ts`, etc.)
- Backend: Stateless request handling, state in PostgreSQL + Redis
- Celery: Task state tracked via `AsyncResult` + database records

## Key Abstractions

**Strategy Package (QYSP):**
- Purpose: Defines the protocol for writing quantitative strategies
- Examples: `packages/qysp/src/qysp/context.py`, `packages/qysp/src/qysp/validator.py`, `packages/qysp/src/qysp/schema/qysp.schema.json`
- Pattern: SDK with `StrategyContext`, `ParameterAccessor`, validation, and indicator helpers. Strategies export a callable entrypoint.

**Integration Provider Registry:**
- Purpose: Plugin-style registration of broker, market data, and LLM providers
- Examples: `backend/app/integrations/registry.py`, `backend/app/models.py` (`IntegrationProvider`, `UserIntegration`)
- Pattern: Dataclass-based provider definitions with capabilities and config schemas. Runtime adapter selection by provider key.

**API Response Envelope:**
- Purpose: Consistent JSON response structure across all endpoints
- Examples: `backend/app/utils/response.py` (`ok()`, `error_response()`), `frontend/src/api/http.ts` (`ApiEnvelope<T>`)
- Pattern: `{ code: number, message: string, data: T, meta?: object }` for success; `{ error: { code, message } }` for errors

**Celery Task Router:**
- Purpose: Route tasks to specialized queues
- Examples: `backend/app/celery_app.py`
- Pattern: `backtest` queue for backtests/reports, `trading` queue for bot execution, `notification` queue for notifications, `review` queue for strategy reviews, `simulation` queue for simulation tasks

## Entry Points

**Flask Application:**
- Location: `backend/app/__init__.py`
- Triggers: Gunicorn in production (`gunicorn`), Flask dev server in development
- Responsibilities: App factory (`create_app()`), registers all blueprints, initializes extensions, configures JWT callbacks

**Celery Worker:**
- Location: `backend/app/celery_app.py`
- Triggers: `celery -A app.celery_app worker` command
- Responsibilities: Task queue processing with 10 concurrent workers

**Celery Beat:**
- Location: `backend/app/celery_app.py` (`beat_schedule`)
- Triggers: `celery -A app.celery_app beat`
- Responsibilities: Scheduled tasks (daily simulation, managed bot dry runs every 5 min, monthly quota reset, health checks)

**Frontend Entry:**
- Location: `frontend/src/main.ts`
- Triggers: Vite dev server or built static files served by nginx
- Responsibilities: Creates Vue app, installs Pinia, Router, i18n, applies theme/market style, starts MSW mock worker in dev mode

## Error Handling

**Strategy:** Centralized error handlers + domain-specific error types

**Patterns:**
- Global HTTP error handler in `backend/app/errors.py` catches `HTTPException` and generic `Exception`
- `StrategyRuntimeError` in `backend/app/strategy_runtime/errors.py` for sandbox execution failures
- Error parser service (`backend/app/services/error_parser.py`) translates sandbox errors to user-facing messages
- Frontend `normalizeError.ts` (`frontend/src/api/normalizeError.ts`) standardizes Axios errors
- API envelope error format: `{ error: { code: string, message: string } }`

## Cross-Cutting Concerns

**Logging:** Python standard `logging` module; Flask request logging; Celery task logging

**Validation:**
- Backend: Marshmallow schemas (`backend/app/schemas.py`) for request/response serialization
- Frontend: TypeScript type definitions (`frontend/src/types/`)
- Strategy: JSON Schema validation (`packages/qysp/src/qysp/schema/qysp.schema.json`)

**Authentication:** JWT (flask-jwt-extended) with access/refresh token rotation, Redis token blacklist, OAuth2 for third-party login (WeChat, GitHub, Google)

**Authorization:** Role-based (`role` field on User: `user`, `admin`), plan-level-based quota enforcement (`backend/app/quota.py`), admin routes guarded by `requiresAdmin` route meta

**Content Moderation:** Sensitive word matching (`backend/app/models.py` `SensitiveWord`, `UserModerationRecord`) with automated Celery task moderation (`backend/app/tasks/moderation_tasks.py`)

**Internationalization:** Vue-i18n with Chinese (`zh.ts`) and English (`en.ts`) locales (`frontend/src/i18n/messages/`)

**Encryption:** Strategy source code encrypted at rest using Fernet symmetric encryption (`backend/app/utils/crypto.py`)

---

*Architecture analysis: 2026-04-27*

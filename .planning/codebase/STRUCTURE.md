# Codebase Structure

**Analysis Date:** 2026-04-27

## Directory Layout

```
QYQuant/
├── backend/                 # Flask API server + Celery workers
│   ├── app/                 # Application source code
│   │   ├── backtest/        # Backtest engine (metrics calculation)
│   │   ├── blueprints/      # Flask-Smorest API route handlers
│   │   ├── integrations/    # External service adapters
│   │   │   ├── brokers/     # Broker integrations (LongPort, GMTrade, XtQuant)
│   │   │   ├── llm/         # LLM integration (OpenAI-compatible)
│   │   │   └── market_data/ # Market data adapters (AkShare, JoinQuant)
│   │   ├── marketdata/      # Market data clients (Binance, gold, Sina)
│   │   ├── providers/       # Data provider abstraction (AkShare, JoinQuant)
│   │   ├── report_agent/    # AI-powered report generation (multi-agent)
│   │   ├── services/        # Business logic services
│   │   ├── strategy_runtime/# Strategy loading, sandbox execution, parameters
│   │   ├── tasks/           # Celery async task definitions
│   │   └── utils/           # Shared utilities (auth, crypto, redis, storage)
│   ├── migrations/          # Flask-Migrate (Alembic) database migrations
│   ├── scripts/             # Operational scripts
│   ├── storage/             # Local file storage (strategy packages, results)
│   ├── strategy_store/      # Strategy storage helpers
│   └── tests/               # Backend test suite
├── frontend/                # Vue 3 SPA
│   ├── public/              # Static assets (design preview HTML)
│   ├── scripts/             # Build/utility scripts
│   ├── server/              # SSR or preview server (if any)
│   ├── src/                 # Application source
│   │   ├── api/             # API client modules (per domain)
│   │   ├── components/      # Vue SFC components
│   │   │   ├── auth/        # Login/register components
│   │   │   ├── backtest/    # Backtest result display components
│   │   │   ├── bots/        # Trading bot management
│   │   │   ├── community/   # Community/social features
│   │   │   ├── help/        # Help panel
│   │   │   ├── notification/# Notification components
│   │   │   ├── onboarding/  # Guided onboarding flow
│   │   │   ├── simulation/  # Simulation bot components
│   │   │   ├── strategy/    # Strategy management components
│   │   │   ├── ui/          # Reusable UI primitives (QCheckbox, QDropdown, etc.)
│   │   │   └── user/        # User profile components
│   │   ├── composables/     # Vue composition functions
│   │   ├── data/            # Static data files
│   │   ├── i18n/            # Internationalization setup and messages
│   │   ├── lib/             # Shared utility functions
│   │   ├── mocks/           # MSW (Mock Service Worker) handlers
│   │   ├── router/          # Vue Router configuration
│   │   ├── stores/          # Pinia state stores
│   │   ├── styles/          # Global CSS, theme, design tokens
│   │   ├── types/           # TypeScript type definitions
│   │   └── views/           # Page-level Vue components
│   │       ├── admin/       # Admin panel views
│   │       └── backtest/    # Backtest report views
│   └── tests/               # Frontend test setup
├── packages/
│   └── qysp/                # QYQuant Strategy Protocol SDK
│       ├── src/qysp/
│       │   ├── cli/         # CLI tool (`qys` command)
│       │   ├── schema/      # JSON Schema for strategy validation
│       │   ├── templates/   # Strategy templates (mean_reversion, momentum, etc.)
│       │   └── utils/       # SDK utilities
│       └── tests/           # QYSP test suite
├── docs/                    # Design documents and plans
│   ├── plans/               # Historical implementation plans
│   ├── qyir/                # QYIR documentation
│   ├── strategy-format/     # Strategy format examples and schema
│   └── superpowers/         # Superpowers documentation
├── static/                  # Shared static assets
└── openspec/                # OpenAPI specification files
```

## Directory Purposes

**`backend/app/blueprints/`:**
- Purpose: HTTP API route definitions, one file per domain
- Contains: Flask-Smorest Blueprint classes with route handlers
- Key files: `auth.py`, `backtests.py`, `bots.py`, `strategies.py`, `marketplace.py`, `community.py`, `forum.py`, `admin.py`, `payments.py`, `integrations.py`

**`backend/app/services/`:**
- Purpose: Core business logic, orchestrates models and external services
- Contains: Service modules (25 files)
- Key files: `sandbox.py`, `bots.py`, `market_data.py`, `strategy_import.py`, `ai_strategy_generation.py`, `managed_bot_execution.py`, `moderation.py`, `backtest_report_export.py`

**`backend/app/strategy_runtime/`:**
- Purpose: Strategy package loading, parameter validation, sandbox execution
- Key files: `executor.py`, `loader.py`, `sandbox.py`, `manifest.py`, `params.py`

**`backend/app/report_agent/`:**
- Purpose: AI-powered backtest report generation with multi-agent orchestration
- Key files: `orchestrator.py`, `narrator.py`, `diagnostician.py`, `advisor.py`, `llm_client.py`, `chat_router.py`

**`frontend/src/views/`:**
- Purpose: Page-level components mapped to routes
- Key files: `DashboardView.vue`, `BacktestResultView.vue`, `StrategyEditorView.vue`, `Marketplace.vue`, `BotsView.vue`, `LoginView.vue`

**`frontend/src/stores/`:**
- Purpose: Pinia state management stores
- Key files: `user.ts`, `backtests.ts`, `bots.ts`, `strategies.ts`, `forum.ts`, `useMarketplaceStore.ts`, `useAdminStore.ts`

**`frontend/src/api/`:**
- Purpose: API client modules, one per domain
- Key files: `http.ts` (shared Axios client with retry + auth refresh), `auth.ts`, `backtests.ts`, `strategies.ts`, `bots.ts`, `admin.ts`

## Key File Locations

**Entry Points:**
- `backend/app/__init__.py`: Flask app factory (`create_app()`)
- `backend/app/celery_app.py`: Celery configuration and beat schedule
- `frontend/src/main.ts`: Vue app bootstrap

**Configuration:**
- `backend/app/config.py`: Environment-based config (DevConfig, TestConfig, ProdConfig)
- `backend/app/extensions.py`: Flask extension singletons (db, jwt, cors, mail, migrate, api)
- `frontend/vite.config.js`: Vite build config with API proxy to `:59999`
- `pyproject.toml`: Python workspace definition (uv workspace)
- `docker-compose.yml`: Full stack Docker orchestration (postgres, redis, backend, celery-worker, celery-beat, frontend)

**Core Logic:**
- `backend/app/models.py`: All SQLAlchemy models (30+ models, single file)
- `backend/app/schemas.py`: Marshmallow serialization schemas
- `backend/app/backtest/engine.py`: Backtest metrics calculation engine
- `backend/app/strategy_runtime/executor.py`: Strategy sandbox execution orchestrator
- `backend/app/strategy_runtime/loader.py`: Strategy package loading and access control
- `backend/app/quota.py`: Plan-level quota limits and enforcement
- `backend/app/utils/response.py`: API response helpers (`ok()`, `error_response()`)
- `frontend/src/api/http.ts`: Axios client with retry and auth refresh

**Testing:**
- `backend/tests/conftest.py`: Test fixtures
- `backend/tests/test_*.py`: Per-domain test files (40+ test files)
- `frontend/src/views/*.test.ts`: Co-located view tests
- `frontend/src/stores/*.test.ts`: Co-located store tests
- `packages/qysp/tests/`: QYSP SDK tests

## Naming Conventions

**Files:**
- Backend Python: `snake_case.py` (e.g., `strategy_import.py`, `managed_bot_execution.py`)
- Frontend Vue: `PascalCase.vue` for components (e.g., `BacktestResultView.vue`, `StrategyCard.vue`)
- Frontend TypeScript: `camelCase.ts` for utilities/stores (e.g., `backtestComputed.ts`, `useAdminStore.ts`)
- Frontend tests: `PascalCase.test.ts` co-located with source (e.g., `BacktestsView.test.ts`)
- Database migrations: `YYYYMMDD_description.py` (e.g., `20260419a1b2_add_backtest_reports.py`)

**Directories:**
- Backend modules: `snake_case/` with `__init__.py` (e.g., `strategy_runtime/`, `report_agent/`)
- Frontend components: `kebab-case/` (e.g., `onboarding/`, `notification/`)
- Frontend stores: `camelCase.ts` files with `use` prefix for composable-style stores (e.g., `useMarketplaceStore.ts`)

## Where to Add New Code

**New API Endpoint:**
1. Add route handler in `backend/app/blueprints/<domain>.py` (create new file if new domain)
2. Register blueprint in `backend/app/__init__.py`
3. Add Marshmallow schema in `backend/app/schemas.py`
4. Add SQLAlchemy model in `backend/app/models.py` if new table needed
5. Add migration: `flask db migrate -m "description"`
6. Add API client function in `frontend/src/api/<domain>.ts`
7. Add Pinia store methods in `frontend/src/stores/<domain>.ts`

**New Frontend Page:**
1. Create view component in `frontend/src/views/<Name>View.vue`
2. Add route definition in `frontend/src/router/index.ts`
3. Add navigation entry in `frontend/src/components/SideNav.vue` if needed
4. Add i18n keys in `frontend/src/i18n/messages/zh.ts` and `en.ts`

**New Celery Task:**
1. Define task in `backend/app/tasks/<domain>_tasks.py` (or create new file)
2. Register import in `backend/app/celery_app.py` `imports` tuple
3. Add queue routing in `celery_app.py` `task_routes` if specialized queue needed
4. Add beat schedule entry if periodic

**New Integration (Broker/Provider):**
1. Add adapter in `backend/app/integrations/brokers/` (or `market_data/`, `llm/`)
2. Register provider in `backend/app/integrations/registry.py` `_PROVIDERS` dict
3. Add migration for `IntegrationProvider` seed data if needed

**New Strategy Template:**
1. Add template in `packages/qysp/src/qysp/templates/<category>/`
2. Update template registry if applicable

**New Shared UI Component:**
1. Create component in `frontend/src/components/ui/<Name>.vue`
2. Export from `frontend/src/components/ui/index.ts`

**New Service:**
1. Create `backend/app/services/<domain>.py`
2. Import and use from blueprint or task as needed

## Special Directories

**`backend/migrations/versions/`:**
- Purpose: Alembic database migration scripts
- Generated: Yes (by `flask db migrate`)
- Committed: Yes

**`backend/storage/`:**
- Purpose: Local file storage for strategy packages, backtest results
- Generated: Yes (runtime)
- Committed: No (Docker volume)

**`frontend/src/mocks/`:**
- Purpose: MSW (Mock Service Worker) handlers for dev-mode API mocking
- Generated: No
- Committed: Yes

**`frontend/dist/`:**
- Purpose: Production build output
- Generated: Yes (by `vite build`)
- Committed: No

**`docs/plans/`:**
- Purpose: Historical design and implementation plan documents
- Generated: No
- Committed: Yes

**`.env`, `.env.*`:**
- Purpose: Environment configuration and secrets
- Generated: No
- Committed: No (in `.gitignore`)

---

*Structure analysis: 2026-04-27*

# Coding Conventions

**Analysis Date:** 2026-04-27

## Naming Patterns

### Files (Backend - Python)

- **Blueprints:** `lowercase.py` matching domain name -- e.g., `auth.py`, `backtests.py`, `marketplace.py`
- **Services:** `lowercase.py` with `snake_case` -- e.g., `market_data.py`, `strategy_import.py`, `managed_bot_execution.py`
- **Tasks (Celery):** `lowercase.py` with `_tasks` suffix -- e.g., `backtests.py`, `notification_tasks.py`, `simulation_tasks.py`
- **Utilities:** `lowercase.py` -- e.g., `response.py`, `redis_client.py`, `request_id.py`
- **Tests:** `test_` prefix + module name -- e.g., `test_auth.py`, `test_strategies.py`, `test_marketplace.py`

### Files (Frontend - TypeScript/Vue)

- **API modules:** `lowercase.ts` -- e.g., `auth.ts`, `backtests.ts`, `strategies.ts`
- **Views:** `PascalCase.vue` with `View` suffix -- e.g., `DashboardView.vue`, `BacktestsView.vue`, `LoginView.vue`
- **Components:** `PascalCase.vue` -- e.g., `BacktestCard.vue`, `SideNav.vue`, `TopNav.vue`
- **Stores:** `usePascalCaseStore.ts` or `lowercase.ts` -- e.g., `useUserStore.ts`, `useMarketplaceStore.ts`, `strategies.ts`
- **Types:** `PascalCase.ts` -- e.g., `User.ts`, `Strategy.ts`, `Backtest.ts`
- **Tests:** Co-located with source, `.test.ts` suffix -- e.g., `auth.test.ts`, `DashboardView.test.ts`

### Python Classes

- **Models:** `PascalCase` inheriting `db.Model` -- e.g., `User`, `Strategy`, `BacktestJob`
- **Schemas (Marshmallow):** `PascalCase` with `Schema` suffix -- e.g., `UserPrivateSchema`, `StrategySchema`, `BacktestSchema`
- **Service classes:** `PascalCase` with `Service` suffix -- e.g., `MarketDataService`, `SandboxService`
- **Enums:** `PascalCase(str, Enum)` -- e.g., `BacktestJobStatus`
- **Exceptions:** `PascalCase` with `Error` suffix -- e.g., `StrategyImportError`, `AIStrategyGenerationError`

### Functions and Variables

- **Python functions:** `snake_case` -- e.g., `error_response()`, `create_app()`, `run_backtest_task()`
- **Private helpers:** `_` prefix -- e.g., `_hash_token()`, `_mask_email()`, `_build_login_payload()`
- **Python variables:** `snake_case` -- e.g., `plan_level`, `user_id`, `result_summary`
- **TypeScript functions:** `camelCase` -- e.g., `createHttpClient()`, `normalizeError()`, `resolveInitialLocale()`
- **TypeScript variables:** `camelCase` -- e.g., `postMock`, `fetchProfileMock`, `requestId`
- **TypeScript types/interfaces:** `PascalCase` -- e.g., `ApiEnvelope<T>`, `LoginResponse`, `UserProfileResponse`

### Database

- **Table names:** `snake_case` plural -- e.g., `users`, `strategies`, `backtest_jobs`
- **Column names:** `snake_case` -- e.g., `plan_level`, `is_banned`, `created_at`
- **Indexes:** `ix_` prefix + table + column -- e.g., `ix_notifications_user_id`, `ix_strategies_category`
- **Unique constraints:** `uq_` prefix + descriptive name -- e.g., `uq_user_imported_strategy`
- **Check constraints:** `ck_` prefix + descriptive name -- e.g., `ck_strategies_share_mode_free`
- **Foreign keys:** `snake_case_id` pattern -- e.g., `user_id`, `strategy_id`, `owner_id`

## Code Style

### Formatting

- **No project-level formatter config** (no `.prettierrc`, no `ruff.toml`, no `biome.json`)
- `ruff` is listed as a dev dependency in `pyproject.toml` but no configuration file found
- TypeScript files use 2-space indentation (observed in `vite.config.js`)
- Python files use 4-space indentation (standard)

### Linting

- **No ESLint configuration** in frontend (no `.eslintrc` or `eslint.config.*`)
- **No ruff configuration file** (listed as dependency only)
- TypeScript strict mode enabled in `tsconfig.json`: `strict: true`, `noUnusedLocals: true`, `noUnusedParameters: true`

### Key TypeScript Settings (`frontend/tsconfig.json`)

- Target: ES2020
- Module: ESNext
- JSX: preserve (Vue SFC compilation)
- `skipLibCheck: true`
- `isolatedModules: true`
- `noEmit: true`

## Import Organization

### Backend (Python)

```python
# 1. Standard library
import hashlib
import json
import re

# 2. Third-party packages
from flask import request
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

# 3. Local application imports (using relative imports)
from ..extensions import db
from ..models import User, Strategy
from ..schemas import StrategySchema
from ..services.strategy_import import StrategyImportError
from ..utils.response import error_response, ok
```

### Frontend (TypeScript)

```typescript
// 1. Third-party packages
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

// 2. Local imports using @/ alias or relative paths
import { useUserStore } from './user'
import { normalizeError } from './normalizeError'
import type { User } from '../types/User'
```

### Path Aliases (Frontend)

- `@/*` maps to `src/*` (configured in `tsconfig.json`)

## API Response Format

### Success Response

All backend endpoints return responses through `ok()` in `backend/app/utils/response.py`:

```python
{
    "code": 0,
    "message": "ok",
    "data": { ... },
    "request_id": "uuid-string"  # always present
}
```

Optional `meta` field for paginated responses:

```python
{
    "code": 0,
    "message": "ok",
    "data": [...],
    "meta": { "total": 24, "page": 2, "page_size": 20 },
    "request_id": "uuid-string"
}
```

### Error Response

All errors return through `error_response()` in `backend/app/utils/response.py`:

```python
{
    "error": {
        "code": "ERROR_CODE_STRING",
        "message": "Human-readable message",
        "details": null  # optional
    },
    "request_id": "uuid-string"
}
```

HTTP status codes: 400, 401, 403, 404, 409, 422, 500

### Frontend API Envelope Type

Defined in `frontend/src/api/http.ts`:

```typescript
interface ApiEnvelope<T> {
    code: number
    message: string
    data: T
    meta?: Record<string, unknown>
}
```

The HTTP client automatically unwraps `response.data.data` so callers receive just the `T` payload.

## Error Handling

### Backend Patterns

**Blueprint-level validation:** Manual checks at the start of route handlers:

```python
# In backend/app/blueprints/strategies.py
if not name:
    return {"code": 40000, "message": "name_required", "details": None}, 400
```

**Error helper function:** Consistent error responses via `error_response()`:

```python
from ..utils.response import error_response
return error_response("EMAIL_EXISTS", "Email already registered", 409)
```

**Global error handlers:** Registered in `backend/app/errors.py` -- HTTP exceptions get formatted as `{code: int, message: str, details: None}`, unhandled exceptions return `{code: 50000, message: "internal_error"}`.

**Service-level exceptions:** Custom exception classes per domain:

```python
class StrategyImportError(Exception): ...
class AIStrategyGenerationError(Exception): ...
class IntentClassificationError(Exception): ...
```

**Celery task error handling:** Structured try/except with status transitions:

```python
try:
    result = run_backtest(...)
except SoftTimeLimitExceeded:
    job.status = BacktestJobStatus.TIMEOUT.value
    job.error_message = 'soft_time_limit_exceeded'
except StrategyRuntimeError as exc:
    job.status = BacktestJobStatus.FAILED.value
    _store_structured_error(job, raw_error)
except Exception as exc:
    job.status = BacktestJobStatus.FAILED.value
    _store_structured_error(job, str(exc))
```

### Frontend Patterns

**Error normalization:** `normalizeError()` in `frontend/src/api/normalizeError.ts` extracts status, code, and message from Axios errors into a consistent shape `{ status?, code?, message }`.

**Auth error recovery:** The HTTP client (`frontend/src/api/http.ts`) automatically retries with token refresh on 401 responses.

**Store error handling:** Stores use try/catch in async actions:

```typescript
try {
    await this.refreshProfile()
} catch (error) {
    if (getErrorStatus(error) === 401) {
        window.localStorage.removeItem('qyquant-token')
    }
    this.profileLoaded = true
}
```

## Database Model Conventions

- All models live in `backend/app/models.py` (single file, 40K+ lines)
- Primary keys: `db.Column(db.String, primary_key=True, default=gen_id)` -- UUID strings via `uuid.uuid4()`
- Timestamps: `db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)` using timezone-aware UTC
- Some models use millisecond timestamps: `db.Column(db.BigInteger, default=now_ms)`
- Boolean defaults: `nullable=False, default=False`
- Soft deletes: `deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)`
- JSON columns use `JSON().with_variant(JSONB(astext_type=Text()), 'postgresql')` for cross-dialect support
- Indexes defined in `__table_args__` tuples, not inline
- Partial/conditional indexes for PostgreSQL: `postgresql_where=db.text('is_public = true')`

## Configuration Patterns

### Backend Config

- **Environment-based classes** in `backend/app/config.py`: `BaseConfig` -> `DevConfig`, `TestConfig`, `ProdConfig`
- All env vars read through `os.getenv()` with defaults
- `.env` files loaded per `FLASK_ENV`: `.env.development`, `.env.production`, `.env.test`
- Config factory: `get_config(env)` returns instantiated config object

### Frontend Config

- Vite proxy: `/api` proxies to `http://127.0.0.1:59999` during development
- Env vars: `import.meta.env.VITE_API_BASE`
- Token storage: `localStorage` under key `qyquant-token`
- Locale storage: `localStorage` under key `qyquant_locale`

### Celery Configuration

- Tasks in `backend/app/celery_app.py` with queue-based routing
- Queue names: `default`, `backtest`, `notification`, `review`, `trading`, `simulation`
- Beat schedule for periodic tasks (daily simulation, bot dry-runs, monthly quota reset)

## Module Design

### Backend

- **Blueprints** handle HTTP routing and validation. Import services for business logic.
- **Services** contain domain logic. Import models, extensions, and other services.
- **Tasks** are Celery task wrappers. Import services and models.
- **Utils** are shared helpers (response formatting, time, crypto, auth).
- **Extensions** are Flask extension singletons (`db`, `jwt`, `cors`, `mail`, `migrate`, `api`).

### Frontend

- **API layer** (`src/api/`) -- thin functions that call Axios. No business logic.
- **Stores** (`src/stores/`) -- Pinia stores with `state`, `getters`, `actions`.
- **Views** (`src/views/`) -- page-level Vue SFCs.
- **Components** (`src/components/`) -- reusable Vue SFCs.
- **Types** (`src/types/`) -- TypeScript interfaces for API shapes.
- **i18n** (`src/i18n/`) -- message files for `en` and `zh` locales.

## Internationalization

- Backend uses Chinese for user-facing messages: `"未登录"`, `"登录已过期，请重新登录"`
- Frontend supports `en` and `zh` via `vue-i18n`
- Locale detection: localStorage > browser language > default to `en`
- Test setup initializes i18n with `en` locale only

## Request ID Pattern

Every request gets a UUID assigned in `backend/app/utils/request_id.py`:
- Read from `X-Request-Id` header if provided, otherwise generate new UUID
- Stored in `flask.g.request_id`
- Attached to response headers as `X-Request-Id`
- Included in response body as `request_id`

---

*Convention analysis: 2026-04-27*

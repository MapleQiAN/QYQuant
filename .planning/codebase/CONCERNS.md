# Codebase Concerns

**Analysis Date:** 2026-04-27

## Tech Debt

### Legacy app file with open CORS
- Issue: `backend/app_legacy.py` contains `CORS(app)` with no origin restrictions, creating a wide-open CORS policy. This file appears to be a legacy scaffold still present in the codebase.
- Files: `backend/app_legacy.py`
- Impact: If accidentally used in production, any origin can make cross-origin requests. Confusing to have two app factories.
- Fix approach: Remove `app_legacy.py` if no longer needed, or clearly mark it as deprecated and gate it behind a check that prevents production use.

### Hardcoded database credentials in test utility
- Issue: `backend/test_db_connection.py` has hardcoded `'password': 'postgres'` in `db_config` dict at module level. This file is not imported by the main app but is present in the backend directory.
- Files: `backend/test_db_connection.py:8-13`
- Impact: Credentials committed to source control. Could mislead developers into using these credentials.
- Fix approach: Move to environment variables or a `.env`-based config, or remove the file if its purpose is served by the migration system.

### Seed script with hardcoded admin password
- Issue: `backend/scripts/seed.py` uses `generate_password_hash('admin123')` and references model fields like `name` that may not exist on the current `User` model (current model has `nickname`, not `name`).
- Files: `backend/scripts/seed.py:16`
- Impact: Seed script likely broken due to schema drift. Hardcoded password is a security anti-pattern.
- Fix approach: Update seed script to match current `User` model schema and read credentials from environment variables.

### File with typo in filename
- Issue: `backend/GoldStratagy(Step-By-Step).py` has "Stratagy" (misspelled "Strategy"). The file uses `print()` statements throughout and appears to be a standalone prototype rather than integrated application code.
- Files: `backend/GoldStratagy(Step-By-Step).py`
- Impact: Clutters the backend directory. The parentheses in the filename can cause issues with some tooling. Not part of the Flask application.
- Fix approach: Move to an `examples/` or `scripts/` directory, or remove if no longer needed.

### `AUTH_FIXED_SMS_CODE` default in production config
- Issue: The `.env.example` sets `AUTH_FIXED_SMS_CODE=123456` and `docker-compose.yml` also defaults to `AUTH_FIXED_SMS_CODE: ${AUTH_FIXED_SMS_CODE:-123456}`. If this variable is set in production, any attacker can authenticate with code `123456`.
- Files: `backend/app/config.py:45`, `.env.example:58`, `docker-compose.yml:72`
- Impact: CRITICAL if deployed with this default. Anyone knowing a phone number could log in.
- Fix approach: Ensure `AUTH_FIXED_SMS_CODE` is empty/unset in production. Add a startup check in `ProdConfig` that warns or raises if this value is set. Remove it from `docker-compose.yml` production defaults.

### `PASS` placeholder in config fallbacks
- Issue: `BaseConfig` in `backend/app/config.py` uses fallback defaults `'dev-secret'` for `SECRET_KEY` and `'dev-jwt-secret'` for `JWT_SECRET_KEY`. These are only acceptable in development but would silently allow the app to start in production with insecure secrets.
- Files: `backend/app/config.py:21-22`
- Impact: If `SECRET_KEY` or `JWT_SECRET` env vars are not set in production, tokens are predictable.
- Fix approach: Add validation in `ProdConfig.__init__` that raises if `SECRET_KEY` or `JWT_SECRET_KEY` still matches the dev default.

## Security Concerns

### No API rate limiting
- Issue: No rate-limiting middleware (e.g., `flask-limiter`) is configured. All API endpoints are unprotected from brute-force or abuse. SMS-based authentication is especially vulnerable.
- Files: `backend/app/__init__.py` (no rate limiter initialization)
- Impact: Attackers can brute-force verification codes, spam backtest requests, or overwhelm the API.
- Fix approach: Integrate `flask-limiter` with Redis backend. Apply strict limits on auth endpoints (`/api/v1/auth/login`, `/api/v1/auth/register`) and reasonable limits on all other endpoints.

### OAuth access token stored in database
- Issue: `OAuthIdentity.access_token` stores the OAuth provider access token in plaintext in the database (column at `backend/app/models.py:770` referenced in `backend/app/blueprints/auth.py:523-524`).
- Files: `backend/app/blueprints/auth.py:523`, `backend/app/models.py`
- Impact: If the database is compromised, all OAuth access tokens are exposed.
- Fix approach: Encrypt OAuth access tokens using the same Fernet encryption used for `UserIntegrationSecret`, or store only a hash and re-request when needed.

### Payment webhook signature verification not implemented
- Issue: Payment webhooks (`/api/v1/payments/webhook/wechat` and `/api/v1/payments/webhook/alipay`) accept payloads in sandbox mode without signature verification. The production branch simply returns an error.
- Files: `backend/app/blueprints/payments.py:284-331`
- Impact: When moving to production, webhook verification must be implemented or payments can be forged.
- Fix approach: Implement proper signature verification for WeChat Pay and Alipay callbacks before enabling production payment mode.

### Sandbox code execution uses `exec()`
- Issue: `backend/app/strategy_runtime/sandbox.py:151` uses `exec(payload['source'], namespace, namespace)` to run user-submitted strategy code. While there are AST-level guards (`guard_strategy_source`) and restricted builtins, `exec()` is inherently dangerous.
- Files: `backend/app/strategy_runtime/sandbox.py:146-204`
- Impact: If AST guards are bypassed (e.g., through encoding tricks, obfuscated code, or new Python features), arbitrary code execution is possible.
- Current mitigation: `FORBIDDEN_IMPORTS` and `FORBIDDEN_BUILTINS` lists, subprocess isolation with timeout, restricted `__builtins__` namespace.
- Fix approach: The subprocess isolation is good. Consider adding resource limits (`resource.setrlimit` for memory/CPU) inside the subprocess, and regularly audit the guard lists against new Python features.

### Inconsistent error message languages
- Issue: Error messages mix Chinese and English. Some JWT callbacks return Chinese (`"未登录"`, `"登录已过期"`, `"无效的访问令牌"`) while others return English. The admin helper returns Chinese (`"管理员权限不足"`).
- Files: `backend/app/__init__.py:90-110`, `backend/app/utils/auth_helpers.py:13`
- Impact: Inconsistent UX. Could confuse frontend error handling that matches on message strings.
- Fix approach: Use error codes (already present) consistently. Store user-facing messages in an i18n layer. Never match on message text for logic.

## Architecture Concerns

### Oversized blueprint files
- Issue: Several blueprint files exceed reasonable size thresholds:
  - `backend/app/blueprints/admin.py` -- 949 lines
  - `backend/app/blueprints/strategies.py` -- 917 lines
  - `backend/app/blueprints/marketplace.py` -- 731 lines
- Files: `backend/app/blueprints/admin.py`, `backend/app/blueprints/strategies.py`, `backend/app/blueprints/marketplace.py`
- Impact: Hard to navigate, review, and test. Increases merge conflict probability.
- Fix approach: Split by domain. For `admin.py`, separate strategy review, user management, and content moderation into sub-blueprints. For `strategies.py`, separate CRUD, import, and AI generation routes.

### Oversized frontend view components
- Issue: Several Vue components are very large:
  - `frontend/src/views/AiStrategyLabView.vue` -- 1982 lines
  - `frontend/src/views/BacktestResultView.vue` -- 1731 lines
  - `frontend/src/views/BacktestsView.vue` -- 1661 lines
  - `frontend/src/views/PricingView.vue` -- 1358 lines
  - `frontend/src/views/NewStrategyView.vue` -- 1354 lines
- Files: `frontend/src/views/AiStrategyLabView.vue`, `frontend/src/views/BacktestResultView.vue`, `frontend/src/views/BacktestsView.vue`, `frontend/src/views/PricingView.vue`, `frontend/src/views/NewStrategyView.vue`
- Impact: Difficult to maintain. Component reusability suffers. Slows build and hot-reload.
- Fix approach: Extract sub-components, composables, and utility functions. Target 400-600 lines per view maximum.

### Monolithic models file
- Issue: `backend/app/models.py` is 814 lines and contains 25+ model classes in a single file.
- Files: `backend/app/models.py`
- Impact: Slow to navigate. Changes to any model risk merge conflicts. Circular import risk increases.
- Fix approach: Split into domain modules: `models/user.py`, `models/strategy.py`, `models/community.py`, `models/payment.py`, `models/integration.py`, etc. Re-export from `models/__init__.py`.

### `strategies_bp` optional import with silent failure
- Issue: `backend/app/__init__.py:29-32` wraps the strategies blueprint import in a `try/except ModuleNotFoundError` and silently sets it to `None`. This hides import errors that could indicate a real problem.
- Files: `backend/app/__init__.py:29-32`
- Impact: If a dependency of the strategies module breaks, the app starts without the strategies API and the error is swallowed.
- Fix approach: Remove the try/except once the module is stable. If conditional loading is needed, log a warning when it fails.

### Duplicate environment config in docker-compose
- Issue: Environment variables are duplicated across the `backend`, `celery-worker`, and `celery-beat` services in `docker-compose.yml` (lines 43-74, 98-125, 142-151). Changing one requires updating all three.
- Files: `docker-compose.yml`
- Impact: Config drift between services. Maintenance burden.
- Fix approach: Use `env_file` directive or YAML anchors/extends to share the common environment block.

## Performance Bottlenecks

### In-memory fallback store for auth tokens
- Issue: `backend/app/utils/redis_client.py:11-64` implements `_MemoryStore` as a fallback when Redis is unavailable. In production without Redis, all token blacklisting, SMS codes, and throttling happen in process memory.
- Files: `backend/app/utils/redis_client.py:11-64`
- Impact: Token blacklists do not survive restarts. SMS codes and rate limits reset. In multi-process deployment (Gunicorn with workers), each worker has independent state.
- Fix approach: Make Redis a hard requirement for production. Log a warning at startup when falling back to memory store. Add a health check that fails if Redis is unavailable in production.

### N+1 query pattern in admin strategy listing
- Issue: `backend/app/blueprints/admin.py:47-55` joins Strategy and User but serialization calls `_serialize_admin_strategy()` which may trigger lazy-loaded relationships per row.
- Files: `backend/app/blueprints/admin.py:47-59`
- Impact: For each strategy in the paginated list, additional queries may fire for related data.
- Fix approach: Use `joinedload()` or `selectinload()` for required relationships, or ensure serialization only accesses already-loaded attributes.

## Fragile Areas

### Strategy sandbox AST guard bypass potential
- Files: `backend/app/strategy_runtime/sandbox.py:40-58`
- Why fragile: AST-based code analysis must keep up with Python language changes. New syntax or builtins could bypass the blocklist. The `FORBIDDEN_BUILTINS` list checks `ast.Name` nodes but does not detect `getattr(__builtins__, 'exec')` patterns.
- Safe modification: Add tests for known bypass patterns. Review guard lists when upgrading Python version.
- Test coverage: `backend/tests/test_sandbox_service.py` and `backend/tests/test_strategy_review.py` exist but should include adversarial test cases.

### OAuth state management relies on Redis/Memory store
- Files: `backend/app/blueprints/auth.py:441`
- Why fragile: OAuth state tokens are stored using `store._backend.set(...)` which exposes the private `_backend` attribute. If store implementation changes, this breaks.
- Safe modification: Add a public method on `AuthStore` for general-purpose key-value storage rather than reaching into `_backend` directly.

## Scaling Limits

### SQLite fallback in tests
- Issue: Test fixture at `backend/tests/conftest.py:53` falls back to SQLite when `QYQUANT_TEST_DATABASE_URL` is not set. SQLite does not support PostgreSQL-specific features (JSONB, TSVECTOR, partial indexes).
- Files: `backend/tests/conftest.py:47-53`
- Impact: Tests may pass on SQLite but fail in production on PostgreSQL due to dialect differences.
- Fix approach: Require PostgreSQL for tests. Document the `QYQUANT_TEST_DATABASE_URL` requirement in the development setup guide.

### Celery tasks without idempotency guards
- Issue: Task files like `backend/app/tasks/backtests.py` and `backend/app/tasks/simulation_tasks.py` process jobs but may not guard against duplicate execution if a task is retried.
- Files: `backend/app/tasks/backtests.py`, `backend/app/tasks/simulation_tasks.py`
- Impact: In Celery with retries, a task could execute twice, consuming quota twice or creating duplicate results.
- Fix approach: Add idempotency checks (e.g., check job status before processing, use database-level locks).

## Test Coverage Gaps

### No frontend E2E tests
- What's not tested: End-to-end user flows (login, strategy creation, backtest execution, payment).
- Files: No `frontend/tests/e2e/` or Playwright/Cypress config found.
- Risk: Critical user journeys (auth, payment) are not verified against real browser behavior.
- Priority: High

### Adversarial sandbox tests missing
- What's not tested: Strategy sandbox bypass attempts (e.g., `getattr(__builtins__, 'exec')`, encoding tricks, `__class__.__subclasses__()` traversal).
- Files: `backend/tests/test_sandbox_service.py`
- Risk: Security-critical sandbox could have bypass paths that are never tested.
- Priority: High

### No integration tests for payment webhooks
- What's not tested: Payment webhook callback handling with realistic payloads.
- Files: `backend/tests/test_payments.py` (441 lines but may not cover webhook flows).
- Risk: Payment activation logic may break silently when moving to production.
- Priority: Medium

### No load or performance tests
- What's not tested: System behavior under concurrent requests, large backtest payloads, or many simultaneous strategy executions.
- Risk: Performance regressions go undetected until production.
- Priority: Medium

## Improvement Opportunities

### Quick wins
1. **Remove `app_legacy.py`** -- Dead code that creates confusion about which app factory to use.
2. **Add `flask-limiter`** -- Prevents brute-force on auth endpoints. Can be added incrementally.
3. **Validate production secrets at startup** -- Add checks in `ProdConfig` to reject default secret values.
4. **Fix seed script schema drift** -- Update `backend/scripts/seed.py` to match current `User` model.
5. **Move prototype files out of backend root** -- Relocate `GoldStratagy(Step-By-Step).py` to an examples directory.

### Patterns that could be standardized
1. **Error response format** -- All blueprints should use `error_response()` from `backend/app/utils/response.py`. Some routes still return raw tuples.
2. **Serialization** -- Some blueprints use Marshmallow schemas, others use manual dict construction. Standardize on one approach.
3. **Blueprint URL prefix convention** -- Some use `/api`, others use `/api/v1`, others use `/api/v1/<resource>`. Adopt a consistent versioning strategy.
4. **Logging** -- `backend/app/errors.py` uses `logging.getLogger(__name__)` but most modules use `print()` for diagnostics. Standardize on structured logging.

### Documentation gaps
1. **Deployment guide** -- No documentation on production deployment beyond `docker-compose.yml`.
2. **Environment variable reference** -- `.env.example` exists but lacks descriptions for each variable.
3. **API documentation** -- OpenAPI/Swagger is configured at `/api/docs` but completeness is unknown.
4. **Development setup guide** -- No step-by-step guide for new developers (database setup, Redis, Celery workers).

---

*Concerns audit: 2026-04-27*

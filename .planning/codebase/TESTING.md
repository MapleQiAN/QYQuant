# Testing Patterns

**Analysis Date:** 2026-04-27

## Test Framework

### Backend (Python)

**Runner:**
- pytest >= 9.0
- pytest-flask >= 1.3.0
- pytest-cov >= 6.0
- Config: `pyproject.toml` (dev dependencies), no `pytest.ini` or `conftest.ini`

**Run Commands:**
```bash
cd backend && python -m pytest                    # Run all tests
cd backend && python -m pytest tests/test_auth.py  # Single file
cd backend && python -m pytest -x                  # Stop on first failure
cd backend && python -m pytest --cov=app           # Coverage
```

### Frontend (TypeScript/Vue)

**Runner:**
- vitest ^1.6.0
- @vue/test-utils ^2.4.5
- jsdom ^24.0.0
- msw ^2.2.0 (Mock Service Worker for dev mocks)
- Config: `frontend/vitest.config.ts`

**Run Commands:**
```bash
cd frontend && npm test              # Run all tests (vitest run)
cd frontend && npx vitest            # Watch mode
cd frontend && npx vitest run --coverage  # Coverage
```

## Test File Organization

### Backend

**Location:** `backend/tests/` -- separate from source code
**Naming:** `test_<module>.py`
**Conftest:** `backend/tests/conftest.py`

```
backend/tests/
    conftest.py               # Shared fixtures (app, client, seed_user)
    test_admin.py             # Admin blueprint tests
    test_auth.py              # Auth blueprint tests
    test_backtests.py         # Backtest blueprint tests
    test_bots.py              # Bot blueprint tests
    test_community.py         # Community blueprint tests
    test_health.py            # Health endpoint tests
    test_integrations.py      # Integration tests
    test_marketplace.py       # Marketplace tests
    test_models.py            # Model persistence tests
    test_payments.py          # Payment tests
    test_report_agent.py      # AI report agent tests
    test_sandbox_service.py   # Sandbox service tests
    test_schemas.py           # Marshmallow schema tests
    test_strategies.py        # Strategy CRUD tests
    test_users.py             # User management tests
    ...                       # ~30+ test files total
```

### Frontend

**Location:** Co-located with source files -- `.test.ts` suffix
**Setup:** `frontend/tests/setup.ts`

```
frontend/tests/
    setup.ts                              # Global test setup (i18n plugin)

frontend/src/api/
    auth.test.ts                          # API layer unit tests
    backtests.test.ts
    http.test.ts
    normalizeError.test.ts
    strategies.test.ts
    ...

frontend/src/stores/
    user.test.ts                          # Pinia store tests
    strategies.test.ts
    backtests.test.ts
    useAdminStore.test.ts
    useMarketplaceStore.test.ts
    ...

frontend/src/views/
    DashboardView.test.ts                 # Vue component tests
    LoginView.test.ts
    BacktestsView.test.ts
    Marketplace.test.ts
    StrategyDetailView.test.ts
    ...

frontend/src/components/
    BacktestCard.test.ts                  # Component unit tests
    SideNav.test.ts
    TopNav.test.ts
    ...
```

## Test Configuration

### Backend (`backend/tests/conftest.py`)

- **Database:** SQLite by default, PostgreSQL if `QYQUANT_TEST_DATABASE_URL` env var is set
- **Environment:** `FLASK_ENV=testing` with fixed `AUTH_FIXED_SMS_CODE='123456'`
- **Celery:** `CELERY_TASK_ALWAYS_EAGER=1` (tasks run synchronously in tests)

### Frontend (`frontend/vitest.config.ts`)

```typescript
export default defineConfig({
    plugins: [vue()],
    test: {
        environment: 'jsdom',
        setupFiles: ['./tests/setup.ts'],
        environmentOptions: {
            jsdom: { url: 'http://127.0.0.1/' }
        }
    }
})
```

### Frontend Test Setup (`frontend/tests/setup.ts`)

```typescript
import { config } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import en from '../src/i18n/messages/en'

const i18n = createI18n({
    legacy: false,
    locale: 'en',
    fallbackLocale: 'en',
    messages: { en }
})

config.global.plugins = [[i18n]]
```

## Backend Test Structure

### Core Fixtures (`conftest.py`)

```python
@pytest.fixture()
def app(tmp_path, monkeypatch):
    """Creates a Flask app with test config, SQLite database, and env vars."""
    monkeypatch.setenv('FLASK_ENV', 'testing')
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{db_path.as_posix()}")
    # ... sets 10+ env vars for isolated testing

    from app import create_app
    app = create_app('testing')
    with app.app_context():
        db.create_all()
    return app

@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()

@pytest.fixture(autouse=True)
def reset_auth_state():
    """Auto-resets auth store and SMS sender between tests."""
    reset_auth_store()
    reset_sms_sender()

@pytest.fixture()
def seed_user(app):
    """Creates a test user in the database."""
    with app.app_context():
        user = User(phone='13800000000', nickname='Admin')
        db.session.add(user)
        db.session.commit()
        return user
```

### Blueprint Test Pattern

Tests call Flask test client directly and assert on response JSON:

```python
def test_register_creates_email_user_and_returns_tokens(client, app):
    from app.models import User

    response = client.post(
        "/api/v1/auth/register",
        json={"email": "password@example.com", "password": "Secret123!", "nickname": "PasswordUser"},
    )

    assert response.status_code == 200
    assert response.json["data"]["nickname"] == "PasswordUser"
    assert isinstance(response.json["access_token"], str)

    with app.app_context():
        user = User.query.filter_by(email="password@example.com").one_or_none()
        assert user is not None
```

### Model Test Pattern

Tests verify database persistence and constraints:

```python
def test_user_model_fields(app):
    with app.app_context():
        user = User(phone="13800138000", nickname="量化小白")
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.phone == "13800138000"
        assert user.role == "user"
```

### Error Response Assertion Pattern

```python
def test_register_rejects_duplicate_email(client):
    second = client.post("/api/v1/auth/register", json={...})
    assert second.status_code == 409
    assert second.json["error"]["code"] == "EMAIL_EXISTS"
```

## Frontend Test Structure

### API Layer Test Pattern

Mock Axios with `vi.mock` and `vi.hoisted`, test function calls and return values:

```typescript
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { login, registerWithPassword } from './auth'

const { postMock } = vi.hoisted(() => ({
    postMock: vi.fn(),
}))

vi.mock('axios', () => ({
    default: {
        create: () => ({
            post: postMock,
            interceptors: { response: { use: vi.fn() } },
        }),
    },
}))

describe('auth api', () => {
    beforeEach(() => { postMock.mockReset() })

    it('supports email login payload', async () => {
        postMock.mockResolvedValueOnce({
            data: { data: { user_id: 'user-1', ... }, access_token: 'token-1' },
        })

        const result = await login({ email: 'alice@example.com', password: 'Secret123!' })
        expect(postMock).toHaveBeenCalledWith('/v1/auth/login', { ... })
        expect(result.access_token).toBe('token-1')
    })
})
```

### Pinia Store Test Pattern

Create fresh Pinia instance per test, mock API layer:

```typescript
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from './user'

vi.mock('../api/users', () => ({
    fetchProfile: fetchProfileMock,
}))

describe('user store', () => {
    beforeEach(() => {
        setActivePinia(createPinia())
        fetchProfileMock.mockReset()
        localStorage.clear()
    })

    it('updates locale', () => {
        const store = useUserStore()
        store.setLocale('zh')
        expect(store.locale).toBe('zh')
    })
})
```

### Vue Component Test Pattern

Mount with `@vue/test-utils`, mock stores and router:

```typescript
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'

vi.mock('vue-router', () => ({
    RouterLink: { template: '<a><slot /></a>' },
    useRouter: () => ({ push: pushMock })
}))

vi.mock('../stores', () => ({
    useUserStore: () => ({ profile: { ... }, loadProfile: vi.fn() }),
    // ... other stores
}))

describe('DashboardView', () => {
    it('renders localized header', () => {
        const i18n = createI18n({ legacy: false, locale: 'zh', messages: { zh } })
        const wrapper = mount(DashboardView, {
            global: {
                plugins: [i18n],
                stubs: { BacktestCard: { template: '<div />' } }
            }
        })
        expect(wrapper.text()).toContain('欢迎回来')
    })
})
```

## Mocking

### Backend Mocking

- **No mocking framework** -- uses real database (SQLite in-memory for speed)
- **Celery eager mode:** `CELERY_TASK_ALWAYS_EAGER=1` makes tasks run synchronously
- **SMS codes:** Fixed `AUTH_FIXED_SMS_CODE='123456'` in test config
- **Redis:** `get_auth_store()` uses a resettable in-memory store (see `reset_auth_state` fixture)
- **Data provider:** `BACKTEST_DATA_PROVIDER=mock` in test environment

### Frontend Mocking

- **Axios mocking:** `vi.mock('axios', ...)` to replace `axios.create()` with mock functions
- **Store mocking:** `vi.mock('../stores', ...)` to provide stub store implementations
- **Router mocking:** `vi.mock('vue-router', ...)` with `useRouter` returning `pushMock`
- **vi.hoisted:** Used for shared mock references before `vi.mock` calls:

```typescript
const { postMock } = vi.hoisted(() => ({ postMock: vi.fn() }))
vi.mock('axios', () => ({ default: { create: () => ({ post: postMock, ... }) } }))
```

- **localStorage mocking:** Custom implementation via `vi.hoisted` for components that need it:

```typescript
const storage = vi.hoisted(() => {
    const values = new Map<string, string>()
    return { getItem(key) { ... }, setItem(key, value) { ... }, ... }
})
Object.defineProperty(globalThis, 'localStorage', { value: storage, configurable: true })
```

- **MSW (Mock Service Worker):** Used in development mode only (`frontend/src/mocks/`), not in tests

## Fixtures and Test Data

### Backend

- No factory library (no factory_boy or similar)
- Test data created inline in tests via model constructors
- `seed_user` fixture provides a baseline user (phone: `13800000000`, nickname: `Admin`)
- Uses `tmp_path` fixture for file storage isolation

### Frontend

- MSW mock data in `frontend/src/mocks/data.ts` (for dev mode, not test mode)
- Test-specific mock return values defined inline in each test via `mockResolvedValueOnce()`

## Coverage

**Requirements:** No enforced coverage threshold detected in config files.

**Run Coverage:**
```bash
cd backend && python -m pytest --cov=app           # Backend coverage
cd frontend && npx vitest run --coverage            # Frontend coverage
```

**Dependencies:** `pytest-cov >= 6.0` installed but no `--cov-fail-under` configured.

## Test Types

### Unit Tests

- **Backend:** Model persistence tests, schema serialization tests, utility function tests
  - Examples: `test_models.py`, `test_schemas.py`, `test_error_parser.py`
- **Frontend:** API function tests, store action tests, utility function tests
  - Examples: `auth.test.ts`, `user.test.ts`, `normalizeError.test.ts`

### Integration Tests

- **Backend:** Blueprint endpoint tests that exercise the full Flask request/response cycle through the test client
  - Examples: `test_auth.py`, `test_strategies.py`, `test_marketplace.py`
  - These use real database, real Flask app, real route dispatch

### Component Tests

- **Frontend:** Vue component mount tests with stubs for child components and mocked stores
  - Examples: `DashboardView.test.ts`, `SideNav.test.ts`, `BacktestCard.test.ts`

### E2E Tests

- **Not used.** No Playwright, Cypress, or similar E2E framework detected.

## CI/CD Test Integration

**No CI/CD pipeline detected.** No `.github/workflows/`, no `Jenkinsfile`, no `GitLab CI` config.

Tests are run manually via command line.

## Common Patterns

### Backend Test Helper Functions

Tests for auth-related endpoints define helper functions at the top of the test file:

```python
def _extract_refresh_cookie(response):
    cookies = response.headers.getlist("Set-Cookie")
    for cookie in cookies:
        if cookie.startswith("refresh_token="):
            return cookie
    return ""
```

### Backend Testing with Auth

Authenticated endpoints use the test client with JWT headers:

```python
# Register and get token
register = client.post("/api/v1/auth/register", json={...})
token = register.json["access_token"]

# Use token for authenticated request
response = client.get("/api/v1/protected", headers={"Authorization": f"Bearer {token}"})
```

### Frontend Async Testing

All async tests use `async/await` naturally -- no callbacks:

```typescript
it('loads recent strategies and clears error', async () => {
    const store = useStrategiesStore()
    await store.loadRecent()
    expect(store.error).toBeNull()
    expect(store.recent.length).toBe(1)
})
```

### Frontend Error Testing

```typescript
it('clears token when profile loading fails with unauthorized status', async () => {
    localStorage.setItem('qyquant-token', 'token-1')
    fetchProfileMock.mockRejectedValueOnce({ status: 401, message: 'unauthorized' })

    const store = useUserStore()
    await store.loadProfile()

    expect(localStorage.getItem('qyquant-token')).toBeNull()
})
```

---

*Testing analysis: 2026-04-27*

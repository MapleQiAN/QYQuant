# Dashboard API Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Vue Router, Pinia, Axios API layer, MSW mock backend, and typed data flow so the dashboard loads data from /api endpoints and is Flask-ready.

**Architecture:** Keep UI components as dumb views fed by domain Pinia stores. Stores call an Axios client with retry + error normalization. MSW mocks API responses in dev only. Router controls views and TopNav navigation.

**Tech Stack:** Vue 3 + TS, Vite, Vue Router, Pinia, Axios, MSW, Vue Toastification, Vitest.

---

### Task 1: Add test runner and retry utility (TDD)

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/vitest.config.ts`
- Create: `frontend/src/lib/retry.test.ts`
- Create: `frontend/src/lib/retry.ts`

**Step 1: Write the failing test**

```ts
import { describe, it, expect, vi } from 'vitest'
import { retry } from './retry'

describe('retry', () => {
  it('retries with exponential backoff and succeeds', async () => {
    const fn = vi.fn()
      .mockRejectedValueOnce(new Error('fail'))
      .mockRejectedValueOnce(new Error('fail'))
      .mockResolvedValueOnce('ok')

    vi.useFakeTimers()
    const promise = retry(fn, { retries: 3, delays: [200, 400, 800] })

    await vi.advanceTimersByTimeAsync(200)
    await vi.advanceTimersByTimeAsync(400)

    await expect(promise).resolves.toBe('ok')
    expect(fn).toHaveBeenCalledTimes(3)
  })
})
```

**Step 2: Run test to verify it fails**

Run: `npm run test -- src/lib/retry.test.ts`
Expected: FAIL with "Cannot find module './retry'" or similar.

**Step 3: Write minimal implementation**

```ts
export async function retry<T>(
  fn: () => Promise<T>,
  options: { retries: number; delays: number[] }
): Promise<T> {
  const { retries, delays } = options
  let lastError: unknown
  for (let attempt = 0; attempt < retries; attempt += 1) {
    try {
      return await fn()
    } catch (error) {
      lastError = error
      const delay = delays[attempt] ?? delays[delays.length - 1] ?? 0
      if (attempt < retries - 1 && delay > 0) {
        await new Promise((resolve) => setTimeout(resolve, delay))
      }
    }
  }
  throw lastError
}
```

**Step 4: Run test to verify it passes**

Run: `npm run test -- src/lib/retry.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/package.json frontend/vitest.config.ts frontend/src/lib/retry.test.ts frontend/src/lib/retry.ts
git commit -m "test: add retry utility"
```

---

### Task 2: Axios client + error normalization (TDD)

**Files:**
- Create: `frontend/src/api/normalizeError.test.ts`
- Create: `frontend/src/api/normalizeError.ts`
- Create: `frontend/src/api/http.test.ts`
- Create: `frontend/src/api/http.ts`
- Modify: `frontend/package.json`

**Step 1: Write the failing tests**

```ts
import { describe, it, expect } from 'vitest'
import { normalizeError } from './normalizeError'

describe('normalizeError', () => {
  it('normalizes axios-like error', () => {
    const err = {
      response: { status: 500, data: { message: 'boom' } },
      message: 'Request failed'
    }
    expect(normalizeError(err)).toEqual({
      status: 500,
      message: 'boom'
    })
  })
})
```

```ts
import { describe, it, expect, vi } from 'vitest'
import { createHttpClient } from './http'

vi.mock('axios', () => {
  return {
    default: {
      create: () => ({
        request: vi.fn().mockResolvedValue({ data: { ok: true } }),
        interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } }
      })
    }
  }
})

describe('http client', () => {
  it('returns data from request', async () => {
    const client = createHttpClient()
    const data = await client.request({ method: 'get', url: '/ping' })
    expect(data).toEqual({ ok: true })
  })
})
```

**Step 2: Run tests to verify they fail**

Run: `npm run test -- src/api/normalizeError.test.ts src/api/http.test.ts`
Expected: FAIL (missing modules).

**Step 3: Write minimal implementation**

```ts
export function normalizeError(error: any): { status?: number; message: string } {
  const status = error?.response?.status
  const message = error?.response?.data?.message || error?.message || 'Unknown error'
  return { status, message }
}
```

```ts
import axios, { AxiosRequestConfig } from 'axios'
import { retry } from '../lib/retry'
import { normalizeError } from './normalizeError'

export function createHttpClient() {
  const instance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE || '/api',
    timeout: 8000
  })

  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      throw normalizeError(error)
    }
  )

  return {
    async request<T>(config: AxiosRequestConfig): Promise<T> {
      return retry(async () => {
        const response = await instance.request<T>(config)
        return response.data
      }, { retries: 3, delays: [200, 400, 800] })
    }
  }
}
```

**Step 4: Run tests to verify they pass**

Run: `npm run test -- src/api/normalizeError.test.ts src/api/http.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/api/normalizeError.test.ts frontend/src/api/normalizeError.ts frontend/src/api/http.test.ts frontend/src/api/http.ts
git commit -m "feat: add api http client"
```

---

### Task 3: Types and API modules

**Files:**
- Create: `frontend/src/types/Backtest.ts`
- Create: `frontend/src/types/Strategy.ts`
- Create: `frontend/src/types/Bot.ts`
- Create: `frontend/src/types/Post.ts`
- Create: `frontend/src/types/User.ts`
- Create: `frontend/src/types/KlineBar.ts`
- Create: `frontend/src/types/Trade.ts`
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/api/backtests.ts`
- Create: `frontend/src/api/bots.ts`
- Create: `frontend/src/api/strategies.ts`
- Create: `frontend/src/api/forum.ts`
- Modify: `frontend/src/api/http.ts`

**Step 1: Write failing test for a domain API**

```ts
import { describe, it, expect, vi } from 'vitest'
import * as backtests from './backtests'

vi.mock('./http', () => ({
  createHttpClient: () => ({ request: vi.fn().mockResolvedValue({ ok: true }) })
}))

describe('backtests api', () => {
  it('calls latest endpoint', async () => {
    const data = await backtests.fetchLatest()
    expect(data).toEqual({ ok: true })
  })
})
```

**Step 2: Run test to verify it fails**

Run: `npm run test -- src/api/backtests.test.ts`
Expected: FAIL (missing module).

**Step 3: Write minimal implementation**

```ts
import { createHttpClient } from './http'
import type { BacktestLatestResponse } from '../types/Backtest'

const client = createHttpClient()

export function fetchLatest(): Promise<BacktestLatestResponse> {
  return client.request({ method: 'get', url: '/backtests/latest' })
}
```

**Step 4: Run test to verify it passes**

Run: `npm run test -- src/api/backtests.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/types frontend/src/api
git commit -m "feat: add domain types and api modules"
```

---

### Task 4: Pinia stores (TDD)

**Files:**
- Create: `frontend/src/stores/backtests.test.ts`
- Create: `frontend/src/stores/backtests.ts`
- Create: `frontend/src/stores/bots.test.ts`
- Create: `frontend/src/stores/bots.ts`
- Create: `frontend/src/stores/strategies.test.ts`
- Create: `frontend/src/stores/strategies.ts`
- Create: `frontend/src/stores/forum.test.ts`
- Create: `frontend/src/stores/forum.ts`
- Create: `frontend/src/stores/index.ts`

**Step 1: Write failing test (example: backtests store)**

```ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useBacktestsStore } from './backtests'

vi.mock('../api/backtests', () => ({
  fetchLatest: vi.fn().mockResolvedValue({ summary: { totalReturn: 1 }, kline: [], trades: [] })
}))

describe('backtests store', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('loads latest and clears error', async () => {
    const store = useBacktestsStore()
    await store.loadLatest()
    expect(store.error).toBeNull()
    expect(store.latest).not.toBeNull()
  })
})
```

**Step 2: Run test to verify it fails**

Run: `npm run test -- src/stores/backtests.test.ts`
Expected: FAIL (missing store module).

**Step 3: Write minimal implementation**

```ts
import { defineStore } from 'pinia'
import { fetchLatest } from '../api/backtests'
import type { BacktestLatestResponse } from '../types/Backtest'

export const useBacktestsStore = defineStore('backtests', {
  state: () => ({
    latest: null as BacktestLatestResponse | null,
    loading: false,
    error: null as string | null
  }),
  actions: {
    async loadLatest() {
      this.loading = true
      this.error = null
      try {
        this.latest = await fetchLatest()
      } catch (error: any) {
        this.error = error?.message || 'Failed to load backtest'
      } finally {
        this.loading = false
      }
    }
  }
})
```

**Step 4: Run test to verify it passes**

Run: `npm run test -- src/stores/backtests.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/stores
git commit -m "feat: add pinia domain stores"
```

---

### Task 5: MSW mock backend

**Files:**
- Create: `frontend/src/mocks/data.ts`
- Create: `frontend/src/mocks/handlers.ts`
- Create: `frontend/src/mocks/browser.ts`
- Modify: `frontend/package.json`

**Step 1: Write failing test for a handler**

```ts
import { describe, it, expect } from 'vitest'
import { handlers } from './handlers'

describe('handlers', () => {
  it('exports handlers array', () => {
    expect(Array.isArray(handlers)).toBe(true)
  })
})
```

**Step 2: Run test to verify it fails**

Run: `npm run test -- src/mocks/handlers.test.ts`
Expected: FAIL (missing module).

**Step 3: Write minimal implementation**

```ts
import { http, HttpResponse } from 'msw'
import { latestBacktest, recentBots, recentStrategies, hotPosts } from './data'

export const handlers = [
  http.get('/api/backtests/latest', () => HttpResponse.json(latestBacktest)),
  http.get('/api/bots/recent', () => HttpResponse.json(recentBots)),
  http.get('/api/strategies/recent', () => HttpResponse.json(recentStrategies)),
  http.get('/api/forum/hot', () => HttpResponse.json(hotPosts))
]
```

**Step 4: Run test to verify it passes**

Run: `npm run test -- src/mocks/handlers.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/mocks
git commit -m "feat: add msw mock backend"
```

---

### Task 6: Router + views

**Files:**
- Create: `frontend/src/router/index.ts`
- Create: `frontend/src/views/DashboardView.vue`
- Create: `frontend/src/views/BacktestsView.vue`
- Create: `frontend/src/views/BotsView.vue`
- Create: `frontend/src/views/ForumView.vue`
- Modify: `frontend/src/App.vue`

**Step 1: Write failing test for router config**

```ts
import { describe, it, expect } from 'vitest'
import router from './index'

describe('router', () => {
  it('contains dashboard route', () => {
    const hasDashboard = router.getRoutes().some((r) => r.path === '/')
    expect(hasDashboard).toBe(true)
  })
})
```

**Step 2: Run test to verify it fails**

Run: `npm run test -- src/router/index.test.ts`
Expected: FAIL (missing module).

**Step 3: Write minimal implementation**

```ts
import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'
import BacktestsView from '../views/BacktestsView.vue'
import BotsView from '../views/BotsView.vue'
import ForumView from '../views/ForumView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: DashboardView },
    { path: '/backtests', name: 'backtests', component: BacktestsView },
    { path: '/bots', name: 'bots', component: BotsView },
    { path: '/forum', name: 'forum', component: ForumView }
  ]
})

export default router
```

**Step 4: Run test to verify it passes**

Run: `npm run test -- src/router/index.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/router frontend/src/views frontend/src/App.vue
git commit -m "feat: add router and views"
```

---

### Task 7: UI state components + wire stores into dashboard

**Files:**
- Create: `frontend/src/components/SkeletonState.vue`
- Create: `frontend/src/components/EmptyState.vue`
- Create: `frontend/src/components/ErrorState.vue`
- Modify: `frontend/src/components/BacktestCard.vue`
- Modify: `frontend/src/components/RecentList.vue`
- Modify: `frontend/src/components/ForumMiniCard.vue`
- Modify: `frontend/src/components/TopNav.vue`
- Modify: `frontend/src/components/UpgradeCard.vue`
- Modify: `frontend/src/components/ProgressCard.vue`
- Modify: `frontend/src/views/DashboardView.vue`
- Create: `frontend/src/views/DashboardView.test.ts`

**Step 1: Write failing component test**

```ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import DashboardView from './DashboardView.vue'

describe('DashboardView', () => {
  it('renders backtest section title', () => {
    const wrapper = mount(DashboardView)
    expect(wrapper.text()).toContain('Backtest')
  })
})
```

**Step 2: Run test to verify it fails**

Run: `npm run test -- src/views/DashboardView.test.ts`
Expected: FAIL (missing component / router / store).

**Step 3: Write minimal implementation**

Update dashboard view to load store data in `onMounted`, update components to show Skeleton/Empty/Error based on store state, and keep layout tokens.

**Step 4: Run test to verify it passes**

Run: `npm run test -- src/views/DashboardView.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components frontend/src/views
git commit -m "feat: wire dashboard to stores with state components"
```

---

### Task 8: Main entry wiring (Router, Pinia, Toast, MSW)

**Files:**
- Modify: `frontend/src/main.ts`
- Create: `frontend/src/stores/user.ts`

**Step 1: Write failing test for entry (optional)**

```ts
import { describe, it, expect } from 'vitest'
import { createApp } from 'vue'

describe('main entry', () => {
  it('can create app instance', () => {
    const app = createApp({})
    expect(app).toBeTruthy()
  })
})
```

**Step 2: Run test to verify it fails**

Run: `npm run test -- src/main.test.ts`
Expected: FAIL (missing test file if not created).

**Step 3: Write minimal implementation**

Wire router, pinia, toastification, MSW start in dev, and mount app.

**Step 4: Run test to verify it passes**

Run: `npm run test -- src/main.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/main.ts frontend/src/stores/user.ts
git commit -m "feat: wire app entry"
```

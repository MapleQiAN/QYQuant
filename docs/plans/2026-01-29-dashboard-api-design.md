# QY Quant Dashboard API Integration Design

**Goal:** Upgrade the Vue 3 + TS dashboard skeleton into a Flask-ready architecture with Router, Pinia, API layer, MSW mock backend, and typed data flow.

## Architecture Summary
- **Entry**: `main.ts` boots Router, Pinia, Toastification, global styles, and starts MSW in development only.
- **Routing**: `/` dashboard + placeholder routes for `/backtests`, `/bots`, `/forum`.
- **State**: Pinia stores per domain (`backtests`, `bots`, `strategies`, `forum`) tracking `data`, `loading`, `error` and exposing fetch actions.
- **API**: Axios client with `baseURL = VITE_API_BASE || '/api'`, timeout, response normalization, exponential backoff retry (max 3), and global error handling via toast.
- **Mock**: MSW handlers for `/api/backtests/latest`, `/api/bots/recent`, `/api/strategies/recent`, `/api/forum/hot` with typed payloads.

## Data Flow (Home Page)
1. `DashboardView` loads.
2. It triggers store actions (`loadLatest`, `loadRecent`, `loadHot`).
3. Stores call API methods in `src/api/`.
4. Axios handles retries + errors; errors surface to toast and to store state.
5. Components render based on `loading/error/data` using shared Skeleton/Empty/Error states.

## Types
`src/types/` will include:
- `Backtest` (summary + KPIs + equity/kline + trades)
- `Strategy`
- `Bot`
- `Post`
- `User`
- `KlineBar`
- `Trade`
with `src/types/index.ts` re-exporting all.

## UI Components
- Existing components preserved: `TopNav`, `BacktestCard`, `RecentList`, `ForumMiniCard`, `UpgradeCard`, `ProgressCard`.
- New state components: `SkeletonState`, `EmptyState`, `ErrorState`.
- Existing 12-column grid, 8px spacing, and CSS tokens remain.

## Mock vs Flask
- MSW used only in development (`import.meta.env.DEV`).
- Production uses real `/api` or `VITE_API_BASE` proxy to Flask.

## Testing/Verification (Later)
- Smoke-run dev server to validate API + UI data flow.
- Optional: add unit tests for store actions and API client (not required in initial scope).

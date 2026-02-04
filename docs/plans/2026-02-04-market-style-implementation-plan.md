# Market Color Style Toggle Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a Settings toggle to switch price-movement colors between A-share (red up, green down) and US style (green up, red down) without changing other semantic colors.

**Architecture:** Persist a `marketStyle` preference in the user store and `localStorage`, apply it by setting `data-market-style` on `document.documentElement`, and use CSS variables (`--color-up`/`--color-down`) so only price-movement visuals flip.

**Tech Stack:** Vue 3, Pinia, vue-i18n v11, Vite, global CSS variables.

---

### Task 1: Market Style Helper + Store State

**Files:**
- Create: `frontend/src/styles/marketStyle.ts`
- Modify: `frontend/src/stores/user.ts`
- Modify: `frontend/src/main.ts`

**Step 1: Create the market style helper**

```ts
export type MarketStyle = 'cn' | 'us'
export const MARKET_STYLE_KEY = 'qyquant_market_style'

export function resolveInitialMarketStyle(): MarketStyle {
  if (typeof localStorage === 'undefined') {
    return 'cn'
  }
  const value = localStorage.getItem(MARKET_STYLE_KEY)
  return value === 'us' ? 'us' : 'cn'
}

export function applyMarketStyle(style: MarketStyle) {
  if (typeof document !== 'undefined') {
    document.documentElement.dataset.marketStyle = style
  }
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(MARKET_STYLE_KEY, style)
  }
}
```

**Step 2: Extend the user store**

```ts
import { applyMarketStyle, resolveInitialMarketStyle, type MarketStyle } from '../styles/marketStyle'

state: () => ({
  profile: defaultUser,
  locale: resolveInitialLocale(),
  marketStyle: resolveInitialMarketStyle()
}),
actions: {
  setMarketStyle(next: MarketStyle) {
    this.marketStyle = next
    applyMarketStyle(next)
  }
}
```

**Step 3: Apply style at startup**

```ts
const pinia = createPinia()
app.use(pinia)
const userStore = useUserStore(pinia)
applyMarketStyle(userStore.marketStyle)
```

**Step 4: Commit**

```bash
git add frontend/src/styles/marketStyle.ts frontend/src/stores/user.ts frontend/src/main.ts
git commit -m "feat: persist market color style"
```

---

### Task 2: CSS Variables + Price-Movement Usage

**Files:**
- Modify: `frontend/src/styles/global.css`
- Modify: `frontend/src/components/KlinePlaceholder.vue`
- Modify: `frontend/src/components/RecentList.vue`
- Modify: `frontend/src/components/ProgressCard.vue`
- Modify: `frontend/src/components/StatCard.vue`

**Step 1: Add market color variables**

```css
:root {
  --color-up: #ef4444;
  --color-up-bg: rgba(239, 68, 68, 0.1);
  --color-down: #10b981;
  --color-down-bg: rgba(16, 185, 129, 0.1);
}

:root[data-market-style="us"] {
  --color-up: #10b981;
  --color-up-bg: rgba(16, 185, 129, 0.1);
  --color-down: #ef4444;
  --color-down-bg: rgba(239, 68, 68, 0.1);
}
```

**Step 2: Replace price-movement color usage**
- Swap `var(--color-success)` -> `var(--color-up)` where it represents price up / profit.
- Swap `var(--color-danger)` -> `var(--color-down)` where it represents price down / loss.
- For backgrounds, use `--color-up-bg` / `--color-down-bg`.
- Keep status/semantic colors (`success`, `danger`, `warning`, `error`) unchanged.

**Step 3: Commit**

```bash
git add frontend/src/styles/global.css frontend/src/components/KlinePlaceholder.vue frontend/src/components/RecentList.vue frontend/src/components/ProgressCard.vue frontend/src/components/StatCard.vue
git commit -m "feat: add market up/down color variables"
```

---

### Task 3: Settings UI + i18n

**Files:**
- Modify: `frontend/src/views/SettingsView.vue`
- Modify: `frontend/src/i18n/messages/en.ts`
- Modify: `frontend/src/i18n/messages/zh.ts`

**Step 1: Add i18n strings**

```ts
settings: {
  marketStyle: 'Market Color Style',
  marketStyleHint: 'Choose how price moves are colored.',
  marketStyleCn: 'A-share style (red up, green down)',
  marketStyleUs: 'US style (green up, red down)'
}
```

```ts
settings: {
  marketStyle: '行情颜色风格',
  marketStyleHint: '选择涨跌颜色显示方式。',
  marketStyleCn: 'A股风格（红涨绿跌）',
  marketStyleUs: '美股风格（绿涨红跌）'
}
```

**Step 2: Add a new settings card**
- Reuse the existing toggle pattern and wire to `marketStyle`.
- Buttons should set `'cn'` and `'us'`.

```vue
const { locale, marketStyle } = storeToRefs(userStore)
function setMarketStyle(next: 'cn' | 'us') {
  userStore.setMarketStyle(next)
}
```

**Step 3: Commit**

```bash
git add frontend/src/views/SettingsView.vue frontend/src/i18n/messages/en.ts frontend/src/i18n/messages/zh.ts
git commit -m "feat: add market color style setting"
```

---

### Task 4: Manual Smoke Check (No Tests Requested)

**Step 1: Run dev server**

```bash
npm run dev
```

**Step 2: Verify**
- Settings toggle switches between A-share and US styles.
- Price-up visuals turn red for A-share, green for US.
- Non-price semantic colors (status/error) remain unchanged.

**Step 3: Commit (optional)**
- No code changes expected in this step.

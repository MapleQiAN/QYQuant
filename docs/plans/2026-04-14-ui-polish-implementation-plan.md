# QYQuant UI Polish Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade the current frontend from a generic purple SaaS dashboard into a cohesive, distinctive quant product UI with stronger hierarchy, clearer data emphasis, and better visual consistency across navigation, dashboard, and marketplace flows.

**Architecture:** Keep the existing Vue 3 + Pinia structure, but shift the visual system at the token layer first, then recompose the shell and highest-traffic screens on top of those tokens. The target direction is an editorial trading terminal: restrained charcoal and warm light surfaces, signal-driven market accents, denser data presentation, and stronger typography separation between product chrome and financial content.

**Tech Stack:** Vue 3, TypeScript, Pinia, Vue Router, vue-i18n, Vite, scoped component CSS, global CSS design tokens.

---

## Visual Direction

- **Tone:** Editorial trading terminal, not generic admin panel.
- **Primary look:** Deep graphite / paper-light neutral base, reduced purple usage, signal red/green only where price semantics matter, brass or ink accents for product identity.
- **Typography:** Distinguish product chrome from content. Keep body readable; use stronger heading treatment and more disciplined numeric styling.
- **Spatial model:** Fewer “same-weight cards”, more clear hero/secondary/utility zones.
- **Motion:** Replace blanket `transition: all` hover polish with intentional state transitions, subtle panel reveal, and meaningful feedback for data refresh/filter changes.

## Non-Goals

- No route restructuring.
- No data model changes.
- No new charting library.
- No full design system extraction into a separate package.

---

### Task 1: Reset Global Visual Tokens

**Files:**
- Modify: `frontend/src/styles/global.css`
- Review reference: `frontend/src/styles/theme.ts`
- Review reference: `frontend/src/styles/marketStyle.ts`

**Step 1: Redefine core color tokens**

- Replace the current purple-heavy brand core with a more product-specific palette.
- Keep `--color-up` / `--color-down` reserved for market semantics only.
- Introduce stronger neutral separation between:
  - `--color-background`
  - `--color-surface`
  - `--color-surface-elevated`
  - `--color-surface-active`
- Reduce the frequency of `--color-primary` as a fill color; prefer it for focus, active navigation, key CTAs, and highlights.

**Step 2: Retune typography scale**

- Increase base readability:
  - `--font-size-sm` from `12px` to a less cramped body-support size
  - `--font-size-md` / `--font-size-lg` to better support dense Chinese UI copy
- Tighten the role of each size:
  - chrome labels
  - card titles
  - section titles
  - headline / hero numbers
- Keep `tnum` usage for financial metrics.

**Step 3: Retune radius and shadow language**

- Reduce the “soft SaaS bubble” feel by tightening radius usage hierarchy:
  - pills remain full radius
  - normal controls use smaller radius
  - major panels use medium radius, not oversized rounding everywhere
- Make shadows rarer but more deliberate.
- Remove card hover behavior that only changes border color without changing hierarchy.

**Step 4: Replace global utility anti-patterns**

- Replace global/component `transition: all` with property-scoped transitions.
- Ensure hover, focus, and pressed states are visually distinct.
- Keep reduced-motion compatibility intact.

**Step 5: Verify token pass**

Run:

```bash
npm test -- --runInBand
```

Expected:

- Existing frontend tests stay green after token-only adjustments.
- No unreadable contrast regressions in dark/light themes.

**Step 6: Commit**

```bash
git add frontend/src/styles/global.css
git commit -m "feat: refresh global visual tokens for ui polish"
```

---

### Task 2: Rebuild App Shell Hierarchy

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/components/TopNav.vue`
- Modify: `frontend/src/components/SideNav.vue`
- Test: `frontend/src/components/TopNav.test.ts`
- Test: `frontend/src/components/SideNav.test.ts`

**Step 1: Strengthen shell composition**

- Make sidebar, top bar, and page canvas feel like one system.
- Use one consistent shell background strategy:
  - sidebar = product rail
  - top nav = thin control plane
  - main canvas = content field
- Avoid three unrelated surface tones.

**Step 2: Simplify top navigation**

- Reduce default “pill tab row” feel.
- Make active navigation clearer through:
  - stronger active indicator
  - clearer typography contrast
  - less decorative rounded-fill everywhere
- Refine search box into a more premium command/search affordance.
- Improve icon button grouping so buttons feel intentional rather than floating circles.

**Step 3: Normalize sidebar behavior**

- Make active item more structural, not just tinted.
- Tone down subscription badge color chaos:
  - align all plan tiers to one family
  - differentiate by intensity/material, not unrelated hues
- Improve logo block so brand feels deliberate.

**Step 4: Improve responsive chrome**

- Ensure mobile overlay, sidebar slide-in, and top bar spacing feel cohesive.
- Check tap-target sizing and visual density on <= `768px`.

**Step 5: Update tests**

- Adjust assertions in `TopNav.test.ts` and `SideNav.test.ts` only if visual markup changes break selectors.
- Preserve current behavior coverage for toggles, user actions, and active navigation.

**Step 6: Run focused tests**

Run:

```bash
npm test -- src/components/TopNav.test.ts src/components/SideNav.test.ts
```

Expected:

- PASS for shell interaction tests.

**Step 7: Commit**

```bash
git add frontend/src/App.vue frontend/src/components/TopNav.vue frontend/src/components/SideNav.vue frontend/src/components/TopNav.test.ts frontend/src/components/SideNav.test.ts
git commit -m "feat: rebuild app shell visual hierarchy"
```

---

### Task 3: Redesign Dashboard as Primary Command Surface

**Files:**
- Modify: `frontend/src/views/DashboardView.vue`
- Modify: `frontend/src/components/BacktestCard.vue`
- Modify: `frontend/src/components/ProgressCard.vue`
- Modify: `frontend/src/components/RecentList.vue`
- Modify: `frontend/src/components/ForumMiniCard.vue`
- Modify: `frontend/src/components/UpgradeCard.vue`
- Test: `frontend/src/views/DashboardView.test.ts`
- Test: `frontend/src/components/BacktestCard.test.ts`
- Test: `frontend/src/components/RecentList.test.ts`
- Test: `frontend/src/components/ForumMiniCard.test.ts`
- Test: `frontend/src/components/UpgradeCard.test.ts`

**Step 1: Recompose dashboard page header**

- Turn current header into a stronger entry point:
  - greeting/title
  - compact status summary
  - primary action
- Make this area feel like an operator console, not a standard page title.

**Step 2: Rebuild KPI row**

- Give KPI cards clearer rank:
  - primary PnL / total return
  - active automation/runtime
  - strategy count / backtest count as supporting metrics
- Add stronger metric typography and subtler labels.
- Avoid four visually identical cards.

**Step 3: Elevate backtest card to hero module**

- Treat `BacktestCard.vue` as dashboard centerpiece.
- Improve internal hierarchy:
  - card header
  - current run context
  - KPI strip
  - chart zone
  - secondary stats
- Make export/refresh/data-source controls feel integrated, not bolted on.

**Step 4: Tighten support cards**

- `ProgressCard.vue`: reduce decorative gradients, improve quota/runtime readability, make progress blocks feel data-driven.
- `RecentList.vue`: improve scanability, row states, and action priority.
- `ForumMiniCard.vue`: reduce “social card” toy feel; make it read as community intelligence feed.
- `UpgradeCard.vue`: align upsell styling with the new premium system, not old template accenting.

**Step 5: Normalize dashboard spacing**

- Align `DashboardView.vue` width with the shared container strategy.
- Remove page-specific max-width mismatch that makes pages feel inconsistent.

**Step 6: Update tests**

- Preserve dashboard loading/error/render coverage.
- Update selectors only where markup hierarchy changes.

**Step 7: Run focused tests**

Run:

```bash
npm test -- src/views/DashboardView.test.ts src/components/BacktestCard.test.ts src/components/RecentList.test.ts src/components/ForumMiniCard.test.ts src/components/UpgradeCard.test.ts
```

Expected:

- PASS for dashboard surface regressions.

**Step 8: Commit**

```bash
git add frontend/src/views/DashboardView.vue frontend/src/components/BacktestCard.vue frontend/src/components/ProgressCard.vue frontend/src/components/RecentList.vue frontend/src/components/ForumMiniCard.vue frontend/src/components/UpgradeCard.vue frontend/src/views/DashboardView.test.ts frontend/src/components/BacktestCard.test.ts frontend/src/components/RecentList.test.ts frontend/src/components/ForumMiniCard.test.ts frontend/src/components/UpgradeCard.test.ts
git commit -m "feat: redesign dashboard as primary quant workspace"
```

---

### Task 4: Rebuild Marketplace Discovery Experience

**Files:**
- Modify: `frontend/src/views/Marketplace.vue`
- Modify: `frontend/src/components/strategy/StrategyCard.vue`
- Modify: `frontend/src/components/strategy/FeaturedStrategyCard.vue`
- Modify: `frontend/src/components/strategy/VerifiedBadge.vue`
- Test: `frontend/src/views/Marketplace.test.ts`
- Test: `frontend/src/components/strategy/StrategyCard.test.ts`
- Test: `frontend/src/components/strategy/FeaturedStrategyCard.test.ts`

**Step 1: Rework marketplace toolbar**

- Upgrade search + filter area into a proper discovery console.
- Clarify filter grouping:
  - category filters
  - quality/risk filters
  - reset state
- Make active filters easier to parse at a glance.

**Step 2: Rebuild featured strip**

- Make featured strategies feel curated, not just larger cards in a row.
- Improve information contrast:
  - category kicker
  - title
  - short thesis
  - core metrics
  - author credibility

**Step 3: Rebuild strategy cards**

- Replace generic card hover uplift with stronger content hierarchy.
- Improve metric blocks so annual return / drawdown / Sharpe are legible in one scan.
- Improve author + CTA footer relationship.
- Reduce decorative top gradient line if it feels template-like after redesign.

**Step 4: Refine credibility markers**

- `VerifiedBadge.vue` should feel like a quality signal, not sticker decoration.
- Align badge language with the new brand palette.

**Step 5: Improve empty/loading/pagination polish**

- Empty states should feel designed, not placeholder text in a dashed box.
- Pagination should visually belong to the page.

**Step 6: Update tests**

- Preserve search, filter, empty state, and CTA behavior checks.
- Update selectors if structure changes.

**Step 7: Run focused tests**

Run:

```bash
npm test -- src/views/Marketplace.test.ts src/components/strategy/StrategyCard.test.ts src/components/strategy/FeaturedStrategyCard.test.ts
```

Expected:

- PASS for marketplace discovery flows.

**Step 8: Commit**

```bash
git add frontend/src/views/Marketplace.vue frontend/src/components/strategy/StrategyCard.vue frontend/src/components/strategy/FeaturedStrategyCard.vue frontend/src/components/strategy/VerifiedBadge.vue frontend/src/views/Marketplace.test.ts frontend/src/components/strategy/StrategyCard.test.ts frontend/src/components/strategy/FeaturedStrategyCard.test.ts
git commit -m "feat: rebuild marketplace discovery ui"
```

---

### Task 5: Motion, States, and Accessibility Polish

**Files:**
- Modify: `frontend/src/styles/global.css`
- Modify: `frontend/src/components/TopNav.vue`
- Modify: `frontend/src/components/BacktestCard.vue`
- Modify: `frontend/src/components/ProgressCard.vue`
- Modify: `frontend/src/components/ForumMiniCard.vue`
- Modify: `frontend/src/components/strategy/StrategyCard.vue`
- Review: `frontend/index.html`

**Step 1: Remove motion anti-patterns**

- Replace `transition: all` with explicit property lists.
- Ensure large hover transforms are used sparingly.
- Add subtle entrance/stagger only where it improves orientation.

**Step 2: Improve focus and keyboard affordances**

- Ensure all clickable controls have visible focus states that fit the new visual system.
- Verify contrast and shape change for hover vs focus vs active.

**Step 3: Improve content accessibility**

- Check readable line lengths.
- Avoid oversmall muted copy for labels and metadata.
- Ensure text truncation does not hide critical financial data.

**Step 4: Optional semantic polish**

- If current markup is too generic, upgrade with better landmarks and labels:
  - stronger `header` / `nav` / `section` semantics
  - useful button labels
  - clearer list semantics for rows/cards

**Step 5: Verify visual behavior**

Run:

```bash
npm test -- --runInBand
```

Expected:

- PASS across frontend tests.
- No focus regression.
- No reduced-motion regression.

**Step 6: Commit**

```bash
git add frontend/src/styles/global.css frontend/src/components/TopNav.vue frontend/src/components/BacktestCard.vue frontend/src/components/ProgressCard.vue frontend/src/components/ForumMiniCard.vue frontend/src/components/strategy/StrategyCard.vue frontend/index.html
git commit -m "feat: polish motion and accessibility states"
```

---

### Task 6: Final Verification and Visual QA

**Files:**
- Review: `frontend/src/App.vue`
- Review: `frontend/src/views/DashboardView.vue`
- Review: `frontend/src/views/Marketplace.vue`
- Review: `frontend/src/components/TopNav.vue`
- Review: `frontend/src/components/SideNav.vue`
- Review: `frontend/src/components/BacktestCard.vue`
- Review: `frontend/src/components/strategy/StrategyCard.vue`

**Step 1: Run full frontend test suite**

Run:

```bash
npm test
```

Expected:

- PASS across all frontend tests.

**Step 2: Run production build**

Run:

```bash
npm run build
```

Expected:

- Successful Vite build with no type errors.

**Step 3: Manual QA checklist**

- Check dark mode first, then light mode.
- Check widths:
  - desktop
  - tablet
  - mobile
- Verify:
  - shell hierarchy feels unified
  - dashboard reads as primary workspace
  - marketplace feels curated and premium
  - financial metrics remain clear
  - market up/down colors still respect user market-style preference

**Step 4: Final commit**

```bash
git add frontend
git commit -m "feat: complete qyquant ui polish pass"
```

---

## Execution Notes

- Start with token reset, not page-by-page patching. Otherwise the visual language will drift.
- Avoid introducing new purple-first accents during implementation.
- Prefer deleting weak decoration over adding more decoration.
- If a component cannot be made distinctive without changing structure, change structure.
- Keep selectors stable where possible to minimize test churn.

## Suggested Order of Review

1. `frontend/src/styles/global.css`
2. `frontend/src/components/TopNav.vue`
3. `frontend/src/components/SideNav.vue`
4. `frontend/src/views/DashboardView.vue`
5. `frontend/src/components/BacktestCard.vue`
6. `frontend/src/views/Marketplace.vue`
7. `frontend/src/components/strategy/StrategyCard.vue`

Plan complete and saved to `docs/plans/2026-04-14-ui-polish-implementation-plan.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?

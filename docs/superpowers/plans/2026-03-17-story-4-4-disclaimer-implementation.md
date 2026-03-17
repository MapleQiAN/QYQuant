# Story 4.4 Disclaimer Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement story 4.4 with centralized disclaimer content, reusable disclaimer components, and active integration on the backtest result page.

**Architecture:** Keep legal copy centralized in a small data module, build four focused UI components under a dedicated `disclaimer/` directory, and integrate only the backtest-result footer plus `StatCard` disclaimer prewiring in this story. Reuse existing project patterns for lightweight tooltips, inline SVGs, and scoped component tests.

**Tech Stack:** Vue 3, TypeScript, `<script setup>`, Vitest, Vue Test Utils

---

## Chunk 1: Data and Component Tests

### Task 1: Add failing tests for disclaimer content and footer

**Files:**
- Create: `frontend/src/data/disclaimer-content.test.ts`
- Create: `frontend/src/components/disclaimer/DisclaimerFooter.test.ts`
- Reference: `frontend/src/components/help/MetricTooltip.test.ts`

- [ ] **Step 1: Write the failing data test**
- [ ] **Step 2: Run `npm test -- disclaimer-content.test.ts` from `frontend/` and verify failure**
- [ ] **Step 3: Write the failing footer rendering test**
- [ ] **Step 4: Run `npm test -- DisclaimerFooter.test.ts` from `frontend/` and verify failure**

### Task 2: Add failing tests for tooltip, registration, and modal components

**Files:**
- Create: `frontend/src/components/disclaimer/DisclaimerTooltip.test.ts`
- Create: `frontend/src/components/disclaimer/RegistrationDisclaimer.test.ts`
- Create: `frontend/src/components/disclaimer/SimulationDisclaimerModal.test.ts`
- Reference: `frontend/src/views/SettingsView.test.ts`

- [ ] **Step 1: Write the failing tooltip delay and aria tests**
- [ ] **Step 2: Run `npm test -- DisclaimerTooltip.test.ts` and verify failure**
- [ ] **Step 3: Write the failing registration v-model and link tests**
- [ ] **Step 4: Run `npm test -- RegistrationDisclaimer.test.ts` and verify failure**
- [ ] **Step 5: Write the failing modal interaction and focus tests**
- [ ] **Step 6: Run `npm test -- SimulationDisclaimerModal.test.ts` and verify failure**

## Chunk 2: Minimal Production Implementation

### Task 3: Add centralized disclaimer data

**Files:**
- Create: `frontend/src/data/disclaimer-content.ts`
- Test: `frontend/src/data/disclaimer-content.test.ts`

- [ ] **Step 1: Add `DisclaimerType` and four disclaimer string constants**
- [ ] **Step 2: Export a typed map and lookup helper if useful**
- [ ] **Step 3: Run `npm test -- disclaimer-content.test.ts` and verify pass**

### Task 4: Implement disclaimer components

**Files:**
- Create: `frontend/src/components/disclaimer/DisclaimerFooter.vue`
- Create: `frontend/src/components/disclaimer/DisclaimerTooltip.vue`
- Create: `frontend/src/components/disclaimer/RegistrationDisclaimer.vue`
- Create: `frontend/src/components/disclaimer/SimulationDisclaimerModal.vue`
- Test: `frontend/src/components/disclaimer/DisclaimerFooter.test.ts`
- Test: `frontend/src/components/disclaimer/DisclaimerTooltip.test.ts`
- Test: `frontend/src/components/disclaimer/RegistrationDisclaimer.test.ts`
- Test: `frontend/src/components/disclaimer/SimulationDisclaimerModal.test.ts`

- [ ] **Step 1: Implement `DisclaimerFooter.vue` with constant DOM rendering and muted styling**
- [ ] **Step 2: Implement `DisclaimerTooltip.vue` with delayed desktop hover, mobile click, and inline SVG trigger**
- [ ] **Step 3: Implement `RegistrationDisclaimer.vue` with `v-model` support and placeholder agreement links**
- [ ] **Step 4: Implement `SimulationDisclaimerModal.vue` with teleport, checkbox-gated confirm, localStorage persistence helpers, and focus management**
- [ ] **Step 5: Run the four component test files and verify pass**

### Task 5: Integrate active story behavior into existing views/components

**Files:**
- Modify: `frontend/src/components/StatCard.vue`
- Modify: `frontend/src/views/BacktestResultView.vue`
- Modify: `frontend/src/views/BacktestResultView.test.ts`

- [ ] **Step 1: Add a failing backtest view assertion for footer disclaimer and earnings disclaimer triggers**
- [ ] **Step 2: Run `npm test -- BacktestResultView.test.ts` and verify failure**
- [ ] **Step 3: Extend `StatCard.vue` with `showDisclaimer` and render `DisclaimerTooltip` next to the label when enabled**
- [ ] **Step 4: Update `BacktestResultView.vue` to use `StatCard` for relevant earnings metrics or minimally wire `showDisclaimer` into current stat rendering without changing unrelated behavior**
- [ ] **Step 5: Replace the existing dynamic disclaimer card with the fixed footer disclaimer component**
- [ ] **Step 6: Run `npm test -- BacktestResultView.test.ts` and verify pass**

## Chunk 3: Story Verification

### Task 6: Run focused verification for story 4.4

**Files:**
- Test: `frontend/src/data/disclaimer-content.test.ts`
- Test: `frontend/src/components/disclaimer/DisclaimerFooter.test.ts`
- Test: `frontend/src/components/disclaimer/DisclaimerTooltip.test.ts`
- Test: `frontend/src/components/disclaimer/RegistrationDisclaimer.test.ts`
- Test: `frontend/src/components/disclaimer/SimulationDisclaimerModal.test.ts`
- Test: `frontend/src/views/BacktestResultView.test.ts`

- [ ] **Step 1: Run `npm test -- disclaimer-content.test.ts DisclaimerFooter.test.ts DisclaimerTooltip.test.ts RegistrationDisclaimer.test.ts SimulationDisclaimerModal.test.ts BacktestResultView.test.ts` from `frontend/`**
- [ ] **Step 2: Run `npm run build` from `frontend/`**
- [ ] **Step 3: Recheck acceptance criteria against shipped behavior**
- [ ] **Step 4: Update story notes if implementation details diverged**

Plan complete and saved to `docs/superpowers/plans/2026-03-17-story-4-4-disclaimer-implementation.md`. Ready to execute?

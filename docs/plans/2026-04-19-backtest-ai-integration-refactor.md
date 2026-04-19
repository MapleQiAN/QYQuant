# Backtest AI Integration Refactor

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform the AI Agent from an isolated bottom panel into an integrated intelligent layer embedded throughout the backtest report, with an opt-in toggle at backtest submission time.

**Architecture:** Right sidebar (340px) Chat replaces bottom ChatPanel. AI content (summary, diagnosis, alerts, comparison) merges into MetricsPanel and ChartPanel instead of 4 standalone blocks. MetricCard gets always-visible AI caption. ChartPanel gets embedded AI narration. Context-aware Chat via provide/inject reactive context. Backend gates AI report generation on `enable_ai` param.

**Tech Stack:** Vue 3 Composition API, TypeScript, Flask, Celery, provide/inject for context

---

## Phase 1: Backend — enable_ai Gate

### Task 1.1: Accept `enable_ai` in API payloads

**Files:**
- Modify: `backend/app/blueprints/backtests.py:89-104` (`_build_v1_job_params`)
- Modify: `backend/app/blueprints/backtests.py:145-195` (`run`)
- Modify: `backend/app/blueprints/backtests.py:438-480` (`submit_backtest`)

**Step 1: Add `enable_ai` to `_build_v1_job_params`**

In `_build_v1_job_params` at line 89, append to the returned dict:

```python
def _build_v1_job_params(payload):
    symbols = payload.get("symbols") or []
    parameters = payload.get("parameters") or {}
    return {
        "name": payload.get("name"),
        "symbol": symbols[0] if symbols else None,
        "symbols": symbols,
        "start_date": payload.get("start_date"),
        "end_date": payload.get("end_date"),
        "start_time": payload.get("start_date"),
        "end_time": payload.get("end_date"),
        "data_source": payload.get("data_source", payload.get("dataSource", payload.get("provider"))),
        "strategy_id": payload.get("strategy_id"),
        "strategy_params": parameters,
        "parameters": parameters,
        "enable_ai": payload.get("enable_ai", True),
    }
```

**Step 2: Add `enable_ai` to `run` endpoint**

In `run()` at line 176, add to the params dict:

```python
params = {
    "symbol": symbol,
    "interval": interval,
    "limit": limit,
    "start_time": start_time,
    "end_time": end_time,
    "strategy_id": strategy_id,
    "strategy_version": strategy_version,
    "strategy_params": strategy_params,
    "data_source": data_source,
    "enable_ai": payload.get("enableAi", payload.get("enable_ai", True)),
}
```

**Step 3: No change needed in `submit_backtest`** — it calls `_build_v1_job_params` which now includes `enable_ai`.

**Step 4: Commit**

```bash
git add backend/app/blueprints/backtests.py
git commit -m "feat: accept enable_ai param in backtest submission endpoints"
```

---

### Task 1.2: Gate AI report generation on `enable_ai`

**Files:**
- Modify: `backend/app/tasks/backtests.py:111-114` (`_run_job`)

**Step 1: Add conditional check before triggering AI report**

In `_run_job` at line 111, change:

```python
# Before
if job.user_id:
    from .report_generation import generate_backtest_report
    generate_backtest_report.delay(job.id, job.user_id)

# After
if job.user_id and params.get("enable_ai", True):
    from .report_generation import generate_backtest_report
    generate_backtest_report.delay(job.id, job.user_id)
```

**Step 2: Verify**

Confirm the logic: `enable_ai` defaults to `True` so existing backtests still generate AI reports. Only explicit `enable_ai: false` skips.

**Step 3: Commit**

```bash
git add backend/app/tasks/backtests.py
git commit -m "feat: gate AI report generation on enable_ai param"
```

---

### Task 1.3: Add `enable_ai` to frontend types and API

**Files:**
- Modify: `frontend/src/types/Backtest.ts:69-77` (`SubmitBacktestPayload`)
- Modify: `frontend/src/types/Backtest.ts:51-58` (`RunBacktestPayload`)

**Step 1: Add `enable_ai` to both payload interfaces**

```typescript
// SubmitBacktestPayload (line 69)
export interface SubmitBacktestPayload {
  strategy_id: string
  symbols: string[]
  start_date: string
  end_date: string
  data_source?: string
  name?: string
  parameters?: Record<string, unknown>
  enable_ai?: boolean
}

// RunBacktestPayload (line 51)
export interface RunBacktestPayload {
  symbol: string
  interval?: string
  limit?: number
  strategyId?: string
  strategyVersion?: string
  strategyParams?: Record<string, unknown>
  enableAi?: boolean
}
```

**Step 2: Commit**

```bash
git add frontend/src/types/Backtest.ts
git commit -m "feat: add enable_ai to backtest payload types"
```

---

## Phase 2: Layout Skeleton — Right Sidebar

### Task 2.1: Create `ChatSidebar.vue` from `ChatPanel.vue`

**Files:**
- Create: `frontend/src/views/backtest/report/ChatSidebar.vue`
- Reference: `frontend/src/views/backtest/report/ChatPanel.vue` (existing, to be replaced)

**Step 1: Create ChatSidebar.vue**

```vue
<template>
  <aside v-if="enabled" :class="['chat-sidebar', { 'chat-sidebar--collapsed': collapsed }]">
    <div class="chat-sidebar__toggle" @click="collapsed = !collapsed">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    </div>

    <template v-if="!collapsed">
      <div class="chat-sidebar__header">
        <span class="chat-sidebar__eyebrow">AI</span>
        <h3 class="chat-sidebar__title">{{ $t('backtestReport.chatTitle') }}</h3>
        <p v-if="contextHint" class="chat-sidebar__context">
          {{ contextHint }}
          <button class="chat-sidebar__context-clear" @click="$emit('clear-context')">&times;</button>
        </p>
      </div>

      <div ref="messagesRef" class="chat-sidebar__messages">
        <article v-for="message in messages" :key="message.id" :class="['chat-message', `chat-message--${message.role}`]">
          <strong>{{ message.role === 'user' ? 'You' : 'AI' }}</strong>
          <p>{{ message.message }}</p>
        </article>
      </div>

      <form class="chat-sidebar__form" @submit.prevent="sendMessage">
        <input
          v-model="draft"
          class="chat-sidebar__input"
          data-test="chat-input"
          :disabled="loading"
          :placeholder="$t('backtestReport.chatPlaceholder')"
        />
        <button class="btn btn-primary" data-test="chat-send" type="submit" :disabled="!canSend">
          {{ loading ? '...' : $t('backtestReport.chatSend') }}
        </button>
      </form>
    </template>
  </aside>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { fetchReportChatHistory, sendReportChatMessage } from '../../../api/reports'
import type { BacktestAiChatMessage } from '../../../types/Backtest'

const props = defineProps<{
  reportId: string
  enabled: boolean
  contextHint?: string
}>()

defineEmits<{ 'clear-context': [] }>()

const draft = ref('')
const loading = ref(false)
const collapsed = ref(false)
const messages = ref<BacktestAiChatMessage[]>([])
const messagesRef = ref<HTMLElement | null>(null)

const canSend = computed(() => !loading.value && draft.value.trim().length > 0)

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

async function loadHistory() {
  if (!props.reportId) return
  try {
    const response = await fetchReportChatHistory(props.reportId)
    messages.value = response.messages
    scrollToBottom()
  } catch {
    messages.value = []
  }
}

async function sendMessage() {
  if (!canSend.value) return
  const message = draft.value.trim()
  draft.value = ''
  loading.value = true
  try {
    messages.value = [
      ...messages.value,
      { id: `local-${Date.now()}`, role: 'user', message },
    ]
    scrollToBottom()
    const answer = await sendReportChatMessage(props.reportId, message)
    messages.value = [...messages.value, answer]
    scrollToBottom()
  } finally {
    loading.value = false
  }
}

watch(() => props.reportId, () => { void loadHistory() })
onMounted(() => { void loadHistory() })
</script>

<style scoped>
.chat-sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  border-left: 2px solid var(--color-border);
  background: var(--color-surface);
  overflow: hidden;
}

.chat-sidebar--collapsed {
  grid-template-rows: auto;
}

.chat-sidebar__toggle {
  display: flex;
  justify-content: flex-end;
  padding: var(--spacing-xs);
  cursor: pointer;
  color: var(--color-text-muted);
}

.chat-sidebar__toggle:hover {
  color: var(--color-primary);
}

.chat-sidebar__header {
  display: grid;
  gap: 4px;
}

.chat-sidebar__eyebrow {
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.chat-sidebar__title {
  margin: 0;
  font-size: var(--font-size-md);
}

.chat-sidebar__context {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  background: var(--color-surface-elevated);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.chat-sidebar__context-clear {
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: var(--font-size-md);
  line-height: 1;
  padding: 0 4px;
}

.chat-sidebar__messages {
  overflow-y: auto;
  display: grid;
  gap: var(--spacing-sm);
  align-content: start;
}

.chat-message {
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-light);
  background: var(--color-surface-elevated);
}

.chat-message--assistant {
  border-color: color-mix(in srgb, var(--color-primary) 40%, var(--color-border));
}

.chat-message p {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.chat-message strong {
  font-size: var(--font-size-xs);
}

.chat-sidebar__form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--spacing-xs);
}

.chat-sidebar__input {
  min-width: 0;
  padding: 8px 10px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}

@media (max-width: 768px) {
  .chat-sidebar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 50vh;
    border-left: none;
    border-top: 2px solid var(--color-border);
    z-index: 100;
  }
}
</style>
```

**Step 2: Commit**

```bash
git add frontend/src/views/backtest/report/ChatSidebar.vue
git commit -m "feat: create ChatSidebar component (right sidebar layout)"
```

---

### Task 2.2: Convert `BacktestResultView.vue` to grid layout with sidebar

**Files:**
- Modify: `frontend/src/views/BacktestResultView.vue` (template + script + style)

**Step 1: Update imports**

Replace `ChatPanel` import with `ChatSidebar`:

```typescript
// In imports section (around line 133)
// Remove:
import ChatPanel from './backtest/report/ChatPanel.vue'
// Add:
import ChatSidebar from './backtest/report/ChatSidebar.vue'
```

**Step 2: Add provide for AI context**

After `const exportRoot = ref<HTMLElement | null>(null)` (line 165), add:

```typescript
import { provide, reactive } from 'vue'

const aiContext = reactive({
  activeSection: 'metrics' as 'metrics' | 'charts' | 'params',
  focusedMetric: null as string | null,
  focusedChartRange: null as { start: number; end: number } | null,
})

provide('aiContext', aiContext)

const contextHint = computed(() => {
  if (aiContext.focusedMetric) {
    return `${t('backtestReport.contextMetric')}: ${aiContext.focusedMetric}`
  }
  if (aiContext.focusedChartRange) {
    return t('backtestReport.contextChartRange')
  }
  return ''
})
```

**Step 3: Update template**

Replace the `<template v-else-if="report">` section. Change the `ChatPanel` usage (line 83-87) to `ChatSidebar` outside the container:

```html
<template v-else-if="report">
  <!-- ... guided success, error display unchanged ... -->

  <template v-else>
    <div class="report-layout">
      <div class="report-body">
        <!-- MetricsPanel, ChartPanel, etc. stay here (no ChatPanel) -->
        <MetricsPanel ... />
        <AISummaryPanel ... />      <!-- Phase 3 will merge these -->
        <DiagnosisPanel ... />
        <ComparisonPanel ... />
        <AlertsPanel ... />
        <section class="support-grid">...</section>
        <ChartPanel ... />
        <DisclaimerFooter />
      </div>
      <ChatSidebar
        v-if="aiReport?.id"
        :enabled="isReportChatEnabled"
        :report-id="aiReport.id"
        :context-hint="contextHint"
        @clear-context="clearAiContext"
      />
    </div>
  </template>
</template>
```

**Step 4: Add `clearAiContext` function**

```typescript
function clearAiContext() {
  aiContext.focusedMetric = null
  aiContext.focusedChartRange = null
}
```

**Step 5: Add layout styles**

```css
.report-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 0;
}

.report-body {
  min-width: 0;
  display: grid;
  gap: var(--spacing-xl);
}

@media (max-width: 768px) {
  .report-layout {
    grid-template-columns: 1fr;
  }
}
```

**Step 6: Commit**

```bash
git add frontend/src/views/BacktestResultView.vue
git commit -m "feat: convert BacktestResultView to grid layout with ChatSidebar"
```

---

## Phase 3: AI Content Merge

### Task 3.1: Add AI caption styling to `MetricCard.vue`

**Files:**
- Modify: `frontend/src/views/backtest/report/MetricCard.vue:8,66-69`

**Step 1: Update caption element**

Change line 8:

```html
<!-- Before -->
<span class="metric-tile__caption">{{ caption }}</span>

<!-- After -->
<span v-if="caption" :class="['metric-tile__caption', { 'metric-tile__caption--ai': aiCaption }]">
  {{ caption }}
</span>
```

**Step 2: Add `aiCaption` prop**

```typescript
const props = defineProps<{
  label: string
  value: string
  caption: string
  tone: 'positive' | 'negative' | 'warning' | 'neutral'
  metricKey: string
  aiCaption?: boolean
}>()
```

**Step 3: Add AI caption style**

```css
.metric-tile__caption--ai {
  color: var(--color-primary);
  font-style: italic;
  padding-top: 4px;
  border-top: 1px dashed var(--color-border-light);
}
```

**Step 4: Commit**

```bash
git add frontend/src/views/backtest/report/MetricCard.vue
git commit -m "feat: add AI caption variant to MetricCard"
```

---

### Task 3.2: Merge AI content into `MetricsPanel.vue`

**Files:**
- Modify: `frontend/src/views/backtest/report/MetricsPanel.vue`

**Step 1: Add AI-related props**

```typescript
defineProps<{
  // ... existing props unchanged ...
  aiSummary?: string
  diagnosisNarration?: string
  anomalyAlerts?: Array<{ title: string; description: string; severity?: string }>
}>()
```

**Step 2: Add AI summary block after summary-conclusion**

After line 51 (`</article>` closing `.summary-conclusion`), add:

```html
<div v-if="aiSummary" class="ai-summary-block">
  <span class="analysis-panel__eyebrow">AI Insight</span>
  <p class="ai-summary-block__text">{{ aiSummary }}</p>
</div>
```

**Step 3: Add diagnosis block in insights panel**

After the insight rows loop (line 85), add:

```html
<div v-if="diagnosisNarration" class="insight-row tone-warning">
  <span class="insight-row__dot"></span>
  <div class="insight-row__content">
    <strong>{{ $t('backtestReport.aiDiagnosis') }}</strong>
    <p>{{ diagnosisNarration }}</p>
  </div>
</div>
```

**Step 4: Add anomaly alerts after diagnostics**

After the diagnostics panel (line 101), add:

```html
<article v-if="anomalyAlerts && anomalyAlerts.length" class="analysis-panel analysis-panel--alerts" data-test="report-alerts">
  <div class="analysis-panel__header">
    <span class="analysis-panel__eyebrow">{{ $t('backtestReport.alertsTitle') }}</span>
    <h3 class="analysis-panel__title">{{ $t('backtestReport.alertsTitle') }}</h3>
  </div>
  <div class="analysis-panel__body">
    <div v-for="(alert, i) in anomalyAlerts" :key="i" class="insight-row tone-negative">
      <span class="insight-row__dot"></span>
      <div class="insight-row__content">
        <strong>{{ alert.title }}</strong>
        <p>{{ alert.description }}</p>
      </div>
    </div>
  </div>
</article>
```

**Step 5: Add styles**

```css
.ai-summary-block {
  display: grid;
  gap: 8px;
  padding: 18px 24px;
  border-top: 2px solid var(--color-border);
  position: relative;
  z-index: 1;
}

.ai-summary-block__text {
  margin: 0;
  color: var(--color-text-secondary);
  line-height: 1.7;
  font-size: var(--font-size-md);
}

.analysis-panel--alerts .insight-row__dot {
  background: var(--color-negative);
}
```

**Step 6: Commit**

```bash
git add frontend/src/views/backtest/report/MetricsPanel.vue
git commit -m "feat: merge AI summary, diagnosis, and alerts into MetricsPanel"
```

---

### Task 3.3: Merge AI narration and comparison into `ChartPanel.vue`

**Files:**
- Modify: `frontend/src/views/backtest/report/ChartPanel.vue`

**Step 1: Add AI-related props**

```typescript
defineProps<{
  report: BacktestReportResponse
  hasKlineData: boolean
  hasDrawdownData: boolean
  tradeMarkers: TradeMarker[]
  tradeHoldingDurations: Map<number, number>
  cumulativeReturns: number[]
  tradeDistribution: TradeDistribution
  aiChartNarration?: string
  parameterSensitivity?: Array<Record<string, unknown>>
  regimeAnalysis?: Array<Record<string, unknown>>
  monteCarlo?: Record<string, unknown> | null
}>()
```

**Step 2: Add AI narration after each chart section**

After each `.chart-section` closing `</div>`, add:

```html
<div v-if="aiChartNarration" class="chart-ai-narration">
  <p>{{ aiChartNarration }}</p>
</div>
```

**Step 3: Add comparison section before TradeTable**

Before `<TradeTable :trades="report.trades || []" />` (line 44), add:

```html
<section v-if="hasComparisonData" class="chart-comparison">
  <div class="chart-section__header">
    <span class="chart-section__title">{{ $t('backtestReport.comparisonTitle') }}</span>
  </div>
  <div class="chart-comparison__body">
    <div v-if="parameterSensitivity && parameterSensitivity.length" class="comparison-block">
      <h4>Parameter Sensitivity</h4>
      <pre>{{ JSON.stringify(parameterSensitivity, null, 2) }}</pre>
    </div>
    <div v-if="regimeAnalysis && regimeAnalysis.length" class="comparison-block">
      <h4>Regime Analysis</h4>
      <pre>{{ JSON.stringify(regimeAnalysis, null, 2) }}</pre>
    </div>
    <div v-if="monteCarlo && Object.keys(monteCarlo).length" class="comparison-block">
      <h4>Monte Carlo</h4>
      <pre>{{ JSON.stringify(monteCarlo, null, 2) }}</pre>
    </div>
  </div>
</section>
```

**Step 4: Add computed for `hasComparisonData`**

```typescript
import { computed } from 'vue'

const props = defineProps<{ ... }>()

const hasComparisonData = computed(() =>
  (props.parameterSensitivity && props.parameterSensitivity.length > 0)
  || (props.regimeAnalysis && props.regimeAnalysis.length > 0)
  || (props.monteCarlo && Object.keys(props.monteCarlo).length > 0)
)
```

**Step 5: Add styles**

```css
.chart-ai-narration {
  padding: 12px 16px;
  background: var(--color-surface-elevated);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-sm);
  margin-top: -1px;
}

.chart-ai-narration p {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.6;
}

.chart-comparison {
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-md);
}

.chart-comparison__body {
  padding: var(--spacing-md);
  display: grid;
  gap: var(--spacing-md);
}

.comparison-block h4 {
  margin: 0 0 var(--spacing-sm);
  font-size: var(--font-size-sm);
}

.comparison-block pre {
  margin: 0;
  padding: var(--spacing-sm);
  background: var(--color-surface-elevated);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  overflow-x: auto;
}
```

**Step 6: Commit**

```bash
git add frontend/src/views/backtest/report/ChartPanel.vue
git commit -m "feat: merge AI narration and comparison data into ChartPanel"
```

---

### Task 3.4: Wire AI props in `BacktestResultView.vue`

**Files:**
- Modify: `frontend/src/views/BacktestResultView.vue`

**Step 1: Pass AI props to MetricsPanel**

```html
<MetricsPanel
  v-bind="{ ...existing props... }"
  :ai-summary="aiExecutiveSummary"
  :diagnosis-narration="aiDiagnosisNarration"
  :anomaly-alerts="aiAnomalies"
/>
```

**Step 2: Pass AI narration map to MetricCard via MetricsPanel's `detailedMetrics`**

In the computed `detailedMetrics` (search for where it's built), append AI narration as caption:

```typescript
// For each detailedMetric item, check aiMetricNarrations for a matching key
// The existing `caption` field on detailedMetrics items will now pull from aiMetricNarrations
```

Find where `detailedMetrics` is constructed and add AI narration:

```typescript
caption: aiMetricNarrations[metricKey] || existingCaption,
```

Mark these as `aiCaption: true` on MetricCard when AI narration exists.

**Step 3: Pass AI props to ChartPanel**

```html
<ChartPanel
  v-bind="{ ...existing props... }"
  :ai-chart-narration="aiChartNarration"
  :parameter-sensitivity="aiParameterSensitivity"
  :regime-analysis="aiRegimeAnalysis"
  :monte-carlo="aiMonteCarlo"
/>
```

Add `aiChartNarration` computed:

```typescript
const aiChartNarration = computed(() => {
  // Use the equity curve narration if available
  const narrations = aiMetricNarrations.value
  return narrations['equity_curve'] || narrations['chart_overview'] || ''
})
```

**Step 4: Remove standalone AI panel components from template**

Remove these from the template (they're now merged into MetricsPanel/ChartPanel):

```html
<!-- DELETE these -->
<AISummaryPanel ... />
<DiagnosisPanel ... />
<ComparisonPanel ... />
<AlertsPanel ... />
```

**Step 5: Remove unused imports**

```typescript
// Remove these imports
import AISummaryPanel from './backtest/report/AISummaryPanel.vue'
import DiagnosisPanel from './backtest/report/DiagnosisPanel.vue'
import ComparisonPanel from './backtest/report/ComparisonPanel.vue'
import AlertsPanel from './backtest/report/AlertsPanel.vue'
```

**Step 6: Commit**

```bash
git add frontend/src/views/BacktestResultView.vue
git commit -m "feat: wire AI props to MetricsPanel and ChartPanel, remove standalone panels"
```

---

## Phase 4: Context Awareness

### Task 4.1: Add context emit to `MetricCard.vue`

**Files:**
- Modify: `frontend/src/views/backtest/report/MetricCard.vue`

**Step 1: Inject aiContext and emit on click**

```vue
<script setup lang="ts">
import { computed, inject } from 'vue'
import MetricTooltip from '../../../components/help/MetricTooltip.vue'

const props = defineProps<{
  label: string
  value: string
  caption: string
  tone: 'positive' | 'negative' | 'warning' | 'neutral'
  metricKey: string
  aiCaption?: boolean
}>()

const toneClass = computed(() => `tone-${props.tone}`)

const aiContext = inject<{
  focusedMetric: string | null
  activeSection: string
}>('aiContext', { focusedMetric: null, activeSection: 'metrics' })

function handleClick() {
  if (aiContext) {
    aiContext.focusedMetric = props.metricKey
    aiContext.activeSection = 'metrics'
  }
}
</script>

<template>
  <article class="metric-tile" @click="handleClick">
    <!-- ... existing template unchanged ... -->
  </article>
</template>
```

**Step 2: Add cursor style**

```css
.metric-tile {
  cursor: pointer;
}
```

**Step 3: Commit**

```bash
git add frontend/src/views/backtest/report/MetricCard.vue
git commit -m "feat: MetricCard updates aiContext on click"
```

---

### Task 4.2: Add context emit to `ChartPanel.vue`

**Files:**
- Modify: `frontend/src/views/backtest/report/ChartPanel.vue`

**Step 1: Inject aiContext and update on chart interaction**

```typescript
import { inject } from 'vue'

const aiContext = inject<{
  focusedChartRange: { start: number; end: number } | null
  activeSection: string
}>('aiContext', { focusedChartRange: null, activeSection: 'charts' })

function handleChartFocus() {
  if (aiContext) {
    aiContext.activeSection = 'charts'
  }
}
```

**Step 2: Wire into chart sections**

Add `@click="handleChartFocus"` to each `.chart-section` div.

**Step 3: Commit**

```bash
git add frontend/src/views/backtest/report/ChartPanel.vue
git commit -m "feat: ChartPanel updates aiContext on interaction"
```

---

## Phase 5: enable_ai Toggle in Backtest Forms

### Task 5.1: Add toggle to `BacktestsView.vue`

**Files:**
- Modify: `frontend/src/views/BacktestsView.vue`

**Step 1: Add `enableAI` ref**

```typescript
const enableAI = ref(true)
```

**Step 2: Add checkbox in form, before submit button**

```html
<label class="field field--checkbox" v-if="userStore.profile?.plan_level && userStore.profile.plan_level !== 'free'">
  <input type="checkbox" v-model="enableAI" />
  <span>{{ $t('backtests.enableAI') }}</span>
</label>
```

**Step 3: Pass to `submitBacktest` payload**

Find where `submitBacktest(payload)` is called (~line 744) and add `enable_ai`:

```typescript
const payload: SubmitBacktestPayload = {
  // ... existing fields ...
  enable_ai: enableAI.value,
}
```

**Step 4: Commit**

```bash
git add frontend/src/views/BacktestsView.vue
git commit -m "feat: add enable_ai toggle to BacktestsView form"
```

---

### Task 5.2: Add toggle to `StrategyDetailView.vue`

**Files:**
- Modify: `frontend/src/views/StrategyDetailView.vue`

**Step 1: Add `enableAI` ref**

```typescript
const enableAI = ref(true)
```

**Step 2: Add checkbox before submit button**

```html
<label class="field field--checkbox" v-if="userStore.profile?.plan_level && userStore.profile.plan_level !== 'free'">
  <input type="checkbox" v-model="enableAI" />
  <span>{{ $t('backtests.enableAI') }}</span>
</label>
```

**Step 3: Pass to `submitBacktest` payload**

Find where `submitBacktest({...})` is called (~line 330) and add `enable_ai`:

```typescript
const result = await submitBacktest({
  strategy_id: strategyId,
  symbols,
  start_date: runForm.startDate,
  end_date: runForm.endDate,
  data_source: effectiveDataSource.value,
  name: runForm.name || undefined,
  parameters: runForm.parameters,
  enable_ai: enableAI.value,
})
```

**Step 4: Commit**

```bash
git add frontend/src/views/StrategyDetailView.vue
git commit -m "feat: add enable_ai toggle to StrategyDetailView form"
```

---

## Phase 6: Cleanup + i18n

### Task 6.1: Add i18n keys

**Files:**
- Modify: `frontend/src/i18n/messages/en.ts`
- Modify: `frontend/src/i18n/messages/zh.ts`

**Step 1: Add keys**

English:
```typescript
backtestReport: {
  // ... existing ...
  chatTitle: 'Report Q&A',
  chatPlaceholder: 'Ask about this backtest...',
  chatSend: 'Send',
  contextMetric: 'Focused on',
  contextChartRange: 'Viewing chart range',
  aiDiagnosis: 'AI Diagnosis',
  alertsTitle: 'Anomaly Alerts',
  comparisonTitle: 'Advanced Analysis',
}
backtests: {
  // ... existing ...
  enableAI: 'AI Enhanced Report',
}
```

Chinese:
```typescript
backtestReport: {
  // ... existing ...
  chatTitle: '报告问答',
  chatPlaceholder: '围绕本次回测提问...',
  chatSend: '发送',
  contextMetric: '当前关注',
  contextChartRange: '正在查看图表区间',
  aiDiagnosis: 'AI 诊断',
  alertsTitle: '异常告警',
  comparisonTitle: '高级分析',
}
backtests: {
  // ... existing ...
  enableAI: 'AI 增强报告',
}
```

**Step 2: Commit**

```bash
git add frontend/src/i18n/messages/en.ts frontend/src/i18n/messages/zh.ts
git commit -m "feat: add i18n keys for AI integration refactor"
```

---

### Task 6.2: Delete unused standalone AI panels

**Files:**
- Delete: `frontend/src/views/backtest/report/AISummaryPanel.vue`
- Delete: `frontend/src/views/backtest/report/DiagnosisPanel.vue`
- Delete: `frontend/src/views/backtest/report/ComparisonPanel.vue`
- Delete: `frontend/src/views/backtest/report/AlertsPanel.vue`
- Delete: `frontend/src/views/backtest/report/ChatPanel.vue` (replaced by ChatSidebar)

**Step 1: Verify no remaining imports**

```bash
rtk grep -r "AISummaryPanel\|DiagnosisPanel\|ComparisonPanel\|AlertsPanel\|ChatPanel" frontend/src --include="*.vue" --include="*.ts"
```

Expected: no results (all references removed in Task 3.4).

**Step 2: Delete files**

```bash
rm frontend/src/views/backtest/report/AISummaryPanel.vue
rm frontend/src/views/backtest/report/DiagnosisPanel.vue
rm frontend/src/views/backtest/report/ComparisonPanel.vue
rm frontend/src/views/backtest/report/AlertsPanel.vue
rm frontend/src/views/backtest/report/ChatPanel.vue
```

**Step 3: Commit**

```bash
git add -u frontend/src/views/backtest/report/
git commit -m "refactor: delete standalone AI panel components (merged into MetricsPanel/ChartPanel)"
```

---

### Task 6.3: Verify PDF/HTML export excludes sidebar

**Files:**
- Modify: `frontend/src/lib/backtestReportExport.ts` (if needed)

**Step 1: Check export logic**

The export uses `exportRoot` ref which wraps the `<section class="view">`. The ChatSidebar is inside the `.report-layout` grid. Verify that the export captures only `.report-body` or that ChatSidebar has CSS `@media print { display: none; }`.

**Step 2: Add print style to ChatSidebar**

In `ChatSidebar.vue` styles, add:

```css
@media print {
  .chat-sidebar {
    display: none;
  }
}
```

**Step 3: Commit**

```bash
git add frontend/src/views/backtest/report/ChatSidebar.vue
git commit -m "fix: hide ChatSidebar from PDF/HTML export"
```

---

## Summary of Changes

| Phase | Tasks | Key Change |
|-------|-------|-----------|
| 1 | 1.1-1.3 | Backend `enable_ai` gate + frontend types |
| 2 | 2.1-2.2 | ChatSidebar + grid layout |
| 3 | 3.1-3.4 | AI content merge into MetricsPanel/ChartPanel |
| 4 | 4.1-4.2 | Context awareness (provide/inject) |
| 5 | 5.1-5.2 | enable_ai toggle in backtest forms |
| 6 | 6.1-6.3 | i18n + cleanup + export safety |

**Files created:** 1 (`ChatSidebar.vue`)
**Files deleted:** 5 (4 standalone AI panels + old ChatPanel)
**Files modified:** ~12

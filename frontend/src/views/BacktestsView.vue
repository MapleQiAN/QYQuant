<template>
  <section class="view">
    <div class="container">
      <div class="page-header">
        <div class="header-text">
          <p class="eyebrow">{{ $t('backtests.title') }}</p>
          <h1 class="view-title">{{ $t('backtests.runBacktest') }}</h1>
          <p class="view-subtitle">{{ $t('backtests.subtitle') }}</p>
        </div>

        <div v-if="quota" class="quota-widget">
          <div class="quota-widget__top">
            <span class="quota-label">{{ $t('backtests.remainingQuota') }}</span>
            <span class="quota-count">
              <strong class="quota-num">{{ quota.remaining === 'unlimited' ? '∞' : quota.remaining }}</strong>
              <span class="quota-sep">/</span>
              <span>{{ quota.plan_limit === 'unlimited' ? '∞' : quota.plan_limit }}</span>
            </span>
          </div>
          <div v-if="quota.remaining !== 'unlimited' && quota.plan_limit !== 'unlimited'" class="quota-bar">
            <div
              class="quota-bar__fill"
              :style="{ width: `${Math.min(100, (Number(quota.remaining) / Number(quota.plan_limit)) * 100)}%` }"
              :class="{ 'quota-bar__fill--low': Number(quota.remaining) / Number(quota.plan_limit) < 0.2 }"
            ></div>
          </div>
          <span v-if="quota.reset_at" class="quota-reset">
            {{ $t('backtests.resetTime') }}：{{ quota.reset_at.slice(0, 10) }}
          </span>
        </div>
        <p v-else-if="quotaError" class="message error quota-error">{{ quotaError }}</p>
      </div>

      <div class="layout-grid">
        <!-- Left Panel: Config Form -->
        <div class="card panel panel--form">
          <div class="panel-header">
            <span class="panel-header__accent"></span>
            <span class="panel-header__icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
            </span>
            <h3 class="panel-title">{{ $t('backtests.runBacktest') }}</h3>
          </div>

          <div class="form-section">
            <div class="form-section__label">{{ $t('backtests.strategy') }}</div>
            <label class="field">
              <select class="field-input" v-model="runForm.strategyId">
                <option value="">{{ $t('backtests.selectStrategy') }}</option>
                <option v-for="item in strategies" :key="item.id" :value="item.id">
                  {{ item.name }} ({{ item.symbol }})
                </option>
              </select>
            </label>
            <div v-if="strategiesError" class="message error">{{ strategiesError }}</div>

            <label class="field">
              <span class="field-label">{{ $t('backtests.backtestName') }}</span>
              <input
                v-model.trim="runForm.name"
                data-test="backtest-name-input"
                class="field-input"
                type="text"
                :placeholder="suggestedBacktestName"
              />
              <span class="field-help">{{ $t('backtests.backtestNameHelp') }}</span>
            </label>
          </div>

          <div class="form-divider"></div>

          <div class="form-section">
            <div class="form-section__label">{{ $t('backtests.symbol') }}</div>
            <label class="field">
              <input v-model.trim="runForm.symbol" class="field-input" type="text" :placeholder="$t('backtests.symbolPlaceholder')" />
            </label>

            <div class="field-row">
              <label class="field">
                <span class="field-label">{{ $t('backtests.interval') }}</span>
                <input v-model.trim="runForm.interval" class="field-input" type="text" :placeholder="$t('backtests.intervalPlaceholder')" />
              </label>
              <label class="field">
                <span class="field-label">{{ $t('backtests.bars') }}</span>
                <input v-model.number="runForm.limit" class="field-input" type="number" min="10" max="3000" />
              </label>
            </div>

            <div class="field-row">
              <label class="field">
                <span class="field-label">{{ $t('backtests.startDate') }}</span>
                <input v-model="runForm.startDate" class="field-input" type="date" />
              </label>
              <label class="field">
                <span class="field-label">{{ $t('backtests.endDate') }}</span>
                <input v-model="runForm.endDate" class="field-input" type="date" />
              </label>
            </div>
          </div>

          <div v-if="runForm.strategyId" class="runtime-box">
            <div class="runtime-header">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              <span class="runtime-title">{{ $t('backtests.strategyRuntime') }}</span>
              <span v-if="runtimeDescriptor" class="runtime-version-badge">v{{ runtimeDescriptor.strategyVersion }}</span>
            </div>
            <p v-if="runtimeLoading" class="message runtime-loading">
              <span class="loading-dots"><span></span><span></span><span></span></span>
              {{ $t('backtests.loadingParameters') }}
            </p>
            <p v-else-if="runtimeError" class="message error">{{ runtimeError }}</p>
            <template v-else-if="runtimeDescriptor">
              <div v-if="runtimeDescriptor.parameters.length === 0" class="message runtime-empty">
                {{ $t('backtests.noCustomParameters') }}
              </div>

              <div class="runtime-params">
                <label v-for="param in runtimeDescriptor.parameters" :key="param.key" class="field">
                  <span class="field-label field-label--mono">{{ param.key }}</span>

                  <select
                    v-if="param.type === 'enum'"
                    class="field-input"
                    :value="String(paramValues[param.key] ?? '')"
                    @change="onParamInput(param.key, $event)"
                  >
                    <option v-for="option in param.enum || []" :key="String(option)" :value="String(option)">
                      {{ option }}
                    </option>
                  </select>

                  <input
                    v-else-if="param.type === 'boolean'"
                    class="field-checkbox"
                    type="checkbox"
                    :checked="Boolean(paramValues[param.key])"
                    @change="onBooleanParamInput(param.key, $event)"
                  />

                  <input
                    v-else-if="param.type === 'integer' || param.type === 'number'"
                    class="field-input"
                    type="number"
                    :min="param.min"
                    :max="param.max"
                    :step="param.step ?? (param.type === 'integer' ? 1 : 0.01)"
                    :value="paramValues[param.key]"
                    @input="onParamInput(param.key, $event)"
                  />

                  <input
                    v-else
                    class="field-input"
                    type="text"
                    :value="String(paramValues[param.key] ?? '')"
                    @input="onParamInput(param.key, $event)"
                  />

                  <span v-if="param.description" class="field-help">{{ param.description }}</span>
                </label>
              </div>
            </template>
          </div>

          <div class="actions">
            <button
              v-if="!isQuotaExhausted"
              :class="['btn btn-run', { 'btn-run--active': runState.running }]"
              type="button"
              :disabled="runState.running || runtimeLoading"
              @click="handleRun"
            >
              <span v-if="runState.running" class="btn-run__spinner"></span>
              <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              {{ runState.running ? $t('backtests.running') : $t('backtests.runBacktest') }}
            </button>
            <button
              v-else
              class="btn btn-upgrade"
              type="button"
              @click="goToPricing"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87L18.18 21 12 17.27 5.82 21 7 14.14l-5-4.87 6.91-1.01L12 2z"/></svg>
              {{ $t('backtests.upgradeForMore') }}
            </button>
          </div>

          <p v-if="runState.error" class="message error run-error">{{ runState.error }}</p>
        </div>

        <!-- Right Panel: Status Terminal -->
        <div class="card panel panel--status">
          <div class="panel-header">
            <span class="panel-header__accent panel-header__accent--accent"></span>
            <span class="panel-header__icon panel-header__icon--status">
              <span :class="['status-dot', { 'status-dot--active': runState.running, 'status-dot--done': runState.completedJobId }]"></span>
            </span>
            <h3 class="panel-title">{{ $t('backtests.reportStatus') }}</h3>
          </div>

          <div class="terminal">
            <div class="terminal__bar">
              <span class="terminal__dot terminal__dot--red"></span>
              <span class="terminal__dot terminal__dot--yellow"></span>
              <span class="terminal__dot terminal__dot--green"></span>
              <span class="terminal__path">QYQuant / backtest</span>
            </div>
            <div class="terminal__body">
              <div class="terminal__line">
                <span class="terminal__prompt">›</span>
                <span class="terminal__key">{{ $t('backtests.currentState') }}</span>
              </div>
              <div class="terminal__output">
                {{ runState.status || $t('backtests.fillFormHint') }}
                <span v-if="runState.running" class="terminal__cursor">_</span>
              </div>

              <template v-if="runState.jobId">
                <div class="terminal__line terminal__line--gap">
                  <span class="terminal__prompt">›</span>
                  <span class="terminal__key">{{ $t('backtests.jobId') }}</span>
                </div>
                <div class="terminal__output terminal__output--mono">{{ runState.jobId }}</div>
              </template>
            </div>
          </div>

          <div v-if="runState.completedJobId" class="report-ready">
            <div class="report-ready__icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            </div>
            <div class="report-ready__text">
              <strong>{{ $t('backtestReport.backtestCompleted') }}</strong>
              <span>{{ $t('backtestReport.reportReady') }}</span>
            </div>
            <button class="btn btn-report" type="button" @click="openReport(runState.completedJobId)">
              {{ $t('backtests.openReport') }}
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            </button>
          </div>
        </div>
      </div>

      <section class="card history-panel">
        <div class="panel-header">
          <span class="panel-header__accent panel-header__accent--secondary"></span>
          <span class="panel-header__icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v5h5"/><path d="M3.05 13A9 9 0 1 0 6 5.3L3 8"/></svg>
          </span>
          <div class="history-panel__header-copy">
            <h3 class="panel-title">{{ $t('backtests.historyTitle') }}</h3>
            <p class="history-panel__subtitle">{{ $t('backtests.historySubtitle') }}</p>
          </div>
        </div>

        <div class="history-panel__toolbar">
          <input
            v-model.trim="historySearch"
            data-test="backtest-history-search"
            class="field-input history-panel__search"
            type="text"
            :placeholder="$t('backtests.historySearchPlaceholder')"
          />
        </div>

        <div v-if="historyLoading" class="history-panel__empty">{{ $t('backtests.historyLoading') }}</div>
        <div v-else-if="historyError" class="history-panel__empty message error">{{ historyError }}</div>
        <div v-else-if="filteredHistory.length === 0" class="history-panel__empty">
          {{ historySearch ? $t('backtests.historyNoMatch') : $t('backtests.historyEmpty') }}
        </div>
        <div v-else class="history-list">
          <article v-for="item in filteredHistory" :key="item.job_id" class="history-item">
            <div class="history-item__main">
              <div class="history-item__top">
                <strong class="history-item__name">{{ item.name }}</strong>
                <span :class="['history-item__status', `history-item__status--${item.status}`]">{{ item.status }}</span>
              </div>
              <div class="history-item__meta">
                <span>{{ item.strategy_name || $t('backtests.unknownStrategy') }}</span>
                <span>{{ item.symbol || '--' }}</span>
                <span>{{ formatHistoryDate(item.created_at) }}</span>
              </div>
              <div v-if="item.result_summary?.totalReturn !== undefined" class="history-item__summary">
                {{ $t('backtests.historyTotalReturn') }}: {{ formatHistoryPercent(item.result_summary.totalReturn) }}
              </div>
            </div>

            <button
              v-if="item.has_report"
              :data-test="`history-open-report-${item.job_id}`"
              class="btn btn-report history-item__action"
              type="button"
              @click="openReport(item.job_id)"
            >
              {{ $t('backtests.openReport') }}
            </button>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { fetchRecent, fetchRuntimeDescriptor } from '../api/strategies'
import { fetchBacktestHistory, fetchBacktestStatus, getBacktestFailureMessage, submitBacktest } from '../api/backtests'
import { fetchMyQuota, type UserQuotaResponse } from '../api/users'
import type { BacktestHistoryItem, SubmitBacktestPayload } from '../types/Backtest'
import type { Strategy, StrategyParameter, StrategyRuntimeDescriptor } from '../types/Strategy'

const strategies = ref<Strategy[]>([])
const strategiesError = ref('')
const quota = ref<UserQuotaResponse | null>(null)
const quotaError = ref('')
const runtimeDescriptor = ref<StrategyRuntimeDescriptor | null>(null)
const runtimeLoading = ref(false)
const runtimeError = ref('')
const historyItems = ref<BacktestHistoryItem[]>([])
const historyLoading = ref(false)
const historyError = ref('')
const historySearch = ref('')
const router = useRouter()

function formatDateInput(date: Date) {
  return date.toISOString().slice(0, 10)
}

function defaultStartDate() {
  const value = new Date()
  value.setDate(value.getDate() - 30)
  return formatDateInput(value)
}

function defaultEndDate() {
  return formatDateInput(new Date())
}

const runForm = reactive({
  strategyId: '',
  name: '',
  symbol: 'BTCUSDT',
  interval: '1m',
  limit: 120,
  startDate: defaultStartDate(),
  endDate: defaultEndDate(),
})

const runState = reactive({
  running: false,
  status: '',
  error: '',
  jobId: '',
  completedJobId: '',
})

const paramValues = reactive<Record<string, any>>({})

const selectedStrategy = computed(() => {
  return strategies.value.find((item) => item.id === runForm.strategyId) || null
})

const suggestedBacktestName = computed(() => {
  const segments = [
    selectedStrategy.value?.name || undefined,
    runForm.symbol || undefined,
    runForm.startDate && runForm.endDate ? `${runForm.startDate} ~ ${runForm.endDate}` : undefined,
  ].filter(Boolean)

  return segments.join(' / ') || 'My backtest'
})

const filteredHistory = computed(() => {
  const keyword = historySearch.value.trim().toLowerCase()
  if (!keyword) {
    return historyItems.value
  }

  return historyItems.value.filter((item) => {
    return [item.name, item.strategy_name, item.symbol, item.job_id]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(keyword))
  })
})

function defaultParamValue(param: StrategyParameter): unknown {
  if (param.default !== undefined) {
    return param.default
  }
  if (param.type === 'boolean') {
    return false
  }
  if (param.type === 'integer' || param.type === 'number') {
    return 0
  }
  if (param.type === 'enum') {
    return param.enum && param.enum.length > 0 ? param.enum[0] : ''
  }
  return ''
}

function resetParamValues(params: StrategyParameter[]) {
  for (const key of Object.keys(paramValues)) {
    delete paramValues[key]
  }
  for (const param of params) {
    paramValues[param.key] = defaultParamValue(param)
  }
}

function onParamInput(key: string, event: Event) {
  const target = event.target as HTMLInputElement | HTMLSelectElement
  paramValues[key] = target.value
}

function onBooleanParamInput(key: string, event: Event) {
  const target = event.target as HTMLInputElement
  paramValues[key] = target.checked
}

async function loadStrategies() {
  strategiesError.value = ''
  try {
    const recent = await fetchRecent()
    strategies.value = recent
    if (!runForm.strategyId && recent.length > 0) {
      runForm.strategyId = recent[0].id
      runForm.symbol = recent[0].symbol || runForm.symbol
    }
  } catch (error: any) {
    strategiesError.value = error?.message || 'Failed to load strategies'
  }
}

async function loadQuota() {
  quotaError.value = ''
  try {
    quota.value = await fetchMyQuota()
  } catch (error: any) {
    quotaError.value = error?.message || 'Failed to load quota information'
  }
}

async function loadHistory() {
  historyLoading.value = true
  historyError.value = ''
  try {
    const response = await fetchBacktestHistory()
    historyItems.value = response.items
  } catch (error: any) {
    historyError.value = error?.message || 'Failed to load backtest history'
  } finally {
    historyLoading.value = false
  }
}

async function loadRuntime(strategyId: string) {
  runtimeDescriptor.value = null
  runtimeError.value = ''

  if (!strategyId) {
    resetParamValues([])
    return
  }

  runtimeLoading.value = true
  try {
    const descriptor = await fetchRuntimeDescriptor(strategyId)
    runtimeDescriptor.value = descriptor
    resetParamValues(descriptor.parameters)

    const selected = strategies.value.find((item) => item.id === strategyId)
    if (selected?.symbol) {
      runForm.symbol = selected.symbol
    }
  } catch (error: any) {
    runtimeError.value = error?.message || 'Failed to load strategy runtime descriptor'
  } finally {
    runtimeLoading.value = false
  }
}

function buildStrategyParams(parameters: StrategyParameter[]): Record<string, unknown> {
  const result: Record<string, unknown> = {}
  for (const parameter of parameters) {
    const rawValue = paramValues[parameter.key]
    if (parameter.type === 'integer') {
      const parsed = Number.parseInt(String(rawValue), 10)
      result[parameter.key] = Number.isNaN(parsed) ? rawValue : parsed
      continue
    }
    if (parameter.type === 'number') {
      const parsed = Number.parseFloat(String(rawValue))
      result[parameter.key] = Number.isNaN(parsed) ? rawValue : parsed
      continue
    }
    if (parameter.type === 'boolean') {
      result[parameter.key] = Boolean(rawValue)
      continue
    }
    result[parameter.key] = rawValue
  }
  return result
}

function buildBacktestName() {
  return runForm.name.trim() || suggestedBacktestName.value
}

function sleep(ms: number) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms)
  })
}

async function waitJobSuccess(jobId: string): Promise<string> {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    const job = await fetchBacktestStatus(jobId)
    if (job.status === 'completed') {
      return jobId
    }
    if (job.status === 'failed' || job.status === 'timeout') {
      throw new Error(getBacktestFailureMessage(job))
    }
    runState.status = `Task ${job.status}...`
    await sleep(1000)
  }
  throw new Error('Backtest job timeout')
}

function openReport(jobId: string) {
  void router.push({ name: 'backtest-report', params: { jobId } })
}

function goToPricing() {
  void router.push('/pricing')
}

function formatHistoryDate(value?: string | null) {
  if (!value) {
    return '--'
  }
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }
  return parsed.toLocaleString()
}

function formatHistoryPercent(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return '--'
  }
  const prefix = value > 0 ? '+' : ''
  return `${prefix}${value.toFixed(2)}%`
}

const isQuotaExhausted = computed(() => {
  if (!quota.value) {
    return false
  }
  return quota.value.remaining !== 'unlimited' && quota.value.remaining <= 0
})

async function handleRun() {
  runState.error = ''
  runState.status = ''
  runState.running = true
  runState.jobId = ''
  runState.completedJobId = ''

  try {
    if (!runForm.strategyId) {
      throw new Error('Please select a strategy before running a backtest')
    }

    const payload: SubmitBacktestPayload = {
      strategy_id: runForm.strategyId,
      symbols: [runForm.symbol],
      start_date: runForm.startDate,
      end_date: runForm.endDate,
      name: buildBacktestName(),
    }

    if (runtimeDescriptor.value) {
      payload.parameters = buildStrategyParams(runtimeDescriptor.value.parameters)
    }

    runState.status = 'Submitting backtest task...'
    const runResponse = await submitBacktest(payload)
    runState.jobId = runResponse.job_id

    runState.status = `Waiting for result (${runResponse.job_id})...`
    runState.completedJobId = await waitJobSuccess(runResponse.job_id)
    runState.status = 'Backtest completed. Opening report...'
    openReport(runResponse.job_id)
  } catch (error: any) {
    runState.error = error?.message || 'Failed to run backtest'
  } finally {
    if (runState.jobId) {
      await loadHistory()
    }
    runState.running = false
  }
}

watch(
  () => runForm.strategyId,
  (strategyId) => {
    void loadRuntime(strategyId)
  },
)

onMounted(() => {
  void loadStrategies()
  void loadQuota()
  void loadHistory()
})
</script>

<style scoped>
/* ── Animations ── */
@keyframes pulse-ring {
  0% { box-shadow: 0 0 0 0 var(--color-primary-bg); }
  70% { box-shadow: 0 0 0 12px transparent; }
  100% { box-shadow: 0 0 0 0 transparent; }
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(0); opacity: 0.3; }
  40% { transform: scale(1); opacity: 1; }
}
@keyframes status-dot-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.75); }
}
@keyframes slide-up {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes terminal-scan {
  0% { background-position: 0 0; }
  100% { background-position: 0 100%; }
}

/* ── Page Layout ── */
.view {
  width: 100%;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-xl);
  margin-bottom: var(--spacing-xl);
}

.header-text {
  min-width: 0;
}

.eyebrow {
  margin: 0 0 6px;
  font-size: var(--font-size-xs);
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-accent);
}

.view-title {
  margin: 0 0 var(--spacing-xs);
  font-size: var(--font-size-xxl);
  font-weight: 800;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
}

.view-subtitle {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

/* ── Quota Widget — Bauhaus card with accent bar ── */
.quota-widget {
  flex-shrink: 0;
  min-width: 200px;
  padding: 14px 18px;
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  display: flex;
  flex-direction: column;
  gap: 8px;
  position: relative;
  overflow: hidden;
}

.quota-widget::after {
  content: "";
  position: absolute;
  height: 5px;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--color-accent);
}

.quota-widget__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
}

.quota-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.quota-count {
  display: flex;
  align-items: baseline;
  gap: 4px;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  font-family: var(--font-mono);
}

.quota-num {
  font-size: var(--font-size-lg);
  font-weight: 800;
  color: var(--color-accent);
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono);
}

.quota-sep {
  color: var(--color-text-muted);
}

.quota-bar {
  height: 4px;
  background: var(--color-surface-active);
  border-radius: 0;
  overflow: hidden;
}

.quota-bar__fill {
  height: 100%;
  background: var(--color-primary);
  transition: width 0.6s var(--ease-out-expo);
}

.quota-bar__fill--low {
  background: var(--color-danger);
}

.quota-reset {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.quota-error {
  margin-top: var(--spacing-sm);
}

/* ── Grid Layout ── */
.layout-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-lg);
  align-items: start;
}

.history-panel {
  margin-top: var(--spacing-lg);
  padding: 0;
  overflow: hidden;
  position: relative;
}

.history-panel__header-copy {
  display: grid;
  gap: 2px;
}

.history-panel__subtitle {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.history-panel__toolbar {
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 2px solid var(--color-border);
}

.history-panel__search {
  max-width: 360px;
}

.history-panel__empty {
  padding: var(--spacing-lg);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.history-list {
  display: grid;
}

.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 2px solid var(--color-border-light);
  transition: background var(--transition-fast);
}

.history-item:hover {
  background: var(--color-surface-hover);
}

.history-item:first-child {
  border-top: none;
}

.history-item__main {
  min-width: 0;
  display: grid;
  gap: 6px;
}

.history-item__top {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.history-item__name {
  color: var(--color-text-primary);
  font-size: var(--font-size-md);
  font-weight: 700;
}

.history-item__status {
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  border: 2px solid transparent;
}

.history-item__status--completed {
  color: var(--color-success);
  border-color: var(--color-success);
  background: var(--color-success-bg);
}

.history-item__status--failed,
.history-item__status--timeout {
  color: var(--color-danger);
  border-color: var(--color-danger);
  background: var(--color-danger-bg);
}

.history-item__status--pending,
.history-item__status--running {
  color: var(--color-warning);
  border-color: var(--color-warning);
  background: var(--color-warning-bg);
}

.history-item__meta,
.history-item__summary {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.history-item__summary {
  font-family: var(--font-mono);
  font-weight: 500;
}

.history-item__action {
  flex-shrink: 0;
}

/* ── Panel Cards — Bauhaus geometric structure ── */
.panel {
  padding: 0;
  overflow: hidden;
  position: relative;
}

.panel:hover {
  transform: none;
}

.panel::after {
  content: "";
  position: absolute;
  height: 5px;
  bottom: 0;
  left: 0;
  right: 0;
}

.panel--form::after {
  background: var(--color-primary);
}

.panel--status::after {
  background: var(--color-accent);
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 2px solid var(--color-border);
  background: var(--color-surface-elevated);
}

.panel-header__accent {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
  flex-shrink: 0;
}

.panel-header__accent--accent {
  background: var(--color-accent);
}

.panel-header__accent--secondary {
  background: var(--color-secondary);
}

.panel-header__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 2px solid var(--color-border);
  border-radius: 0;
  background: var(--color-surface);
  color: var(--color-primary);
  flex-shrink: 0;
}

.panel-header__icon--status {
  background: transparent;
  border: none;
  width: auto;
  height: auto;
  border-radius: 0;
}

.panel-title {
  margin: 0;
  font-size: var(--font-size-md);
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

/* ── Form Sections ── */
.form-section {
  padding: var(--spacing-md) var(--spacing-lg);
}

.form-section__label {
  font-size: var(--font-size-xs);
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-text-muted);
  margin-bottom: var(--spacing-sm);
}

.form-divider {
  height: 2px;
  background: var(--color-border-light);
  margin: 0 var(--spacing-lg);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: var(--spacing-sm);
}

.field-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-sm);
}

.field-label {
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  font-weight: 600;
}

.field-label--mono {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--color-primary);
}

.field-input {
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 9px 12px;
  background: var(--color-surface);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-family: var(--font-family);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
  width: 100%;
  box-sizing: border-box;
}

.field-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-bg);
}

.field-input:hover:not(:focus) {
  border-color: var(--color-border-strong);
}

.field-checkbox {
  width: 18px;
  height: 18px;
  accent-color: var(--color-accent);
}

.field-help {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  line-height: 1.4;
}

/* ── Runtime Box — Bauhaus inset panel ── */
.runtime-box {
  margin: 0 var(--spacing-lg);
  padding: var(--spacing-md);
  border: 2px solid var(--color-primary);
  border-radius: 0;
  background: var(--color-primary-bg);
  margin-bottom: var(--spacing-md);
  position: relative;
}

.runtime-box::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  width: 5px;
  background: var(--color-primary);
}

.runtime-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: var(--spacing-sm);
  color: var(--color-primary);
}

.runtime-title {
  font-size: var(--font-size-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  flex: 1;
}

.runtime-version-badge {
  padding: 2px 8px;
  border-radius: var(--radius-full);
  background: var(--color-accent-bg);
  color: var(--color-primary);
  font-size: 11px;
  font-family: var(--font-mono);
  font-weight: 700;
  border: 2px solid var(--color-primary-border);
}

.runtime-loading {
  display: flex;
  align-items: center;
  gap: 8px;
}

.runtime-empty {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.runtime-params {
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* ── Loading Dots ── */
.loading-dots {
  display: inline-flex;
  gap: 3px;
}

.loading-dots span {
  width: 5px;
  height: 5px;
  border-radius: 0;
  background: var(--color-primary);
  animation: dot-bounce 1.2s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

/* ── Run Button — Bauhaus accent (yellow) with 2px border ── */
.actions {
  padding: var(--spacing-md) var(--spacing-lg) var(--spacing-lg);
}

.btn-run {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-full);
  background: var(--color-accent);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-weight: 700;
  letter-spacing: 0.03em;
  cursor: pointer;
  transition: all 0.2s;
  width: 100%;
  justify-content: center;
  font-family: var(--font-family);
}

.btn-run:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
  box-shadow: var(--shadow-lg);
}

.btn-run:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-run--active {
  animation: pulse-ring 1.5s infinite;
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

.btn-run__spinner {
  width: 14px;
  height: 14px;
  border: 2px solid var(--color-border-light);
  border-top-color: var(--color-text-primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}

.btn-upgrade {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: 2px solid var(--color-accent);
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--color-accent);
  font-size: var(--font-size-sm);
  font-weight: 700;
  cursor: pointer;
  width: 100%;
  justify-content: center;
  transition: all 0.2s;
  font-family: var(--font-family);
}

.btn-upgrade:hover {
  background: var(--color-accent-bg);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.run-error {
  padding: 0 var(--spacing-lg) var(--spacing-md);
  color: var(--color-danger);
  font-size: var(--font-size-sm);
}

.message {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.message.error {
  color: var(--color-danger);
}

/* ── Status Dot — geometric square ── */
.status-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 0;
  background: var(--color-border-strong);
}

.status-dot--active {
  background: var(--color-accent);
  animation: status-dot-pulse 1s infinite;
}

.status-dot--done {
  background: var(--color-success);
}

/* ── Terminal — Bauhaus light with scan lines ── */
.terminal {
  margin: var(--spacing-md) var(--spacing-lg);
  border: 2px solid var(--color-border);
  border-radius: 0;
  overflow: hidden;
  font-family: var(--font-mono);
  background: var(--color-surface-elevated);
}

.terminal__bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--color-surface);
  border-bottom: 2px solid var(--color-border);
}

.terminal__dot {
  width: 10px;
  height: 10px;
  border-radius: 0;
}

.terminal__dot--red { background: var(--color-danger); }
.terminal__dot--yellow { background: var(--color-accent); }
.terminal__dot--green { background: var(--color-success); }

.terminal__path {
  margin-left: 8px;
  font-size: 11px;
  color: var(--color-text-muted);
  letter-spacing: 0.05em;
}

.terminal__body {
  padding: var(--spacing-md);
  min-height: 120px;
  background: var(--color-surface-elevated);
  background-image: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 23px,
    var(--color-border-light) 23px,
    var(--color-border-light) 24px
  );
}

.terminal__line {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.terminal__line--gap {
  margin-top: var(--spacing-md);
}

.terminal__prompt {
  color: var(--color-primary);
  font-size: 13px;
  font-weight: 700;
}

.terminal__key {
  font-size: 11px;
  color: var(--color-text-muted);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  font-weight: 700;
}

.terminal__output {
  padding: 6px 10px;
  font-size: 12px;
  color: var(--color-text-primary);
  background: var(--color-surface);
  border-left: 3px solid var(--color-primary);
  line-height: 1.5;
}

.terminal__output--mono {
  color: var(--color-primary);
  letter-spacing: 0.05em;
  font-weight: 500;
}

.terminal__cursor {
  animation: blink 1s step-end infinite;
  color: var(--color-accent);
  font-weight: 700;
}

/* ── Report Ready Banner — Bauhaus success card ── */
.report-ready {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin: 0 var(--spacing-lg) var(--spacing-lg);
  padding: var(--spacing-md);
  background: var(--color-success-bg);
  border: 2px solid var(--color-success);
  border-radius: 0;
  animation: slide-up 0.3s var(--ease-out-expo);
}

.report-ready__icon {
  color: var(--color-success);
  flex-shrink: 0;
  display: flex;
}

.report-ready__text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.report-ready__text strong {
  font-size: var(--font-size-sm);
  color: var(--color-success);
}

.report-ready__text span {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.btn-report {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 16px;
  border: 2px solid var(--color-success);
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--color-success);
  font-size: var(--font-size-sm);
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  transition: all var(--transition-fast);
  flex-shrink: 0;
  font-family: var(--font-family);
}

.btn-report:hover {
  background: var(--color-success-bg);
  transform: translateX(2px);
  box-shadow: var(--shadow-sm);
}

/* ── Responsive ── */
@media (max-width: 960px) {
  .layout-grid {
    grid-template-columns: 1fr;
  }

  .page-header {
    flex-direction: column;
  }

  .quota-widget {
    width: 100%;
    min-width: unset;
  }

  .history-item {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>

<template>
  <section class="strategy-detail-view">
    <div class="container">
      <div class="page-header">
        <div class="header-text">
          <p class="eyebrow">策略配置</p>
          <h1 class="page-title">{{ $t('strategyDetail.title') }}</h1>
          <p class="page-subtitle">{{ $t('strategyDetail.subtitle') }}</p>
        </div>
        <RouterLink class="btn btn-secondary" to="/strategies">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
          {{ $t('strategyDetail.backToLibrary') }}
        </RouterLink>
      </div>

      <div v-if="isGuidedMode" class="guided-banner">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg>
        {{ $t('strategyDetail.guidedBanner') }}
      </div>

      <div v-if="isGuidedMode" data-test="guided-next-steps" class="guided-next-steps">
        <div class="guided-next-steps__content">
          <p class="guided-next-steps__eyebrow">{{ $t('strategyDetail.nextStepsTitle') }}</p>
          <h2>{{ nextStepsBody }}</h2>
          <p>{{ $t('strategyDetail.nextStepsRun') }}</p>
        </div>
        <div class="guided-next-steps__actions">
          <RouterLink class="btn btn-secondary" to="/strategies">
            {{ $t('strategyDetail.nextStepsLibrary') }}
          </RouterLink>
          <button class="btn btn-primary" type="button" @click="focusRunButton">
            {{ $t('strategyDetail.nextStepsConfigure') }}
          </button>
        </div>
      </div>

      <div v-if="strategyId" class="strategy-identity">
        <div class="strategy-identity__icon">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
        </div>
        <div class="strategy-identity__info">
          <span class="strategy-identity__id">ID: {{ strategyId }}</span>
        </div>
      </div>

      <div class="layout-grid">
        <!-- Control Card: Backtest Setup -->
        <div class="card panel-card">
          <div class="panel-card__header">
            <div class="panel-card__icon">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
            </div>
            <h3 class="panel-title">{{ $t('strategyDetail.backtestSetup') }}</h3>
          </div>

          <div class="panel-body">
            <div class="field-grid">
              <label class="field field--full">
                <span class="field-label">{{ $t('strategyDetail.symbols') }}</span>
                <input
                  data-test="symbol-input"
                  v-model.trim="runForm.symbols"
                  class="field-input"
                  type="text"
                  :placeholder="$t('strategyDetail.symbolsPlaceholder')"
                />
              </label>
              <label class="field">
                <span class="field-label">{{ $t('strategyDetail.startDate') }}</span>
                <input
                  data-test="start-date-input"
                  v-model="runForm.startDate"
                  class="field-input"
                  type="date"
                />
              </label>
              <label class="field">
                <span class="field-label">{{ $t('strategyDetail.endDate') }}</span>
                <input
                  data-test="end-date-input"
                  v-model="runForm.endDate"
                  class="field-input"
                  type="date"
                />
              </label>
              <label class="field field--full">
                <span class="field-label">{{ $t('strategyDetail.dataSource') }}</span>
                <select
                  data-test="data-source-select"
                  v-model="runForm.dataSource"
                  class="field-input"
                >
                  <option v-for="option in dataSourceOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
                <span v-if="dataSourceHint" class="field-hint">{{ dataSourceHint }}</span>
              </label>
            </div>

            <div class="preset-divider">
              <span>{{ $t('strategy.presets.title') }}</span>
            </div>

            <PresetManager
              :presets="presetsStore.presets"
              :selected-preset-id="selectedPresetId"
              :saving="presetsStore.saving"
              :deleting="presetsStore.deleting"
              @select="handlePresetSelect"
              @save="handlePresetSave"
              @delete="handlePresetDelete"
            />
          </div>
        </div>

        <!-- Form Card: Parameters -->
        <div class="card panel-card">
          <div class="panel-card__header">
            <div class="panel-card__icon">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="10" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="14" y2="21"/></svg>
            </div>
            <h3 class="panel-title">{{ $t('strategyDetail.parameterForm') }}</h3>
          </div>

          <div class="panel-body">
            <div v-if="loading" class="loading-state">
              <div class="loading-state__spinner"></div>
              <span>{{ $t('strategyDetail.loadingParameters') }}</span>
            </div>
            <p v-else-if="loadError" class="message error">{{ loadError }}</p>
            <ParameterForm
              v-else
              v-model="parameterValues"
              :definitions="definitions"
              @validation-change="formValid = $event"
            />
          </div>
        </div>
      </div>

      <!-- Submit Bar -->
      <div class="submit-bar">
        <div class="submit-bar__feedback">
          <p v-if="submitError" class="message error">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            {{ submitError }}
          </p>
          <p v-else-if="submitSuccess" class="message success">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            {{ submitSuccess }}
          </p>
        </div>
        <label v-if="userStore.profile?.plan_level && userStore.profile.plan_level !== 'free'" class="field field--checkbox">
          <input type="checkbox" v-model="enableAI" />
          <span>{{ $t('backtests.enableAI') }}</span>
        </label>
        <button
          data-test="start-backtest"
          :class="['btn btn-run', { 'onboarding-highlight': userStore.onboardingHighlightTarget === 'guided-run-button', 'btn-run--active': submitting }]"
          data-onboarding-target="guided-run-button"
          type="button"
          :disabled="submitting || loading"
          @click="handleSubmit"
        >
          <span v-if="submitting" class="btn-run__spinner"></span>
          <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          {{ submitting ? $t('strategyDetail.submitting') : $t('strategyDetail.startBacktest') }}
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { fetchBacktestStatus, getBacktestFailureMessage, submitBacktest } from '../api/backtests'
import { fetchStrategyParameters } from '../api/strategies'
import ParameterForm from '../components/strategy/ParameterForm.vue'
import PresetManager from '../components/strategy/PresetManager.vue'
import { useUserStore } from '../stores'
import { usePresetsStore } from '../stores/usePresetsStore'
import type { StrategyParameterDefinition } from '../types/Strategy'

const { t, locale } = useI18n()

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const strategyId = String(route.params.strategyId || route.query.strategy_id || '')
const isGuidedMode = route.query.guided === 'true'
const guidedSource = String(route.query.source || '')
const presetsStore = usePresetsStore()

const definitions = ref<StrategyParameterDefinition[]>([])
const parameterValues = ref<Record<string, unknown>>({})
const selectedPresetId = ref('')
const loading = ref(false)
const loadError = ref('')
const submitting = ref(false)
const submitError = ref('')
const submitSuccess = ref('')
const formValid = ref(true)
const enableAI = ref(true)

const runForm = reactive({
  symbols: '',
  startDate: defaultStartDate(),
  endDate: defaultEndDate(),
  dataSource: 'auto',
})

const dataSourceOptions = computed(() => ([
  { value: 'auto', label: t('backtest.dataSourceAuto') },
  { value: 'joinquant', label: t('backtest.dataSourceJoinquant') },
  { value: 'akshare', label: t('backtest.dataSourceAkshare') },
  { value: 'binance', label: t('backtest.dataSourceBinance') },
  { value: 'freegold', label: t('backtest.dataSourceFreegold') },
  { value: 'mock', label: t('backtest.dataSourceMock') },
]))

const primarySymbol = computed(() => {
  const [first] = runForm.symbols
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
  return first || ''
})

const recommendedDataSource = computed(() => inferRecommendedDataSource(primarySymbol.value))
const effectiveDataSource = computed(() =>
  runForm.dataSource === 'auto' ? recommendedDataSource.value : runForm.dataSource
)
const dataSourceHint = computed(() => {
  if (!primarySymbol.value) {
    return ''
  }
  const resolvedLabel = dataSourceOptions.value.find((option) => option.value === effectiveDataSource.value)?.label ?? effectiveDataSource.value
  if (runForm.dataSource === 'auto' && effectiveDataSource.value !== 'auto') {
    return t('strategyDetail.dataSourceAutoResolved', { source: resolvedLabel })
  }
  if (isAshareSymbol(primarySymbol.value)) {
    return t('strategyDetail.dataSourceAshareHint')
  }
  if (isGoldSymbol(primarySymbol.value)) {
    return t('strategyDetail.dataSourceGoldHint')
  }
  return ''
})

const nextStepsBody = computed(() => {
  if (guidedSource === 'template') {
    return t('strategyDetail.nextStepsTemplate')
  }
  if (guidedSource === 'import') {
    return t('strategyDetail.nextStepsImport')
  }
  return t('strategyDetail.nextStepsGeneric')
})

onMounted(() => {
  void loadDetail()
})

async function loadDetail() {
  loading.value = true
  loadError.value = ''
  try {
    const [parameterDefinitions] = await Promise.all([
      fetchStrategyParameters(strategyId),
      presetsStore.loadPresets(strategyId),
    ])
    definitions.value = parameterDefinitions
    parameterValues.value = mergeDefaults(parameterDefinitions, parameterValues.value)
  } catch (error: any) {
    loadError.value = error?.message || t('strategyDetail.loadError')
  } finally {
    loading.value = false
  }
}

function handlePresetSelect(presetId: string) {
  selectedPresetId.value = presetId
  const preset = presetsStore.presets.find((item) => item.id === presetId)
  if (!preset) {
    parameterValues.value = mergeDefaults(definitions.value, {})
    return
  }
  parameterValues.value = mergeDefaults(definitions.value, preset.parameters)
}

async function handlePresetSave(name: string) {
  const preset = await presetsStore.savePreset(strategyId, {
    name,
    parameters: sanitizeParameters(definitions.value, parameterValues.value),
  })
  selectedPresetId.value = preset.id
}

async function handlePresetDelete(presetId: string) {
  await presetsStore.removePreset(strategyId, presetId)
  selectedPresetId.value = ''
}

async function handleSubmit() {
  submitError.value = ''
  submitSuccess.value = ''

  const symbols = runForm.symbols
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)

  if (!symbols.length) {
    submitError.value = t('strategyDetail.errorAtLeastOneSymbol')
    return
  }
  if (!runForm.startDate || !runForm.endDate) {
    submitError.value = t('strategyDetail.errorCompleteDateRange')
    return
  }
  if (!formValid.value) {
    submitError.value = t('strategyDetail.errorFixFormErrors')
    return
  }
  if (hasIncompatibleDataSource(symbols, effectiveDataSource.value)) {
    submitError.value = t('strategyDetail.errorIncompatibleDataSource')
    return
  }

  submitting.value = true
  try {
    const result = await submitBacktest({
      strategy_id: strategyId,
      symbols,
      start_date: runForm.startDate,
      end_date: runForm.endDate,
      data_source: effectiveDataSource.value,
      parameters: sanitizeParameters(definitions.value, parameterValues.value),
      enable_ai: enableAI.value,
      locale: locale.value,
    })

    if (isGuidedMode) {
      userStore.setGuidedBacktestJob(result.job_id)
      userStore.setGuidedBacktestStep(3)
      userStore.setOnboardingHighlightTarget(null)
      await waitForGuidedReport(result.job_id)
      userStore.setGuidedBacktestStep(4)
      userStore.setOnboardingHighlightTarget('backtest-results-section')
      await router.push({
        name: 'backtest-report',
        params: { jobId: result.job_id },
        query: { guided: 'true' },
      })
    } else {
      submitSuccess.value = t('strategyDetail.backtestSubmitted', { jobId: result.job_id })
    }
  } catch (error: any) {
    submitError.value = error?.message || t('strategyDetail.submitError')
  } finally {
    submitting.value = false
  }
}

function focusRunButton() {
  const button = document.querySelector('[data-test="start-backtest"]') as HTMLButtonElement | null
  button?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  button?.focus()
}

function mergeDefaults(definitionsList: StrategyParameterDefinition[], values: Record<string, unknown>) {
  const next = { ...values }
  for (const definition of definitionsList) {
    if (next[definition.name] === undefined && definition.default !== undefined) {
      next[definition.name] = definition.default
    }
  }
  return next
}

function sanitizeParameters(definitionsList: StrategyParameterDefinition[], values: Record<string, unknown>) {
  const next: Record<string, unknown> = {}
  for (const definition of definitionsList) {
    const value = values[definition.name]
    if (value === '' || value === undefined || value === null) {
      if (definition.required && definition.default !== undefined) {
        next[definition.name] = definition.default
      }
      continue
    }
    next[definition.name] = value
  }
  return next
}

function defaultEndDate() {
  return new Date().toISOString().slice(0, 10)
}

function defaultStartDate() {
  const date = new Date()
  date.setMonth(date.getMonth() - 1)
  return date.toISOString().slice(0, 10)
}

function isAshareSymbol(symbol: string) {
  const normalized = String(symbol || '').trim().toUpperCase()
  return /^\d{6}\.(XSHE|XSHG)$/.test(normalized)
}

function isGoldSymbol(symbol: string) {
  const normalized = String(symbol || '').trim().toUpperCase().replace(/[\/-]/g, '')
  return ['XAUUSD', 'XAU', 'GOLD', 'GCF', 'GC=F', 'GCF=F'].includes(normalized)
}

function inferRecommendedDataSource(symbol: string) {
  if (isAshareSymbol(symbol)) {
    return 'akshare'
  }
  if (isGoldSymbol(symbol)) {
    return 'freegold'
  }
  return 'auto'
}

function hasIncompatibleDataSource(symbols: string[], dataSource: string) {
  if (!symbols.length) {
    return false
  }
  const normalizedSource = String(dataSource || '').trim().toLowerCase()
  const allAshare = symbols.every((symbol) => isAshareSymbol(symbol))
  const allGold = symbols.every((symbol) => isGoldSymbol(symbol))

  if (allAshare) {
    return ['binance', 'freegold'].includes(normalizedSource)
  }
  if (allGold) {
    return ['akshare', 'joinquant'].includes(normalizedSource)
  }
  return false
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function waitForGuidedReport(jobId: string) {
  for (let attempt = 0; attempt < 30; attempt += 1) {
    const status = await fetchBacktestStatus(jobId)
    if (status.status === 'completed') {
      return
    }
    if (status.status === 'failed' || status.status === 'timeout') {
      throw new Error(getBacktestFailureMessage(status))
    }
    await sleep(1000)
  }
  throw new Error('Backtest job timeout')
}
</script>

<style scoped>
@keyframes spin {
  to { transform: rotate(360deg); }
}
@keyframes pulse-ring {
  0% { box-shadow: 0 0 0 0 rgba(0, 217, 255, 0.35); }
  70% { box-shadow: 0 0 0 12px rgba(0, 217, 255, 0); }
  100% { box-shadow: 0 0 0 0 rgba(0, 217, 255, 0); }
}

.strategy-detail-view {
  width: 100%;
}

/* ── Page Header ── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
  padding-bottom: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
}

.eyebrow {
  margin: 0 0 6px;
  font-size: var(--font-size-xs);
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-accent);
}

.page-title {
  margin: 0;
  font-size: var(--font-size-xxl);
  font-weight: 800;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
}

.page-subtitle {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

/* ── Guided Banner ── */
.guided-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: var(--spacing-md) var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  background: var(--color-primary-bg);
  border: 2px solid var(--color-primary-border);
  border-left: 4px solid var(--color-accent);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.guided-next-steps {
  margin-bottom: var(--spacing-lg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-lg);
  padding: var(--spacing-lg);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.guided-next-steps__eyebrow {
  margin: 0 0 8px;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.guided-next-steps__content h2 {
  margin: 0 0 var(--spacing-xs);
  font-size: var(--font-size-xl);
  color: var(--color-text-primary);
}

.guided-next-steps__content p {
  margin: 0;
  color: var(--color-text-secondary);
}

.guided-next-steps__actions {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

/* ── Grid Layout ── */
.layout-grid {
  display: grid;
  grid-template-columns: minmax(300px, 0.9fr) minmax(0, 1.1fr);
  gap: var(--spacing-lg);
  align-items: start;
}

/* ── Panel Cards ── */
.panel-card {
  padding: 0;
  overflow: hidden;
}

.panel-card__header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 2px solid var(--color-border);
  background: var(--color-surface-elevated);
}

.panel-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  background: var(--color-primary-bg);
  border: 2px solid var(--color-border);
  color: var(--color-accent);
  flex-shrink: 0;
}

.panel-title {
  margin: 0;
  font-size: var(--font-size-md);
  font-weight: 700;
  color: var(--color-text-primary);
}

.panel-body {
  padding: var(--spacing-lg);
}

/* ── Field Grid ── */
.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.field--full {
  grid-column: 1 / -1;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.field-input {
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 9px 12px;
  background: var(--color-surface-elevated);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-family: var(--font-mono);
  transition: border-color 0.15s, box-shadow 0.15s;
  width: 100%;
  box-sizing: border-box;
}

.field-input:focus {
  outline: none;
  border-color: var(--color-primary-border);
  box-shadow: 0 0 0 3px rgba(30, 90, 168, 0.12);
}

.field-hint {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  line-height: 1.5;
}

/* ── Preset Divider ── */
.preset-divider {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.preset-divider::before,
.preset-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--color-border-light);
}

.preset-divider span {
  font-size: var(--font-size-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
  white-space: nowrap;
}

/* ── Loading State ── */
.loading-state {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xl);
  justify-content: center;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.loading-state__spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

/* ── Submit Bar ── */
.submit-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.submit-bar__feedback {
  flex: 1;
}

.message {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--font-size-sm);
}

.message.error {
  color: var(--color-danger);
}

.message.success {
  color: var(--color-success);
}

/* ── Run Button ── */
.btn-run {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 11px 28px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-full);
  background: var(--color-accent);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-weight: 700;
  letter-spacing: 0.03em;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  flex-shrink: 0;
}

.btn-run:hover:not(:disabled) {
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
}

.btn-run__spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

/* ── Strategy Identity ── */
.strategy-identity {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  margin-bottom: var(--spacing-lg);
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  width: fit-content;
}

.strategy-identity__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
  background: var(--color-primary-bg);
  color: var(--color-accent);
  flex-shrink: 0;
}

.strategy-identity__info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.strategy-identity__id {
  font-size: var(--font-size-xs);
  font-family: var(--font-mono);
  color: var(--color-text-muted);
  letter-spacing: 0.02em;
}

/* ── Responsive ── */
@media (max-width: 960px) {
  .page-header,
  .layout-grid {
    display: flex;
    flex-direction: column;
  }

  .field-grid {
    grid-template-columns: 1fr;
  }

  .field--full {
    grid-column: 1;
  }

  .submit-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .guided-next-steps {
    flex-direction: column;
    align-items: flex-start;
  }

  .btn-run {
    width: 100%;
    justify-content: center;
  }

  .strategy-identity {
    width: 100%;
  }
}
</style>

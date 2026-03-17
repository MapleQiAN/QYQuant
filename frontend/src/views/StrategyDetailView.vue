<template>
  <section class="strategy-detail-view">
    <div class="container">
      <div class="page-header">
        <div>
          <h1 class="page-title">Strategy Parameters</h1>
          <p class="page-subtitle">Configure strategy inputs, save presets, and launch a backtest task.</p>
        </div>
        <RouterLink class="btn btn-secondary" to="/strategies">Back to strategy library</RouterLink>
      </div>

      <div v-if="isGuidedMode" class="card guided-banner">
        Guided backtest is enabled. The default symbols, date range, and parameters are already prepared for your first run.
      </div>

      <div class="layout-grid">
        <div class="card control-card">
          <div class="section-title">Backtest Setup</div>
          <div class="field-grid">
            <label class="field">
              <span class="field-label">Symbols</span>
              <input
                data-test="symbol-input"
                v-model.trim="runForm.symbols"
                class="field-input"
                type="text"
                placeholder="BTCUSDT, ETHUSDT"
              />
            </label>
            <label class="field">
              <span class="field-label">Start Date</span>
              <input
                data-test="start-date-input"
                v-model="runForm.startDate"
                class="field-input"
                type="date"
              />
            </label>
            <label class="field">
              <span class="field-label">End Date</span>
              <input
                data-test="end-date-input"
                v-model="runForm.endDate"
                class="field-input"
                type="date"
              />
            </label>
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

        <div class="card form-card">
          <div class="section-title">Parameter Form</div>
          <p v-if="loading" class="message">Loading strategy parameters...</p>
          <p v-else-if="loadError" class="message error">{{ loadError }}</p>
          <ParameterForm
            v-else
            v-model="parameterValues"
            :definitions="definitions"
            @validation-change="formValid = $event"
          />
        </div>
      </div>

      <div class="submit-bar">
        <p v-if="submitError" class="message error">{{ submitError }}</p>
        <p v-else-if="submitSuccess" class="message success">{{ submitSuccess }}</p>
        <button
          data-test="start-backtest"
          :class="['btn btn-primary', { 'onboarding-highlight': userStore.onboardingHighlightTarget === 'guided-run-button' }]"
          data-onboarding-target="guided-run-button"
          type="button"
          :disabled="submitting || loading"
          @click="handleSubmit"
        >
          {{ submitting ? 'Submitting...' : 'Start Backtest' }}
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { fetchBacktestStatus, submitBacktest } from '../api/backtests'
import { fetchStrategyParameters } from '../api/strategies'
import ParameterForm from '../components/strategy/ParameterForm.vue'
import PresetManager from '../components/strategy/PresetManager.vue'
import { useUserStore } from '../stores'
import { usePresetsStore } from '../stores/usePresetsStore'
import type { StrategyParameterDefinition } from '../types/Strategy'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const strategyId = String(route.params.strategyId || '')
const isGuidedMode = route.query.guided === 'true'
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

const runForm = reactive({
  symbols: '',
  startDate: defaultStartDate(),
  endDate: defaultEndDate(),
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
    loadError.value = error?.message || 'Failed to load strategy parameters'
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
    submitError.value = 'Please enter at least one symbol'
    return
  }
  if (!runForm.startDate || !runForm.endDate) {
    submitError.value = 'Please choose a complete date range'
    return
  }
  if (!formValid.value) {
    submitError.value = 'Please fix the parameter form errors first'
    return
  }

  submitting.value = true
  try {
    const result = await submitBacktest({
      strategy_id: strategyId,
      symbols,
      start_date: runForm.startDate,
      end_date: runForm.endDate,
      parameters: sanitizeParameters(definitions.value, parameterValues.value),
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
      submitSuccess.value = `Backtest submitted: ${result.job_id}`
    }
  } catch (error: any) {
    submitError.value = error?.message || 'Failed to submit backtest'
  } finally {
    submitting.value = false
  }
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
      throw new Error(`Backtest job failed: ${status.status}`)
    }
    await sleep(1000)
  }
  throw new Error('Backtest job timeout')
}
</script>

<style scoped>
.strategy-detail-view {
  width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.page-title {
  margin: 0;
  font-size: var(--font-size-xxl);
  color: var(--color-text-primary);
}

.page-subtitle {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-muted);
}

.guided-banner {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  border-left: 4px solid #f5e642;
}

.layout-grid {
  display: grid;
  grid-template-columns: minmax(300px, 0.9fr) minmax(0, 1.1fr);
  gap: var(--spacing-lg);
}

.control-card,
.form-card {
  padding: var(--spacing-lg);
}

.section-title {
  margin-bottom: var(--spacing-md);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.field-label {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.field-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-primary);
}

.submit-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
}

.message {
  margin: 0;
  color: var(--color-text-muted);
}

.message.error {
  color: var(--color-danger);
}

.message.success {
  color: #15803d;
}

@media (max-width: 960px) {
  .page-header,
  .layout-grid,
  .submit-bar {
    display: flex;
    flex-direction: column;
  }

  .submit-bar {
    align-items: stretch;
  }
}
</style>

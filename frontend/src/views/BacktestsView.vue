<template>
  <section class="view">
    <div class="container">
      <h1 class="view-title">{{ $t('pages.backtestsTitle') }}</h1>
      <p class="view-subtitle">{{ $t('pages.backtestsSubtitle') }}</p>

      <div class="layout-grid">
        <div class="card panel">
          <h3 class="panel-title">Run Backtest</h3>

          <label class="field">
            <span class="field-label">Strategy</span>
            <select class="field-input" v-model="runForm.strategyId">
              <option value="">None (price-only summary)</option>
              <option v-for="item in strategies" :key="item.id" :value="item.id">
                {{ item.name }} ({{ item.symbol }})
              </option>
            </select>
          </label>

          <div v-if="strategiesError" class="message error">{{ strategiesError }}</div>

          <label class="field">
            <span class="field-label">Symbol</span>
            <input v-model.trim="runForm.symbol" class="field-input" type="text" placeholder="e.g. BTCUSDT" />
          </label>

          <div class="field-row">
            <label class="field">
              <span class="field-label">Interval</span>
              <input v-model.trim="runForm.interval" class="field-input" type="text" placeholder="e.g. 1m" />
            </label>
            <label class="field">
              <span class="field-label">Bars</span>
              <input v-model.number="runForm.limit" class="field-input" type="number" min="10" max="3000" />
            </label>
          </div>

          <div v-if="runForm.strategyId" class="runtime-box">
            <div class="runtime-title">Strategy Runtime</div>
            <p v-if="runtimeLoading" class="message">Loading strategy parameters...</p>
            <p v-else-if="runtimeError" class="message error">{{ runtimeError }}</p>
            <template v-else-if="runtimeDescriptor">
              <p class="runtime-version">Version: {{ runtimeDescriptor.strategyVersion }}</p>

              <div v-if="runtimeDescriptor.parameters.length === 0" class="message">
                No custom parameters.
              </div>

              <label v-for="param in runtimeDescriptor.parameters" :key="param.key" class="field">
                <span class="field-label">{{ param.key }}</span>

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
            </template>
          </div>

          <div class="actions">
            <button class="btn btn-primary" type="button" :disabled="runState.running || runtimeLoading" @click="handleRun">
              {{ runState.running ? 'Running...' : 'Run Backtest' }}
            </button>
          </div>

          <p v-if="runState.status" class="message">{{ runState.status }}</p>
          <p v-if="runState.error" class="message error">{{ runState.error }}</p>
        </div>

        <div class="card panel">
          <h3 class="panel-title">Result</h3>
          <div v-if="latestResult" class="result-grid">
            <div class="result-item">
              <span class="result-label">Total Return</span>
              <span class="result-value">{{ latestResult.summary.totalReturn }}%</span>
            </div>
            <div class="result-item">
              <span class="result-label">Sharpe</span>
              <span class="result-value">{{ latestResult.summary.sharpeRatio ?? '-' }}</span>
            </div>
            <div class="result-item">
              <span class="result-label">Max Drawdown</span>
              <span class="result-value">{{ latestResult.summary.maxDrawdown ?? '-' }}%</span>
            </div>
            <div class="result-item">
              <span class="result-label">Trades</span>
              <span class="result-value">{{ latestResult.trades.length }}</span>
            </div>
            <div v-if="latestResult.runtime" class="result-item wide">
              <span class="result-label">Runtime</span>
              <span class="result-value">
                {{ latestResult.runtime.strategyId }} @ {{ latestResult.runtime.strategyVersion }}
              </span>
            </div>
          </div>
          <p v-else class="message">Run a backtest to see metrics.</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { fetchRecent, fetchRuntimeDescriptor } from '../api/strategies'
import { fetchBacktestJob, runBacktest } from '../api/backtests'
import type { BacktestLatestResponse, RunBacktestPayload } from '../types/Backtest'
import type { Strategy, StrategyParameter, StrategyRuntimeDescriptor } from '../types/Strategy'

const strategies = ref<Strategy[]>([])
const strategiesError = ref('')
const runtimeDescriptor = ref<StrategyRuntimeDescriptor | null>(null)
const runtimeLoading = ref(false)
const runtimeError = ref('')
const latestResult = ref<BacktestLatestResponse | null>(null)

const runForm = reactive({
  strategyId: '',
  symbol: 'BTCUSDT',
  interval: '1m',
  limit: 120,
})

const runState = reactive({
  running: false,
  status: '',
  error: '',
})

const paramValues = reactive<Record<string, any>>({})

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

function sleep(ms: number) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms)
  })
}

async function waitJobSuccess(jobId: string): Promise<BacktestLatestResponse> {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    const job = await fetchBacktestJob(jobId)
    if (job.status === 'SUCCESS' && job.result) {
      return job.result
    }
    if (job.status === 'FAILURE' || job.status === 'REVOKED') {
      throw new Error(`Backtest job failed: ${job.status}`)
    }
    await sleep(500)
  }
  throw new Error('Backtest job timeout')
}

async function handleRun() {
  runState.error = ''
  runState.status = ''
  runState.running = true

  try {
    const payload: RunBacktestPayload = {
      symbol: runForm.symbol,
      interval: runForm.interval,
      limit: runForm.limit,
    }

    if (runForm.strategyId && runtimeDescriptor.value) {
      payload.strategyId = runForm.strategyId
      payload.strategyVersion = runtimeDescriptor.value.strategyVersion
      payload.strategyParams = buildStrategyParams(runtimeDescriptor.value.parameters)
    }

    runState.status = 'Submitting backtest task...'
    const runResponse = await runBacktest(payload)

    runState.status = `Waiting for result (${runResponse.job_id})...`
    latestResult.value = await waitJobSuccess(runResponse.job_id)
    runState.status = 'Backtest completed'
  } catch (error: any) {
    runState.error = error?.message || 'Failed to run backtest'
  } finally {
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
})
</script>

<style scoped>
.view {
  width: 100%;
}

.view-title {
  margin: 0 0 var(--spacing-sm);
  font-size: var(--font-size-xl);
  color: var(--color-text-primary);
}

.view-subtitle {
  margin: 0;
  color: var(--color-text-muted);
}

.layout-grid {
  margin-top: var(--spacing-lg);
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-lg);
}

.panel {
  padding: var(--spacing-lg);
}

.panel-title {
  margin: 0 0 var(--spacing-md);
  color: var(--color-text-primary);
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-sm);
}

.field-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-sm);
}

.field-label {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.field-input {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 8px 10px;
  background: var(--color-surface);
  color: var(--color-text-primary);
}

.field-checkbox {
  width: 18px;
  height: 18px;
}

.field-help {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.runtime-box {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.runtime-title {
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--spacing-xs);
  color: var(--color-text-primary);
}

.runtime-version {
  margin: 0 0 var(--spacing-sm);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.actions {
  margin-top: var(--spacing-md);
}

.message {
  margin: var(--spacing-sm) 0 0;
  color: var(--color-text-muted);
}

.message.error {
  color: var(--color-danger);
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-sm);
}

.result-item {
  padding: var(--spacing-sm);
  border-radius: var(--radius-md);
  background: var(--color-surface-alt);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.result-item.wide {
  grid-column: 1 / -1;
}

.result-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.result-value {
  font-size: var(--font-size-md);
  color: var(--color-text-primary);
  font-weight: var(--font-weight-semibold);
}

@media (max-width: 960px) {
  .layout-grid {
    grid-template-columns: 1fr;
  }
}
</style>

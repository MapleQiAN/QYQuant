<template>
  <section class="strategy-detail-view">
    <div class="container">
      <div class="page-header">
        <div>
          <h1 class="page-title">策略参数配置</h1>
          <p class="page-subtitle">配置策略参数、管理个人预设，并直接发起回测任务。</p>
        </div>
        <RouterLink class="btn btn-secondary" to="/strategies">返回策略库</RouterLink>
      </div>

      <div class="layout-grid">
        <div class="card control-card">
          <div class="section-title">回测设置</div>
          <div class="field-grid">
            <label class="field">
              <span class="field-label">交易标的</span>
              <input
                data-test="symbol-input"
                v-model.trim="runForm.symbols"
                class="field-input"
                type="text"
                placeholder="BTCUSDT, ETHUSDT"
              />
            </label>
            <label class="field">
              <span class="field-label">开始日期</span>
              <input
                data-test="start-date-input"
                v-model="runForm.startDate"
                class="field-input"
                type="date"
              />
            </label>
            <label class="field">
              <span class="field-label">结束日期</span>
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
          <div class="section-title">参数表单</div>
          <p v-if="loading" class="message">正在加载参数定义...</p>
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
          class="btn btn-primary"
          type="button"
          :disabled="submitting || loading"
          @click="handleSubmit"
        >
          {{ submitting ? '提交中...' : '开始回测' }}
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { submitBacktest } from '../api/backtests'
import { fetchStrategyParameters } from '../api/strategies'
import ParameterForm from '../components/strategy/ParameterForm.vue'
import PresetManager from '../components/strategy/PresetManager.vue'
import { usePresetsStore } from '../stores/usePresetsStore'
import type { StrategyParameterDefinition } from '../types/Strategy'

const route = useRoute()
const strategyId = String(route.params.strategyId || '')
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
    submitError.value = '请至少输入一个交易标的'
    return
  }
  if (!runForm.startDate || !runForm.endDate) {
    submitError.value = '请选择完整的回测时间区间'
    return
  }
  if (!formValid.value) {
    submitError.value = '请先修正参数表单中的错误'
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
    submitSuccess.value = `回测任务已提交：${result.job_id}`
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

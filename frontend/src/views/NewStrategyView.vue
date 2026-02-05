<template>
  <section class="new-strategy-view">
    <div class="container">
      <div class="page-header">
        <div class="header-text">
          <h1 class="page-title">{{ $t('strategyNew.title') }}</h1>
          <p class="page-subtitle">{{ $t('strategyNew.subtitle') }}</p>
        </div>
        <RouterLink class="btn btn-secondary" to="/">
          <ArrowLeftIcon />
          {{ $t('strategyNew.back') }}
        </RouterLink>
      </div>

      <div class="form-grid">
        <div class="card form-card">
          <div class="card-header">
            <h3>{{ $t('strategyNew.createTitle') }}</h3>
            <p class="hint">{{ $t('strategyNew.createHint') }}</p>
          </div>
          <form class="form-body" @submit.prevent="handleCreate">
            <label class="field">
              <span class="field-label">{{ $t('strategyNew.nameLabel') }}</span>
              <input
                v-model.trim="createForm.name"
                class="field-input"
                type="text"
                :placeholder="$t('strategyNew.namePlaceholder')"
              />
            </label>
            <label class="field">
              <span class="field-label">{{ $t('strategyNew.symbolLabel') }}</span>
              <input
                v-model.trim="createForm.symbol"
                class="field-input"
                type="text"
                :placeholder="$t('strategyNew.symbolPlaceholder')"
              />
            </label>
            <label class="field">
              <span class="field-label">{{ $t('strategyNew.tagsLabel') }}</span>
              <input
                v-model.trim="createForm.tags"
                class="field-input"
                type="text"
                :placeholder="$t('strategyNew.tagsPlaceholder')"
              />
            </label>

            <div class="form-actions">
              <button class="btn btn-primary" type="submit" :disabled="createState.loading">
                {{ $t('strategyNew.createAction') }}
              </button>
              <button class="btn btn-secondary" type="button" @click="resetCreate">
                {{ $t('strategyNew.resetAction') }}
              </button>
            </div>

            <p v-if="createState.error" class="form-message error">{{ createState.error }}</p>
            <p v-else-if="createState.success" class="form-message success">{{ createState.success }}</p>
          </form>
        </div>

        <div class="card form-card import-card">
          <div class="card-header">
            <h3>{{ $t('strategyNew.importTitle') }}</h3>
            <p class="hint">{{ $t('strategyNew.importHint') }}</p>
          </div>
          <div class="form-body">
            <label class="field">
              <span class="field-label">{{ $t('strategyNew.fileLabel') }}</span>
              <input
                class="field-input file-input"
                type="file"
                accept=".qys,.zip"
                @change="handleFileChange"
              />
            </label>
            <p class="field-help">{{ $t('strategyNew.fileHelp') }}</p>

            <div v-if="importFile" class="file-meta">
              <div class="file-row">
                <span class="file-label">{{ $t('strategyNew.fileSelected') }}</span>
                <span class="file-value">{{ importFile.name }}</span>
              </div>
              <div class="file-row">
                <span class="file-label">{{ $t('strategyNew.sizeLabel') }}</span>
                <span class="file-value">{{ formatBytes(importFile.size) }}</span>
              </div>
            </div>

            <div v-if="importState.result" class="import-result">
              <div class="result-title">{{ importState.result.strategy.name }}</div>
              <div class="result-subtitle">
                {{ $t('strategyNew.versionLabel') }}: {{ importState.result.version.version }}
              </div>
            </div>

            <div class="form-actions">
              <button
                class="btn btn-primary"
                type="button"
                :disabled="importState.loading || !importFile"
                @click="handleImport"
              >
                {{ $t('strategyNew.importAction') }}
              </button>
            </div>

            <p v-if="importState.error" class="form-message error">{{ importState.error }}</p>
            <p v-else-if="importState.success" class="form-message success">{{ importState.success }}</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref, h } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import { createStrategy, importStrategy } from '../api/strategies'
import type { StrategyImportResult } from '../types/Strategy'
import { useStrategiesStore } from '../stores'

const { t } = useI18n()
const strategiesStore = useStrategiesStore()

const createForm = reactive({
  name: '',
  symbol: '',
  tags: ''
})

const createState = reactive({
  loading: false,
  error: '',
  success: ''
})

const importFile = ref<File | null>(null)
const importState = reactive<{
  loading: boolean
  error: string
  success: string
  result: StrategyImportResult | null
}>({
  loading: false,
  error: '',
  success: '',
  result: null
})

function resetCreate() {
  createForm.name = ''
  createForm.symbol = ''
  createForm.tags = ''
  createState.error = ''
  createState.success = ''
}

async function handleCreate() {
  createState.error = ''
  createState.success = ''
  const name = createForm.name.trim()
  const symbol = createForm.symbol.trim()
  if (!name) {
    createState.error = t('strategyNew.nameRequired')
    return
  }
  if (!symbol) {
    createState.error = t('strategyNew.symbolRequired')
    return
  }
  const tags = createForm.tags
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean)

  createState.loading = true
  try {
    const strategy = await createStrategy({ name, symbol, tags, status: 'draft' })
    createState.success = `${t('strategyNew.createSuccess')}: ${strategy.name}`
    strategiesStore.loadRecent()
  } catch (error: any) {
    createState.error = error?.message || 'Failed to create strategy'
  } finally {
    createState.loading = false
  }
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  importFile.value = input.files?.[0] || null
  importState.error = ''
  importState.success = ''
  importState.result = null
}

async function handleImport() {
  importState.error = ''
  importState.success = ''
  importState.result = null
  if (!importFile.value) {
    importState.error = t('strategyNew.fileRequired')
    return
  }
  importState.loading = true
  try {
    const result = await importStrategy(importFile.value)
    importState.result = result
    importState.success = `${t('strategyNew.importSuccess')}: ${result.strategy.name}`
    strategiesStore.loadRecent()
    importFile.value = null
  } catch (error: any) {
    importState.error = error?.message || 'Failed to import strategy'
  } finally {
    importState.loading = false
  }
}

function formatBytes(bytes: number) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
}

const ArrowLeftIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M19 12H5' }),
  h('path', { d: 'm12 19-7-7 7-7' })
])
</script>

<style scoped>
.new-strategy-view {
  width: 100%;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.page-title {
  font-size: var(--font-size-xxl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin: 0;
}

.page-subtitle {
  font-size: var(--font-size-md);
  color: var(--color-text-muted);
  margin: 0;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-lg);
}

.form-card {
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.card-header h3 {
  margin: 0 0 var(--spacing-xs);
  font-size: var(--font-size-lg);
  color: var(--color-text-primary);
}

.hint {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.form-body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.field-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.field-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.field-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-bg);
}

.file-input {
  padding: var(--spacing-xs);
}

.field-help {
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.file-meta {
  background: var(--color-background);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--color-border-light);
}

.file-row {
  display: flex;
  justify-content: space-between;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.file-row + .file-row {
  margin-top: var(--spacing-xs);
}

.file-label {
  color: var(--color-text-muted);
}

.file-value {
  color: var(--color-text-primary);
  font-weight: var(--font-weight-medium);
}

.import-result {
  border-radius: var(--radius-md);
  border: 1px solid var(--color-primary-light);
  background: var(--color-primary-bg);
  padding: var(--spacing-md);
}

.result-title {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.result-subtitle {
  margin-top: var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.form-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.form-message {
  margin: 0;
  font-size: var(--font-size-sm);
}

.form-message.error {
  color: var(--color-danger);
}

.form-message.success {
  color: var(--color-success);
}

@media (max-width: 1024px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }
}
</style>

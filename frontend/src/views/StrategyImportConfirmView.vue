<template>
  <section class="strategy-import-confirm-view">
    <div class="container">
      <div class="page-header">
        <div>
          <p class="eyebrow">{{ $t('strategy.import.pageTitle') }}</p>
          <h1 class="page-title">{{ $t('strategy.import.confirmImport') }}</h1>
          <p class="page-subtitle">{{ $t('strategy.import.supportedFormats') }}</p>
        </div>
        <RouterLink class="btn btn-secondary" to="/strategies/import">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
          {{ $t('strategy.import.backToLibrary') }}
        </RouterLink>
      </div>

      <div class="steps">
        <div class="step step--done">
          <span class="step__num">1</span>
          <span class="step__label">{{ $t('strategy.import.strategySource') }}</span>
        </div>
        <div class="step__line step__line--done"></div>
        <div class="step step--active">
          <span class="step__num">2</span>
          <span class="step__label">{{ $t('strategy.import.confirmImport') }}</span>
        </div>
      </div>

      <div v-if="!analysis" class="card panel">
        <p class="message error">{{ $t('strategy.import.failedToAnalyze') }}</p>
      </div>

      <div v-else class="layout-grid">
        <div class="card panel summary-panel">
          <div class="summary-header">
            <div class="summary-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            </div>
            <h2 class="summary-title">Import Summary</h2>
          </div>

          <div class="summary-rows">
            <div class="summary-row">
              <span class="summary-label">Source</span>
              <span class="summary-value">{{ sourceLabel }}</span>
            </div>
            <div v-if="analysis.fileSummary?.filename" class="summary-row">
              <span class="summary-label">File</span>
              <span class="summary-value summary-value--mono">{{ analysis.fileSummary.filename }}</span>
            </div>
          </div>

          <div class="validation-block">
            <h3 class="validation-title">{{ $t('strategy.import.validationTitle') }}</h3>
            <div class="validation-list">
              <div data-test="validation-entrypoint" class="validation-item">
                <span>{{ $t('strategy.import.validationEntrypoint') }}</span>
                <strong :class="validationClass(validationState.entrypointFound)">{{ validationLabel(validationState.entrypointFound) }}</strong>
              </div>
              <div data-test="validation-syntax" class="validation-item">
                <span>{{ $t('strategy.import.validationSyntax') }}</span>
                <strong :class="validationClass(validationState.pythonSyntaxValid)">{{ validationLabel(validationState.pythonSyntaxValid) }}</strong>
              </div>
              <div data-test="validation-return" class="validation-item">
                <span>{{ $t('strategy.import.validationReturn') }}</span>
                <strong :class="validationClass(validationState.orderListReturnLikely)">{{ validationLabel(validationState.orderListReturnLikely) }}</strong>
              </div>
              <div class="validation-item">
                <span>{{ $t('strategy.import.validationMetadata') }}</span>
                <strong :class="validationClass(validationState.metadataDetected)">{{ validationLabel(validationState.metadataDetected) }}</strong>
              </div>
            </div>
          </div>

          <div v-if="analysis.warnings.length" class="summary-alert summary-alert--warning">
            {{ analysis.warnings.join(', ') }}
          </div>
          <div v-if="analysis.errors.length" class="summary-alert summary-alert--error">
            {{ analysis.errors.join(', ') }}
          </div>
        </div>

        <div class="card panel">
          <h2 class="panel-title">{{ $t('strategy.import.confirmImport') }}</h2>
          <label class="field">
            <span class="field-label">Entrypoint</span>
            <QSelect v-model="selectedEntrypointKey" :options="entrypointOptions" />
          </label>

          <label class="field">
            <span class="field-label">{{ $t('strategyNew.nameLabel') }}</span>
            <input v-model="name" class="field-input" type="text" />
          </label>

          <label class="field">
            <span class="field-label">{{ $t('strategy.publish.descriptionLabel') }}</span>
            <textarea v-model="description" class="field-input field-textarea" />
          </label>

          <label class="field">
            <span class="field-label">{{ $t('marketplace.category') }}</span>
            <input v-model="category" class="field-input" type="text" />
          </label>

          <label class="field">
            <span class="field-label">{{ $t('strategyNew.symbolLabel') }}</span>
            <input v-model="symbol" class="field-input" type="text" />
          </label>

          <label class="field">
            <span class="field-label">{{ $t('marketplace.tags') }}</span>
            <input v-model="tags" class="field-input" type="text" />
          </label>

          <div class="actions">
            <button
              data-test="confirm-import"
              class="btn btn-primary"
              type="button"
              :disabled="submitting || !selectedEntrypoint"
              @click="handleConfirm"
            >
              <span v-if="submitting" class="btn-spinner"></span>
              {{ submitting ? $t('strategy.import.importing') : $t('strategy.import.confirmImport') }}
            </button>
          </div>

          <p v-if="error" class="message error">{{ error }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { confirmStrategyImport } from '../api/strategies'
import { toast } from '../lib/toast'
import type { StrategyImportAnalysis } from '../types/Strategy'
import { QSelect } from '../components/ui'

const route = useRoute()
const router = useRouter()
const draftImportId = String(route.query.draftImportId || '')
const source = String(route.query.source || 'import')
const rawAnalysis = draftImportId ? sessionStorage.getItem(`strategy-import:${draftImportId}`) : null
const analysis = ref<StrategyImportAnalysis | null>(rawAnalysis ? JSON.parse(rawAnalysis) : null)
const selectedEntrypointKey = ref(
  analysis.value?.entrypointCandidates[0]
    ? `${analysis.value.entrypointCandidates[0].path}:${analysis.value.entrypointCandidates[0].callable}`
    : ''
)
const metadataCandidates = (analysis.value?.metadataCandidates || {}) as Record<string, unknown>
const name = ref(String(metadataCandidates.name || ''))
const description = ref(String(metadataCandidates.description || ''))
const category = ref(String(metadataCandidates.category || 'other'))
const symbol = ref(String(metadataCandidates.symbol || ''))
const tags = ref(Array.isArray(metadataCandidates.tags) ? metadataCandidates.tags.join(', ') : '')
const submitting = ref(false)
const error = ref('')

const selectedEntrypoint = computed(() => {
  return (
    analysis.value?.entrypointCandidates.find(
      (candidate) => `${candidate.path}:${candidate.callable}` === selectedEntrypointKey.value
    ) || null
  )
})

const sourceLabel = computed(() => {
  if (source === 'template') return 'Template'
  if (source === 'ai') return 'AI draft'
  return 'Imported file'
})

const entrypointOptions = computed(() =>
  (analysis.value?.entrypointCandidates || []).map((c) => ({
    label: `${c.callable} @ ${c.path}`,
    value: `${c.path}:${c.callable}`,
  }))
)

const validationState = computed(() => {
  const base = analysis.value
    ? {
        entrypointFound: analysis.value.entrypointCandidates.length > 0,
        pythonSyntaxValid: !(analysis.value.errors || []).some((item) => item.toLowerCase().includes('syntax')),
        orderListReturnLikely: null,
        metadataDetected: Boolean((analysis.value.metadataCandidates || {}).name || (analysis.value.metadataCandidates || {}).symbol),
      }
    : {
        entrypointFound: false,
        pythonSyntaxValid: null,
        orderListReturnLikely: null,
        metadataDetected: false,
      }

  return {
    ...base,
    ...(analysis.value?.validation || {}),
  }
})

function validationLabel(value: boolean | null | undefined) {
  if (value === true) return 'Passed'
  if (value === false) return 'Needs review'
  return 'Not checked'
}

function validationClass(value: boolean | null | undefined) {
  if (value === true) return 'validation-state validation-state--pass'
  if (value === false) return 'validation-state validation-state--warn'
  return 'validation-state validation-state--unknown'
}

async function handleConfirm() {
  if (!analysis.value || !selectedEntrypoint.value) {
    error.value = 'Select an entrypoint before continuing.'
    toast.error(error.value)
    return
  }
  if (!name.value.trim()) {
    error.value = 'Strategy name is required.'
    toast.error(error.value)
    return
  }

  submitting.value = true
  error.value = ''
  try {
    const result = await confirmStrategyImport({
      draftImportId: analysis.value.draftImportId,
      selectedEntrypoint: {
        path: selectedEntrypoint.value.path,
        callable: selectedEntrypoint.value.callable,
        interface: selectedEntrypoint.value.interface || 'event_v1',
      },
      metadata: {
        name: name.value.trim(),
        description: description.value.trim(),
        category: category.value.trim(),
        symbol: symbol.value.trim(),
        tags: tags.value
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean),
      },
      parameterDefinitions: analysis.value.parameterCandidates,
    })
    sessionStorage.removeItem(`strategy-import:${analysis.value.draftImportId}`)
    toast.success(`策略已导入：${result.strategy.name}`)
    if (result.next) {
      await router.push({
        path: result.next,
        query: {
          guided: 'true',
          source,
        },
      })
    }
  } catch (err: any) {
    error.value = err?.message || 'Failed to confirm strategy import'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
@keyframes spin {
  to { transform: rotate(360deg); }
}

.strategy-import-confirm-view {
  width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
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
}

.page-subtitle {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-muted);
}

.steps {
  display: flex;
  align-items: center;
  margin-bottom: var(--spacing-xl);
}

.step {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.step__num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: var(--color-surface-elevated);
}

.step--done .step__num,
.step--active .step__num {
  background: var(--color-accent);
  color: white;
}

.step__line {
  flex: 0 0 44px;
  height: 2px;
  background: var(--color-border);
  margin: 0 var(--spacing-sm);
}

.step__line--done {
  background: var(--color-accent);
}

.layout-grid {
  display: grid;
  grid-template-columns: minmax(280px, 380px) minmax(0, 1fr);
  gap: var(--spacing-lg);
}

.panel {
  padding: var(--spacing-lg);
}

.summary-header,
.summary-row,
.validation-item,
.actions {
  display: flex;
  align-items: center;
}

.summary-header {
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.summary-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: var(--color-primary-bg);
  color: var(--color-accent);
}

.summary-title,
.validation-title,
.panel-title {
  margin: 0;
}

.summary-rows,
.validation-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.summary-row,
.validation-item {
  justify-content: space-between;
  gap: var(--spacing-sm);
}

.summary-label {
  color: var(--color-text-muted);
}

.summary-value--mono {
  font-family: var(--font-mono);
}

.validation-block {
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}

.validation-title {
  margin-bottom: var(--spacing-sm);
  font-size: var(--font-size-md);
}

.validation-state--pass {
  color: #2a9d65;
}

.validation-state--warn {
  color: #c87a00;
}

.validation-state--unknown {
  color: var(--color-text-muted);
}

.summary-alert {
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
}

.summary-alert--warning {
  background: rgba(200, 122, 0, 0.12);
  color: #c87a00;
}

.summary-alert--error {
  background: rgba(207, 78, 78, 0.12);
  color: #cf4e4e;
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-md);
}

.field-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-primary);
}

.field-textarea {
  min-height: 96px;
  resize: vertical;
}

.actions {
  justify-content: flex-start;
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: white;
  animation: spin 0.8s linear infinite;
}

.message {
  margin: var(--spacing-md) 0 0;
}

.error {
  color: var(--color-danger);
}

@media (max-width: 900px) {
  .layout-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .page-header {
    flex-direction: column;
  }
}
</style>

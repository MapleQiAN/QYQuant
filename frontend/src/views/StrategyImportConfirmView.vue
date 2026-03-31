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

      <!-- Step Indicator -->
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
        <div class="error-state">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          <p class="message error">{{ $t('strategy.import.failedToAnalyze') }}</p>
        </div>
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
              <span class="summary-value">{{ analysis.sourceType }}</span>
            </div>
            <div v-if="analysis.fileSummary?.filename" class="summary-row">
              <span class="summary-label">File</span>
              <span class="summary-value summary-value--mono">{{ analysis.fileSummary.filename }}</span>
            </div>
          </div>
          <div v-if="analysis.warnings.length" class="summary-alert summary-alert--warning">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            {{ analysis.warnings.join(', ') }}
          </div>
          <div v-if="analysis.errors.length" class="summary-alert summary-alert--error">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
            {{ analysis.errors.join(', ') }}
          </div>
        </div>

        <div class="card panel">
          <h2 class="panel-title">{{ $t('strategy.import.confirmImport') }}</h2>
          <label class="field">
            <span class="field-label">Entrypoint</span>
            <select v-model="selectedEntrypointKey" class="field-input">
              <option
                v-for="candidate in analysis.entrypointCandidates"
                :key="candidate.path + ':' + candidate.callable"
                :value="candidate.path + ':' + candidate.callable"
              >
                {{ candidate.callable }} @ {{ candidate.path }}
              </option>
            </select>
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
import type { StrategyImportAnalysis } from '../types/Strategy'

const route = useRoute()
const router = useRouter()
const draftImportId = String(route.query.draftImportId || '')
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

async function handleConfirm() {
  if (!analysis.value || !selectedEntrypoint.value) {
    error.value = 'Select an entrypoint before continuing.'
    return
  }
  if (!name.value.trim()) {
    error.value = 'Strategy name is required.'
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
        interface: selectedEntrypoint.value.interface || 'event_v1'
      },
      metadata: {
        name: name.value.trim(),
        description: description.value.trim(),
        category: category.value.trim(),
        symbol: symbol.value.trim(),
        tags: tags.value
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean)
      },
      parameterDefinitions: analysis.value.parameterCandidates
    })
    sessionStorage.removeItem(`strategy-import:${analysis.value.draftImportId}`)
    if (result.next) {
      await router.push(result.next)
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
  letter-spacing: -0.02em;
}

.page-subtitle {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

/* ── Steps ── */
.steps {
  display: flex;
  align-items: center;
  gap: 0;
  margin-bottom: var(--spacing-xl);
}

.step {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.step__num {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  font-size: 11px;
  font-weight: 700;
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  background: var(--color-surface);
}

.step--done .step__num {
  background: var(--color-primary-bg);
  border-color: var(--color-primary-border);
  color: var(--color-accent);
}

.step--active .step__num {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-text-inverse);
}

.step__label {
  font-size: var(--font-size-xs);
  font-weight: 600;
  color: var(--color-text-muted);
}

.step--active .step__label {
  color: var(--color-text-primary);
}

.step__line {
  width: 40px;
  height: 1px;
  background: var(--color-border);
  margin: 0 var(--spacing-sm);
}

.step__line--done {
  background: var(--color-primary-border);
}

/* ── Layout ── */
.layout-grid {
  display: grid;
  grid-template-columns: minmax(280px, 0.8fr) minmax(0, 1.2fr);
  gap: var(--spacing-lg);
  align-items: start;
}

.panel {
  padding: var(--spacing-lg);
}

.panel:hover {
  transform: none;
}

.panel-title {
  margin: 0 0 var(--spacing-sm);
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-text-primary);
}

/* ── Summary Panel ── */
.summary-panel {
  position: relative;
  overflow: hidden;
}

.summary-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--color-primary), var(--color-accent));
}

.summary-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.summary-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  background: var(--color-primary-bg);
  color: var(--color-accent);
}

.summary-title {
  margin: 0;
  font-size: var(--font-size-md);
  font-weight: 700;
  color: var(--color-text-primary);
}

.summary-rows {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--color-border-light);
}

.summary-row:last-child {
  border-bottom: none;
}

.summary-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 600;
}

.summary-value {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  font-weight: 600;
}

.summary-value--mono {
  font-family: var(--font-mono);
  font-size: var(--font-size-xs);
}

.summary-alert {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
  margin-top: var(--spacing-md);
  line-height: 1.4;
}

.summary-alert--warning {
  background: var(--color-warning-bg);
  color: var(--color-warning);
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.summary-alert--error {
  background: var(--color-danger-bg);
  color: var(--color-danger);
  border: 1px solid rgba(255, 59, 59, 0.2);
}

.summary-alert svg {
  flex-shrink: 0;
  margin-top: 1px;
}

/* ── Error State ── */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xl);
  color: var(--color-danger);
}

/* ── Fields ── */
.field {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-md);
}

.field-label {
  font-size: var(--font-size-xs);
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.field-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface-elevated);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  transition: border-color 0.15s, box-shadow 0.15s;
}

.field-input:focus {
  outline: none;
  border-color: var(--color-primary-border);
  box-shadow: 0 0 0 3px rgba(30, 90, 168, 0.12);
}

.field-textarea {
  min-height: 96px;
  resize: vertical;
}

.actions {
  margin-top: var(--spacing-lg);
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

.message.warning {
  color: var(--color-warning);
}

.message.error {
  margin-top: var(--spacing-md);
  color: var(--color-danger);
  font-size: var(--font-size-sm);
}

@media (max-width: 768px) {
  .page-header,
  .layout-grid {
    display: flex;
    flex-direction: column;
  }

  .steps {
    justify-content: center;
  }
}
</style>

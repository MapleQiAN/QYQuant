<template>
  <section class="new-strategy-view">
    <div class="container">
      <div class="page-header">
        <div class="header-text">
          <p class="eyebrow">{{ $t('pageTitle.strategies') }}</p>
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
            <div class="import-visual">
              <div class="import-visual__icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
              </div>
              <p class="import-visual__text">{{ $t('strategyNew.importHint') }}</p>
            </div>
            <div class="tag-row">
              <span class="pill">.py</span>
              <span class="pill">.zip</span>
              <span class="pill pill--accent">.qys</span>
            </div>

            <div class="form-actions">
              <RouterLink class="btn btn-primary" to="/strategies/import">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                {{ $t('strategyNew.importAction') }}
              </RouterLink>
            </div>
          </div>
        </div>

        <div class="card form-card guide-card">
          <div class="card-header">
            <h3>{{ $t('strategyNew.guideTitle') }}</h3>
            <p class="hint">{{ $t('strategyNew.guideHint') }}</p>
          </div>
          <div class="guide-body">
            <ol class="guide-steps">
              <li>{{ $t('strategyNew.guideStep1') }}</li>
              <li>{{ $t('strategyNew.guideStep2') }}</li>
              <li>{{ $t('strategyNew.guideStep3') }}</li>
            </ol>

            <pre class="guide-snippet guide-snippet--tree"><code>strategy.py</code></pre>

            <pre class="guide-snippet"><code>from qysp import BarData, Order, StrategyContext

def on_bar(ctx: StrategyContext, data: BarData) -> list[Order]:
    return []</code></pre>

            <div class="form-actions">
              <RouterLink
                class="btn btn-primary"
                :to="{ name: 'strategy-writing-guide' }"
                data-testid="strategy-guide-primary"
              >
                {{ $t('strategyNew.guidePrimaryAction') }}
              </RouterLink>
              <RouterLink
                class="btn btn-secondary"
                :to="{ name: 'strategy-writing-guide', hash: '#spec-reference' }"
                data-testid="strategy-guide-secondary"
              >
                {{ $t('strategyNew.guideSecondaryAction') }}
              </RouterLink>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { reactive, h } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import { createStrategy } from '../api/strategies'
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

.form-card:hover {
  transform: none;
}

.guide-card {
  grid-column: 1 / -1;
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

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.eyebrow {
  margin: 0 0 6px;
  font-size: var(--font-size-xs);
  font-weight: 600;
  color: var(--color-text-muted);
}

.pill {
  padding: 3px 9px;
  border-radius: 999px;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  font-size: 10px;
  font-family: var(--font-mono);
  font-weight: 700;
}

.pill--accent {
  border-color: var(--color-primary-border);
  color: var(--color-accent);
  background: var(--color-primary-bg);
}

.import-visual {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--spacing-lg) 0;
}

.import-visual__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  background: var(--color-primary-bg);
  color: var(--color-accent);
  margin-bottom: var(--spacing-sm);
}

.import-visual__text {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  max-width: 260px;
  line-height: 1.5;
}

.guide-body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.guide-steps {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 6px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.guide-snippet {
  margin: 0;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text-primary);
  font-family: var(--font-mono);
  font-size: var(--font-size-xs);
  line-height: 1.5;
  overflow: auto;
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

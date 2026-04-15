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

      <div class="path-grid">
        <article class="card path-card">
          <div class="path-card__header">
            <span class="path-badge">{{ $t('strategyNew.recommendedBadge') }}</span>
            <h2>{{ $t('strategyNew.templateTitle') }}</h2>
            <p>{{ $t('strategyNew.templateHint') }}</p>
          </div>
          <div class="path-card__body">
            <div class="path-checklist">
              <span class="path-check">{{ $t('strategyNew.templateChecklist.one') }}</span>
              <span class="path-check">{{ $t('strategyNew.templateChecklist.two') }}</span>
              <span class="path-check">{{ $t('strategyNew.templateChecklist.three') }}</span>
            </div>
            <button
              data-test="open-template-picker"
              class="btn btn-primary"
              type="button"
              :disabled="templateState.loading"
              @click="templatePickerOpen = true"
            >
              <span v-if="templateState.loading" class="btn-spinner"></span>
              {{ $t('strategyNew.templateAction') }}
            </button>
            <p v-if="templateState.error" class="form-message error">{{ templateState.error }}</p>
          </div>
        </article>

        <article class="card path-card">
          <div class="path-card__header">
            <h2>{{ $t('strategyNew.importTitle') }}</h2>
            <p>{{ $t('strategyNew.importHint') }}</p>
          </div>
          <div class="path-card__body">
            <div class="import-visual">
              <div class="import-visual__icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
              </div>
              <p class="import-visual__text">{{ $t('strategyNew.importNote') }}</p>
            </div>
            <div class="tag-row">
              <span class="pill">.py</span>
              <span class="pill">.zip</span>
              <span class="pill pill--accent">.qys</span>
            </div>
            <div class="path-checklist">
              <span class="path-check">{{ $t('strategyNew.importChecklist.one') }}</span>
              <span class="path-check">{{ $t('strategyNew.importChecklist.two') }}</span>
              <span class="path-check">{{ $t('strategyNew.importChecklist.three') }}</span>
            </div>
            <RouterLink class="btn btn-primary" to="/strategies/import">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              {{ $t('strategyNew.importAction') }}
            </RouterLink>
          </div>
        </article>
      </div>

      <section class="card guide-card">
        <button data-test="guide-toggle" class="guide-toggle" type="button" @click="isGuideOpen = !isGuideOpen">
          <div class="guide-toggle__copy">
            <p class="guide-eyebrow">{{ $t('strategyNew.guideTitle') }}</p>
            <h2>{{ $t('strategyNew.guideIntro') }}</h2>
            <p class="guide-toggle__hint">{{ $t('strategyNew.guideHint') }}</p>
          </div>
          <span class="guide-toggle__icon" :class="{ 'guide-toggle__icon--open': isGuideOpen }">⌄</span>
        </button>

        <div v-if="isGuideOpen" class="guide-content">
          <div class="guide-grid">
            <div class="guide-section">
              <h3>{{ $t('strategyNew.guideExecutionTitle') }}</h3>
              <p>{{ $t('strategyNew.guideExecutionBody') }}</p>
              <ol class="guide-list guide-list--ordered">
                <li>{{ $t('strategyNew.guideStep1') }}</li>
                <li>{{ $t('strategyNew.guideStep2') }}</li>
                <li>{{ $t('strategyNew.guideStep3') }}</li>
              </ol>
            </div>
            <div class="guide-section">
              <h3>{{ $t('strategyNew.guideExampleTitle') }}</h3>
              <pre class="guide-code"><code>{{ minimalGuideCode }}</code></pre>
            </div>
          </div>

          <div class="guide-grid">
            <div class="guide-section">
              <h3>{{ $t('strategyNew.guideApiTitle') }}</h3>
              <ul class="guide-list">
                <li>{{ $t('strategyNew.guideApiCtx') }}</li>
                <li>{{ $t('strategyNew.guideApiData') }}</li>
                <li>{{ $t('strategyNew.guideApiOrder') }}</li>
              </ul>
            </div>
            <div class="guide-section">
              <h3>{{ $t('strategyNew.guideErrorsTitle') }}</h3>
              <ul class="guide-list">
                <li>{{ $t('strategyNew.guideErrorEntrypoint') }}</li>
                <li>{{ $t('strategyNew.guideErrorSyntax') }}</li>
                <li>{{ $t('strategyNew.guideErrorReturn') }}</li>
              </ul>
            </div>
          </div>

          <div class="guide-actions">
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
      </section>

      <div v-if="templatePickerOpen" class="template-picker-backdrop" @click.self="templatePickerOpen = false">
        <div class="card template-picker">
          <div class="template-picker__header">
            <div>
              <p class="guide-eyebrow">{{ $t('strategyNew.templatePickerTitle') }}</p>
              <h2>{{ $t('strategyNew.templatePickerSubtitle') }}</h2>
            </div>
            <button class="btn btn-secondary" type="button" @click="templatePickerOpen = false">
              {{ $t('common.close') }}
            </button>
          </div>

          <div class="template-grid">
            <button
              v-for="template in templates"
              :key="template.id"
              :data-test="`template-card-${template.id}`"
              class="template-card"
              type="button"
              @click="handleTemplateSelect(template)"
            >
              <h3>{{ $t(template.nameKey) }}</h3>
              <p>{{ $t(template.descriptionKey) }}</p>
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, h, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRouter } from 'vue-router'
import { analyzeStrategyImport } from '../api/strategies'
import { strategyTemplates, type StrategyTemplateDefinition } from '../lib/strategyTemplates'

const { t } = useI18n()
const router = useRouter()

const templates = strategyTemplates
const templatePickerOpen = ref(false)
const isGuideOpen = ref(false)
const templateState = ref({
  loading: false,
  error: '',
})

const minimalGuideCode = computed(() => `from qysp import Order


def on_bar(ctx, data):
    if data.close > data.open:
        return [Order(symbol=data.symbol, side="buy", volume=1)]
    return []`)

async function handleTemplateSelect(template: StrategyTemplateDefinition) {
  templateState.value = {
    loading: true,
    error: '',
  }
  try {
    const file = new File([template.code], template.filename, { type: 'text/x-python' })
    const analysis = await analyzeStrategyImport(file)
    sessionStorage.setItem(
      `strategy-import:${analysis.draftImportId}`,
      JSON.stringify({
        ...analysis,
        metadataCandidates: {
          ...(analysis.metadataCandidates || {}),
          name: template.defaultName,
          symbol: (analysis.metadataCandidates?.symbol as string) || template.defaultSymbol,
          category: (analysis.metadataCandidates?.category as string) || template.category,
          tags: Array.isArray(analysis.metadataCandidates?.tags) && analysis.metadataCandidates?.tags.length
            ? analysis.metadataCandidates?.tags
            : template.tags,
        },
      })
    )
    templatePickerOpen.value = false
    await router.push({
      name: 'strategy-import-confirm',
      query: {
        draftImportId: analysis.draftImportId,
        source: 'template',
        template: template.slug,
      },
    })
  } catch (error: any) {
    templateState.value.error = error?.message || t('strategyNew.templateError')
  } finally {
    templateState.value.loading = false
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
  'stroke-linejoin': 'round',
}, [
  h('path', { d: 'M19 12H5' }),
  h('path', { d: 'm12 19-7-7 7-7' }),
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

.path-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-lg);
}

.path-card {
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.path-card__header {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.path-card__header h2,
.path-card__header p,
.guide-eyebrow,
.guide-toggle h2,
.template-card h3,
.template-card p,
.guide-section h3,
.guide-section p,
.guide-toggle__hint {
  margin: 0;
}

.path-card__body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.path-badge {
  width: fit-content;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(64, 162, 255, 0.12);
  color: var(--color-accent);
  font-size: var(--font-size-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.path-checklist,
.guide-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.path-check {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.path-check::before {
  content: '•';
  margin-right: 8px;
  color: var(--color-accent);
}

.import-visual {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
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
}

.import-visual__text,
.guide-toggle__hint,
.guide-section p {
  color: var(--color-text-muted);
}

.tag-row {
  display: flex;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.pill {
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.pill--accent {
  color: var(--color-accent);
}

.guide-card {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-lg);
}

.guide-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  padding: 0;
  border: none;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.guide-toggle__copy {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.guide-eyebrow {
  color: var(--color-accent);
  font-size: var(--font-size-xs);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.guide-toggle__icon {
  font-size: 1.4rem;
  transition: transform 0.2s ease;
}

.guide-toggle__icon--open {
  transform: rotate(180deg);
}

.guide-content {
  margin-top: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.guide-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-lg);
}

.guide-list {
  margin: var(--spacing-sm) 0 0;
  padding-left: 18px;
}

.guide-list--ordered {
  list-style: decimal;
}

.guide-code {
  margin: 0;
  padding: var(--spacing-md);
  border-radius: var(--radius-lg);
  background: rgba(7, 17, 27, 0.94);
  color: #f8fbff;
  overflow-x: auto;
}

.guide-actions {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.template-picker-backdrop {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-lg);
  background: rgba(12, 18, 32, 0.55);
  backdrop-filter: blur(6px);
  z-index: 40;
}

.template-picker {
  width: min(920px, 100%);
  padding: var(--spacing-lg);
}

.template-picker__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-md);
}

.template-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  padding: var(--spacing-lg);
  text-align: left;
  cursor: pointer;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.template-card:hover {
  transform: translateY(-2px);
  border-color: var(--color-accent);
  box-shadow: var(--shadow-md);
}

.template-card p {
  color: var(--color-text-muted);
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: white;
  animation: spin 0.8s linear infinite;
}

.form-message {
  margin: 0;
  font-size: var(--font-size-sm);
}

.error {
  color: var(--color-danger);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 900px) {
  .path-grid,
  .guide-grid,
  .template-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .page-header,
  .template-picker__header {
    flex-direction: column;
  }
}
</style>

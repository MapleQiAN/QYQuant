<template>
  <section class="strategy-writing-guide">
    <div class="container">
      <header class="page-header">
        <div class="header-copy">
          <p class="eyebrow">{{ t('pageTitle.strategies') }}</p>
          <h1 class="page-title">{{ t('strategyWritingGuide.title') }}</h1>
          <p class="page-subtitle">{{ t('strategyWritingGuide.subtitle') }}</p>
        </div>

        <RouterLink class="btn btn-secondary back-link" :to="{ name: 'strategy-new' }">
          <ArrowLeftIcon />
          {{ t('strategyWritingGuide.back') }}
        </RouterLink>
      </header>

      <div class="guide-grid">
        <article class="card guide-card guide-card--summary">
          <div class="card-header">
            <h2>{{ t('strategyWritingGuide.summaryTitle') }}</h2>
            <p class="hint">{{ t('strategyWritingGuide.summaryText') }}</p>
          </div>

          <ul class="detail-list">
            <li v-for="point in summaryPointKeys" :key="point">
              {{ t(point) }}
            </li>
          </ul>
        </article>

        <article class="card guide-card">
          <div class="card-header">
            <h2>{{ t('strategyWritingGuide.scriptTitle') }}</h2>
          </div>
          <pre class="guide-snippet"><code>{{ scriptFileSnippet }}</code></pre>
        </article>

        <article class="card guide-card">
          <div class="card-header">
            <h2>{{ t('strategyWritingGuide.handlerTitle') }}</h2>
          </div>
          <pre class="guide-snippet"><code>{{ onBarSnippet }}</code></pre>
        </article>

        <article class="card guide-card">
          <div class="card-header">
            <h2>{{ t('strategyWritingGuide.uploadTitle') }}</h2>
            <p class="hint">{{ t('strategyWritingGuide.uploadText') }}</p>
          </div>

          <ol class="detail-list detail-list--ordered">
            <li v-for="step in uploadStepKeys" :key="step">
              {{ t(step) }}
            </li>
          </ol>
        </article>

        <article class="card guide-card">
          <div class="card-header">
            <h2>{{ t('strategyWritingGuide.advancedTitle') }}</h2>
            <p class="hint">{{ t('strategyWritingGuide.advancedText') }}</p>
          </div>

          <ul class="detail-list">
            <li v-for="step in advancedPointKeys" :key="step">
              {{ t(step) }}
            </li>
          </ul>
        </article>

        <article class="card guide-card">
          <div class="card-header">
            <h2>{{ t('strategyWritingGuide.packageTitle') }}</h2>
          </div>
          <pre class="guide-snippet"><code>{{ packageTreeSnippet }}</code></pre>
        </article>

        <article class="card guide-card">
          <div class="card-header">
            <h2>{{ t('strategyWritingGuide.checklistTitle') }}</h2>
            <p class="hint">{{ t('strategyWritingGuide.checklistText') }}</p>
          </div>

          <ul class="detail-list">
            <li v-for="item in checklistKeys" :key="item">
              {{ t(item) }}
            </li>
          </ul>
        </article>

        <article id="spec-reference" class="card guide-card guide-card--spec">
          <div class="card-header">
            <h2>{{ t('strategyWritingGuide.specTitle') }}</h2>
            <p class="hint">{{ t('strategyWritingGuide.specText') }}</p>
          </div>

          <div class="spec-note">
            <span class="spec-note__label">{{ t('strategyWritingGuide.specPathLabel') }}</span>
            <code class="spec-note__path">docs/strategy-format/README.md</code>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { h } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

const { t } = useI18n()

const summaryPointKeys = [
  'strategyWritingGuide.summaryPoint1',
  'strategyWritingGuide.summaryPoint2',
  'strategyWritingGuide.summaryPoint3',
]

const uploadStepKeys = [
  'strategyWritingGuide.uploadStep1',
  'strategyWritingGuide.uploadStep2',
  'strategyWritingGuide.uploadStep3',
]

const advancedPointKeys = [
  'strategyWritingGuide.advancedPoint1',
  'strategyWritingGuide.advancedPoint2',
  'strategyWritingGuide.advancedPoint3',
]

const checklistKeys = [
  'strategyWritingGuide.checklistItem1',
  'strategyWritingGuide.checklistItem2',
  'strategyWritingGuide.checklistItem3',
]

const scriptFileSnippet = `strategy.py`

const onBarSnippet = `from qysp import BarData, Order, StrategyContext

def on_bar(ctx: StrategyContext, data: BarData) -> list[Order]:
    threshold = float(ctx.parameters.get("threshold", 1.0))
    if data.close > threshold:
        return [ctx.buy(data.symbol, quantity=1)]
    return []`

const packageTreeSnippet = `my-strategy/
├── strategy.json
└── src/
   └── strategy.py`

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
.strategy-writing-guide {
  width: 100%;
}

.container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-lg);
}

.header-copy {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.page-title {
  margin: 0;
  font-size: var(--font-size-xxl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.page-subtitle {
  margin: 0;
  font-size: var(--font-size-md);
  color: var(--color-text-muted);
  max-width: 760px;
  line-height: 1.6;
}

.back-link {
  flex-shrink: 0;
}

.eyebrow {
  margin: 0;
  font-size: var(--font-size-xs);
  font-weight: 600;
  color: var(--color-text-muted);
}

.guide-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-lg);
}

.guide-card {
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.guide-card--summary,
.guide-card--spec {
  grid-column: 1 / -1;
}

.card-header h2 {
  margin: 0 0 var(--spacing-xs);
  font-size: var(--font-size-lg);
  color: var(--color-text-primary);
}

.hint {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  line-height: 1.5;
}

.detail-list {
  margin: 0;
  padding-left: 1.25rem;
  display: grid;
  gap: var(--spacing-xs);
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.detail-list--ordered {
  list-style: decimal;
}

.guide-snippet {
  margin: 0;
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text-primary);
  font-family: var(--font-mono);
  font-size: var(--font-size-xs);
  line-height: 1.6;
  overflow: auto;
}

.spec-link {
  align-self: flex-start;
}

.spec-note {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.spec-note__label {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.spec-note__path {
  font-family: var(--font-mono);
  font-size: var(--font-size-xs);
  color: var(--color-accent);
}

@media (max-width: 900px) {
  .page-header {
    flex-direction: column;
  }

  .guide-grid {
    grid-template-columns: 1fr;
  }
}
</style>

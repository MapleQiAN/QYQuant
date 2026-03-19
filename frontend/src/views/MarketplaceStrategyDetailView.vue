<template>
  <section class="marketplace-strategy-detail">
    <div class="container">
      <div class="page-header">
        <div class="title-block">
          <div class="eyebrow">Marketplace strategy</div>
          <div class="headline-row">
            <h1 class="page-title">{{ strategy?.title || 'Strategy detail' }}</h1>
            <VerifiedBadge v-if="strategy?.isVerified" />
          </div>
          <p v-if="strategy?.description" class="page-subtitle">{{ strategy.description }}</p>
        </div>

        <div class="cta-block">
          <div v-if="strategy?.alreadyImported" class="import-state" data-test="imported-state">
            Already in strategy library
          </div>
          <button
            v-if="!strategy?.alreadyImported"
            class="btn btn-primary detail-cta"
            data-test="detail-cta"
            type="button"
            :disabled="busy"
            @click="handleImport"
          >
            {{ ctaLabel }}
          </button>
          <template v-else>
            <button
              class="btn btn-secondary detail-cta imported-cta"
              data-test="detail-cta"
              type="button"
              disabled
            >
              Already in strategy library
            </button>
            <button
              class="btn btn-link direct-backtest-link"
              data-test="direct-backtest-link"
              type="button"
              @click="goToBacktestConfiguration"
            >
              Direct backtest
            </button>
          </template>
        </div>
      </div>

      <div v-if="error" class="card feedback error">{{ error }}</div>
      <div v-else-if="loading && !strategy" class="card feedback">Loading marketplace strategy...</div>

      <template v-else-if="strategy">
        <div class="meta-strip">
          <div class="author-chip">
            <img
              v-if="strategy.author.avatarUrl"
              :src="strategy.author.avatarUrl"
              alt=""
              class="author-avatar"
            />
            <div v-else class="author-avatar placeholder">{{ authorInitial }}</div>
            <div>
              <div class="meta-label">Author</div>
              <div class="meta-value">{{ strategy.author.nickname }}</div>
            </div>
          </div>
          <div class="meta-chip">
            <div class="meta-label">Category</div>
            <div class="meta-value">{{ strategy.category || 'uncategorized' }}</div>
          </div>
          <div class="meta-chip">
            <div class="meta-label">Published</div>
            <div class="meta-value">{{ strategy.createdAt || 'Unknown' }}</div>
          </div>
        </div>

        <div class="content-grid">
          <div class="chart-panel">
            <EquityCurveChart :points="chartPoints" />
          </div>

          <aside class="metrics-panel">
            <div class="metrics-header">
              <div class="section-title">Display metrics</div>
              <p class="section-copy">The publisher-selected snapshot for fast evaluation.</p>
            </div>

            <div class="metric-grid">
              <article
                v-for="metric in metricEntries"
                :key="metric.key"
                class="metric-card"
              >
                <div class="metric-label">{{ metric.label }}</div>
                <div class="metric-value">{{ metric.value }}</div>
              </article>
            </div>
          </aside>
        </div>

        <div class="card detail-panel">
          <div class="section-title">About this strategy</div>
          <p class="detail-description">{{ strategy.description || 'No description provided.' }}</p>
          <div class="tag-row">
            <span v-for="tag in strategy.tags" :key="tag" class="pill">{{ tag }}</span>
          </div>
        </div>
      </template>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import EquityCurveChart from '../components/backtest/EquityCurveChart.vue'
import VerifiedBadge from '../components/strategy/VerifiedBadge.vue'
import { useMarketplaceStore } from '../stores'
import { useUserStore } from '../stores/user'

const route = useRoute()
const router = useRouter()
const marketplaceStore = useMarketplaceStore()
const userStore = useUserStore()
const strategyId = computed(() => String(route.params.strategyId || route.query.strategy_id || ''))

onMounted(async () => {
  if (!strategyId.value) return
  try {
    await Promise.all([
      marketplaceStore.fetchStrategyDetail(strategyId.value),
      marketplaceStore.fetchEquityCurve(strategyId.value),
    ])
  } catch {
    // Store error state is rendered by the view.
  }
  if (!marketplaceStore.error && userStore.profile.id) {
    try {
      await marketplaceStore.checkImportStatus(strategyId.value)
    } catch {
      // Import status check failure is non-critical.
    }
  }
})

onBeforeUnmount(() => {
  marketplaceStore.reset()
})

const strategy = computed(() => marketplaceStore.currentStrategy)
const loading = computed(() => marketplaceStore.loading || marketplaceStore.curveLoading)
const busy = computed(() => loading.value || marketplaceStore.importLoading || marketplaceStore.importStatusLoading)
const error = computed(() => marketplaceStore.error)

const ctaLabel = computed(() => {
  if (marketplaceStore.importLoading) {
    return 'Importing...'
  }
  return 'Free backtest trial'
})

const authorInitial = computed(() => {
  const nickname = strategy.value?.author?.nickname || ''
  return nickname.slice(0, 1).toUpperCase() || 'Q'
})

const chartPoints = computed(() => {
  return marketplaceStore.equityCurve.dates.map((date, index) => {
    const timestamp = typeof date === 'number' ? date : Date.parse(String(date))
    const equity = marketplaceStore.equityCurve.values[index] ?? 0
    return {
      timestamp: Number.isFinite(timestamp) ? timestamp : index,
      equity,
      benchmark_equity: equity,
    }
  })
})

const metricEntries = computed(() => {
  const metrics = strategy.value?.displayMetrics || {}
  const preferred = [
    ['totalReturn', 'Total return'],
    ['maxDrawdown', 'Max drawdown'],
    ['sharpeRatio', 'Sharpe ratio'],
    ['winRate', 'Win rate'],
  ]
  const entries: Array<{ key: string; label: string; value: string }> = []
  const seen = new Set<string>()

  for (const [key, label] of preferred) {
    if (metrics[key] === undefined || metrics[key] === null) continue
    entries.push({
      key,
      label,
      value: formatMetricValue(key, metrics[key]),
    })
    seen.add(key)
  }

  for (const [key, value] of Object.entries(metrics)) {
    if (seen.has(key) || value === undefined || value === null) continue
    entries.push({
      key,
      label: humanizeMetricKey(key),
      value: formatMetricValue(key, value),
    })
  }

  return entries
})

async function handleImport() {
  if (!strategy.value) return
  const result = await marketplaceStore.importStrategy(strategy.value.id)
  await router.push(result.redirectTo || buildBacktestConfigurePath(result.strategyId))
}

async function goToBacktestConfiguration() {
  if (!strategy.value?.importedStrategyId) return
  await router.push(buildBacktestConfigurePath(strategy.value.importedStrategyId))
}

function humanizeMetricKey(key: string) {
  return key
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/[_-]+/g, ' ')
    .replace(/^\w/, (char) => char.toUpperCase())
}

function formatMetricValue(key: string, value: string | number | boolean | null) {
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No'
  }
  if (typeof value === 'number') {
    if (key.toLowerCase().includes('rate') || key.toLowerCase().includes('return') || key.toLowerCase().includes('drawdown')) {
      return `${value}%`
    }
    return Number.isInteger(value) ? String(value) : value.toFixed(2)
  }
  return String(value)
}

function buildBacktestConfigurePath(importedStrategyId: string) {
  return `/backtest/configure?strategy_id=${encodeURIComponent(importedStrategyId)}`
}
</script>

<style scoped>
.marketplace-strategy-detail {
  width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-lg);
  align-items: flex-start;
  margin-bottom: var(--spacing-xl);
}

.title-block {
  max-width: 760px;
}

.eyebrow {
  margin-bottom: var(--spacing-xs);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.headline-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.page-title {
  margin: 0;
  font-size: calc(var(--font-size-xxl) + 0.5rem);
  color: var(--color-text-primary);
}

.page-subtitle {
  margin: var(--spacing-sm) 0 0;
  color: var(--color-text-secondary);
  line-height: 1.7;
}

.cta-block {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--spacing-sm);
}

.detail-cta {
  background: #1A1A1A;
  min-width: 220px;
}

.imported-cta {
  background: #d4d4d8;
  color: #3f3f46;
}

.import-state {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(15, 118, 110, 0.1);
  color: #0f766e;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.direct-backtest-link {
  padding: 0;
  min-width: auto;
  color: #0f172a;
  text-decoration: underline;
}

.feedback {
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.feedback.error {
  color: var(--color-danger);
}

.meta-strip {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) repeat(2, minmax(0, 1fr));
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.author-chip,
.meta-chip,
.detail-panel,
.metrics-panel {
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

.author-chip,
.meta-chip {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
}

.author-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
}

.author-avatar.placeholder {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 118, 110, 0.1);
  color: #0f766e;
  font-weight: var(--font-weight-semibold);
}

.meta-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.meta-value {
  margin-top: 4px;
  color: var(--color-text-primary);
  font-weight: var(--font-weight-semibold);
  word-break: break-word;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(320px, 0.9fr);
  gap: var(--spacing-lg);
  align-items: start;
}

.chart-panel :deep(.equity-chart) {
  border-radius: var(--radius-lg);
}

.metrics-panel {
  padding: var(--spacing-lg);
}

.metrics-header {
  margin-bottom: var(--spacing-md);
}

.section-title {
  margin: 0;
  font-size: var(--font-size-lg);
  color: var(--color-text-primary);
}

.section-copy {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-muted);
  line-height: 1.6;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-sm);
}

.metric-card {
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  background:
    linear-gradient(180deg, rgba(15, 118, 110, 0.08), rgba(255, 255, 255, 0.92));
  border: 1px solid rgba(15, 118, 110, 0.12);
}

.metric-label {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.metric-value {
  margin-top: var(--spacing-xs);
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1.1;
}

.detail-panel {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-lg);
}

.detail-description {
  margin: var(--spacing-sm) 0 0;
  color: var(--color-text-secondary);
  line-height: 1.8;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-md);
}

.pill {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  background: #fff;
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
}

@media (max-width: 1100px) {
  .content-grid,
  .meta-strip {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .page-header,
  .cta-block {
    display: flex;
    flex-direction: column;
    align-items: stretch;
  }

  .metric-grid {
    grid-template-columns: 1fr;
  }
}
</style>

<template>
  <section class="marketplace-strategy-detail">
    <div class="container">
      <div class="page-header">
        <div class="title-block">
          <div class="eyebrow">{{ $t('marketplace.detail.eyebrow') }}</div>
          <div class="headline-row">
            <h1 class="page-title">{{ strategy?.title || $t('marketplace.detail.titleFallback') }}</h1>
            <VerifiedBadge v-if="strategy?.isVerified" />
          </div>
          <p v-if="strategy?.description" class="page-subtitle">{{ strategy.description }}</p>
        </div>

        <div class="cta-block">
          <button
            v-if="canReport"
            class="btn btn-ghost detail-cta report-cta"
            data-test="open-report"
            type="button"
            :disabled="busy"
            @click="openReportDialog"
          >
            {{ $t('marketplace.reportStrategy') }}
          </button>
          <template v-if="!strategy?.alreadyImported">
            <button
              class="btn btn-accent detail-cta cta-trial"
              data-test="detail-cta-trial"
              type="button"
              :disabled="busy"
              @click="handleTrialBacktest"
            >
              <span v-if="marketplaceStore.trialBacktestLoading" class="cta-trial__spinner"></span>
              <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              {{ trialCtaLabel }}
            </button>
            <button
              class="btn btn-secondary detail-cta"
              data-test="detail-cta-import"
              type="button"
              :disabled="busy"
              @click="handleImport"
            >
              {{ importCtaLabel }}
            </button>
            <button
              class="btn btn-ghost detail-cta-link"
              data-test="detail-cta-discussions"
              type="button"
              @click="scrollToDiscussions"
            >
              {{ $t('marketplace.detail.discussionsCta') }}
            </button>
          </template>
          <template v-else>
            <div class="import-state" data-test="imported-state">
              <span class="import-state__dot"></span>
              {{ $t('marketplace.detail.alreadyImported') }}
            </div>
            <div class="import-rights" data-test="detail-import-rights">
              <div class="import-rights__title">{{ $t('marketplace.detail.importRightsTitle') }}</div>
              <p>{{ $t('marketplace.detail.importRightsRuntimeOnly') }}</p>
              <p>{{ $t('marketplace.detail.importRightsNoSource') }}</p>
            </div>
            <button
              class="btn btn-primary detail-cta imported-cta"
              data-test="detail-cta"
              type="button"
              disabled
            >
              {{ $t('marketplace.detail.alreadyImported') }}
            </button>
            <button
              class="btn btn-ghost direct-backtest-link"
              data-test="direct-backtest-link"
              type="button"
              @click="goToBacktestConfiguration"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
              {{ $t('marketplace.detail.directBacktest') }}
            </button>
          </template>
        </div>
      </div>

      <div v-if="error" class="card feedback error">{{ error }}</div>
      <div v-else-if="loading && !strategy" class="card feedback">{{ $t('marketplace.detail.loadingStrategy') }}</div>

      <template v-else-if="strategy">
        <div class="meta-strip">
          <div class="author-chip">
            <span class="chip__accent"></span>
            <img
              v-if="strategy.author.avatarUrl"
              :src="strategy.author.avatarUrl"
              alt=""
              class="author-avatar"
            />
            <div v-else class="author-avatar placeholder">{{ authorInitial }}</div>
            <div>
              <div class="meta-label">{{ $t('marketplace.detail.authorLabel') }}</div>
              <div class="meta-value">{{ strategy.author.nickname }}</div>
            </div>
          </div>
          <div class="meta-chip">
            <span class="chip__accent chip__accent--secondary"></span>
            <div class="meta-label">{{ $t('marketplace.detail.categoryLabel') }}</div>
            <div class="meta-value">{{ strategy.category || $t('marketplace.detail.uncategorized') }}</div>
          </div>
          <div class="meta-chip">
            <span class="chip__accent chip__accent--accent"></span>
            <div class="meta-label">{{ $t('marketplace.detail.publishedLabel') }}</div>
            <div class="meta-value">{{ strategy.createdAt || $t('marketplace.detail.unknownDate') }}</div>
          </div>
        </div>

        <div class="content-grid">
          <div class="card chart-panel">
            <div class="panel-header">
              <span class="panel-header__accent"></span>
              <span class="panel-header__icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
              </span>
              <h3 class="panel-title">{{ $t('marketplace.detail.equityCurveTitle') }}</h3>
            </div>
            <div class="chart-panel__body">
              <EquityCurveChart :points="chartPoints" />
            </div>
          </div>

          <aside class="card metrics-panel">
            <div class="panel-header">
              <span class="panel-header__accent panel-header__accent--accent"></span>
              <span class="panel-header__icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/></svg>
              </span>
              <h3 class="panel-title">{{ $t('marketplace.detail.displayMetricsTitle') }}</h3>
            </div>
            <div class="metrics-body">
              <p class="metrics-hint">{{ $t('marketplace.detail.displayMetricsHint') }}</p>
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
            </div>
          </aside>
        </div>

        <div class="card detail-panel">
          <div class="panel-header">
            <span class="panel-header__accent panel-header__accent--secondary"></span>
            <span class="panel-header__icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            </span>
            <h3 class="panel-title">{{ $t('marketplace.detail.aboutTitle') }}</h3>
          </div>
          <div class="detail-panel__body">
            <p class="detail-description">{{ strategy.description || $t('marketplace.detail.noDescription') }}</p>
            <div class="tag-row">
              <span v-for="tag in strategy.tags" :key="tag" class="pill">{{ tag }}</span>
            </div>
          </div>
        </div>

        <div
          ref="discussionsSection"
          class="card detail-panel discussions-panel"
          data-test="detail-discussions-section"
        >
          <div class="panel-header">
            <span class="panel-header__accent panel-header__accent--accent"></span>
            <span class="panel-header__icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            </span>
            <h3 class="panel-title">{{ $t('marketplace.detail.discussionsTitle') }}</h3>
          </div>
          <div class="detail-panel__body">
            <p class="detail-description">{{ $t('marketplace.detail.discussionsHint') }}</p>
          </div>
        </div>

        <div v-if="reportDialogOpen" class="report-dialog">
          <div class="report-dialog__panel">
            <div class="panel-header">
              <span class="panel-header__accent" style="background:var(--color-danger)"></span>
              <h3 class="panel-title">{{ $t('marketplace.detail.reportDialogTitle') }}</h3>
            </div>
            <p class="report-dialog__hint">{{ $t('marketplace.detail.reportDialogHint') }}</p>
            <textarea
              v-model="reportReason"
              data-test="report-reason"
              rows="4"
              class="field-input"
              :placeholder="$t('marketplace.reportReasonPlaceholder')"
            />
            <div class="report-dialog__actions">
              <button type="button" class="btn btn-ghost" @click="closeReportDialog">{{ $t('common.cancel') }}</button>
              <button
                type="button"
                class="btn btn-danger"
                data-test="submit-report"
                :disabled="busy"
                @click="submitReport"
              >
                {{ $t('marketplace.reportStrategy') }}
              </button>
            </div>
          </div>
        </div>
      </template>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import EquityCurveChart from '../components/backtest/EquityCurveChart.vue'
import VerifiedBadge from '../components/strategy/VerifiedBadge.vue'
import { toast } from '../lib/toast'
import { useMarketplaceStore } from '../stores'
import { useUserStore } from '../stores/user'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
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
const busy = computed(() =>
  loading.value
  || marketplaceStore.importLoading
  || marketplaceStore.trialBacktestLoading
  || marketplaceStore.importStatusLoading
  || marketplaceStore.reportLoading
)
const error = computed(() => marketplaceStore.error)
const reportReason = ref('')
const reportDialogOpen = ref(false)
const discussionsSection = ref<HTMLElement | null>(null)
const canReport = computed(() => Boolean(strategy.value?.canReport))

const trialCtaLabel = computed(() => {
  if (marketplaceStore.trialBacktestLoading) {
    return t('marketplace.detail.trialLaunching')
  }
  return t('marketplace.detail.freeBacktestTrial')
})

const importCtaLabel = computed(() => {
  if (marketplaceStore.importLoading) {
    return t('marketplace.detail.importing')
  }
  return t('marketplace.importStrategy')
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
    ['totalReturn', t('marketplace.detail.metricTotalReturn')],
    ['maxDrawdown', t('marketplace.detail.metricMaxDrawdown')],
    ['sharpeRatio', t('marketplace.detail.metricSharpeRatio')],
    ['winRate', t('marketplace.detail.metricWinRate')],
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
  toast.success(t('marketplace.detail.importSuccessToast'))
  await router.push(result.redirectTo || buildBacktestConfigurePath(result.strategyId))
}

async function handleTrialBacktest() {
  if (!strategy.value) return
  const result = await marketplaceStore.launchTrialBacktest(strategy.value.id, { params: {} })
  await router.push({
    name: 'backtest-report',
    params: { jobId: result.jobId },
  })
}

async function goToBacktestConfiguration() {
  if (!strategy.value?.importedStrategyId) return
  await router.push(buildBacktestConfigurePath(strategy.value.importedStrategyId))
}

function scrollToDiscussions() {
  discussionsSection.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function openReportDialog() {
  reportDialogOpen.value = true
}

function closeReportDialog() {
  reportDialogOpen.value = false
  reportReason.value = ''
}

async function submitReport() {
  if (!strategy.value) return
  const reason = reportReason.value.trim()
  if (reason.length < 10 || reason.length > 500) {
    toast.error(t('marketplace.detail.reportReasonLengthError'))
    return
  }

  try {
    await marketplaceStore.reportStrategy(strategy.value.id, reason)
    toast.success(t('marketplace.detail.reportSuccessToast'))
    closeReportDialog()
  } catch (error) {
    toast.error(getErrorMessage(error))
  }
}

function humanizeMetricKey(key: string) {
  return key
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/[_-]+/g, ' ')
    .replace(/^\w/, (char) => char.toUpperCase())
}

function formatMetricValue(key: string, value: string | number | boolean | null) {
  if (typeof value === 'boolean') {
    return value ? t('marketplace.detail.booleanYes') : t('marketplace.detail.booleanNo')
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

function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message
  }
  return t('marketplace.detail.reportFailToast')
}
</script>

<style scoped>
/* ── Animations ── */
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── Page Layout ── */
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
  margin: 0 0 6px;
  font-size: var(--font-size-xs);
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-accent);
}

.headline-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.page-title {
  margin: 0 0 var(--spacing-xs);
  font-size: var(--font-size-xxxl);
  font-weight: 800;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
}

.page-subtitle {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  line-height: 1.7;
}

/* ── CTA Block — right-aligned action column ── */
.cta-block {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--spacing-sm);
}

.detail-cta {
  min-width: 220px;
}

.cta-trial {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-full);
  background: var(--color-accent);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-weight: 700;
  letter-spacing: 0.03em;
  cursor: pointer;
  transition: all 0.2s;
  width: 100%;
  justify-content: center;
  font-family: var(--font-family);
}

.cta-trial:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
  box-shadow: var(--shadow-lg);
}

.cta-trial:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.cta-trial__spinner {
  width: 14px;
  height: 14px;
  border: 2px solid var(--color-border-light);
  border-top-color: var(--color-text-primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}

.report-cta {
  font-size: var(--font-size-xs);
}

.imported-cta {
  opacity: 0.5;
  cursor: not-allowed;
}

.import-state {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 8px 14px;
  border: 2px solid var(--color-primary-border);
  border-radius: var(--radius-full);
  background: var(--color-primary-bg);
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.import-state__dot {
  width: 6px;
  height: 6px;
  border-radius: 0;
  background: var(--color-primary);
  flex-shrink: 0;
}

.direct-backtest-link,
.detail-cta-link {
  min-width: auto;
}

.direct-backtest-link svg,
.detail-cta-link svg {
  vertical-align: -2px;
}

/* ── Feedback ── */
.feedback {
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.feedback.error {
  color: var(--color-danger);
}

/* ── Meta Strip — Bauhaus chip row ── */
.meta-strip {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) repeat(2, minmax(0, 1fr));
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.author-chip,
.meta-chip {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-md);
  position: relative;
  overflow: hidden;
}

.author-chip::after,
.meta-chip::after {
  content: "";
  position: absolute;
  height: 4px;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--color-primary);
}

.meta-chip::after {
  background: var(--color-secondary);
}

.meta-chip:last-child::after {
  background: var(--color-accent);
}

.chip__accent {
  width: 6px;
  height: 6px;
  border-radius: 0;
  background: var(--color-primary);
  flex-shrink: 0;
}

.chip__accent--secondary {
  background: var(--color-secondary);
}

.chip__accent--accent {
  background: var(--color-accent);
}

.author-avatar {
  width: 48px;
  height: 48px;
  border-radius: 0;
  border: 2px solid var(--color-border);
  object-fit: cover;
}

.author-avatar.placeholder {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary-bg);
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

.meta-label {
  font-size: var(--font-size-xs);
  font-weight: 800;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.meta-value {
  margin-top: 4px;
  color: var(--color-text-primary);
  font-weight: var(--font-weight-semibold);
  word-break: break-word;
}

/* ── Import Rights — Bauhaus inset panel ── */
.import-rights {
  max-width: 280px;
  padding: var(--spacing-md);
  border: 2px solid var(--color-primary);
  border-radius: 0;
  background: var(--color-primary-bg);
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  line-height: 1.5;
}

.import-rights p {
  margin: var(--spacing-xs) 0 0;
}

.import-rights__title {
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

/* ── Content Grid ── */
.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(320px, 0.9fr);
  gap: var(--spacing-lg);
  align-items: start;
}

/* ── Panel Cards — Bauhaus geometric structure ── */
.chart-panel,
.metrics-panel,
.detail-panel {
  padding: 0;
  overflow: hidden;
  position: relative;
}

.chart-panel::after,
.metrics-panel::after,
.detail-panel::after {
  content: "";
  position: absolute;
  height: 5px;
  bottom: 0;
  left: 0;
  right: 0;
}

.chart-panel::after {
  background: var(--color-primary);
}

.metrics-panel::after {
  background: var(--color-accent);
}

.detail-panel::after {
  background: var(--color-secondary);
}

.discussions-panel::after {
  background: var(--color-accent) !important;
}

/* ── Panel Header — matches BacktestsView ── */
.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 2px solid var(--color-border);
  background: var(--color-surface-elevated);
}

.panel-header__accent {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
  flex-shrink: 0;
}

.panel-header__accent--accent {
  background: var(--color-accent);
}

.panel-header__accent--secondary {
  background: var(--color-secondary);
}

.panel-header__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 2px solid var(--color-border);
  border-radius: 0;
  background: var(--color-surface);
  color: var(--color-primary);
  flex-shrink: 0;
}

.panel-title {
  margin: 0;
  font-size: var(--font-size-md);
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

/* ── Chart Panel ── */
.chart-panel__body {
  padding: var(--spacing-md);
}

.chart-panel__body :deep(.equity-chart) {
  border-radius: 0;
}

/* ── Metrics Panel ── */
.metrics-body {
  padding: var(--spacing-md) var(--spacing-lg) var(--spacing-lg);
}

.metrics-hint {
  margin: 0 0 var(--spacing-md);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  line-height: 1.5;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-sm);
}

.metric-card {
  padding: var(--spacing-md);
  border: 2px solid var(--color-primary-border);
  border-radius: 0;
  background: var(--color-primary-bg);
  transition: border-color var(--transition-fast), background var(--transition-fast);
}

.metric-card:hover {
  border-color: var(--color-primary);
  background: var(--color-surface);
}

.metric-label {
  font-size: var(--font-size-xs);
  font-weight: 800;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.metric-value {
  margin-top: var(--spacing-xs);
  font-size: 1.8rem;
  font-weight: 800;
  color: var(--color-text-primary);
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}

/* ── Detail Panel ── */
.detail-panel {
  margin-top: var(--spacing-lg);
}

.detail-panel__body {
  padding: var(--spacing-md) var(--spacing-lg) var(--spacing-lg);
}

.detail-description {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-md);
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
  padding: 4px 10px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-full);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  white-space: nowrap;
}

/* ── Report Dialog — Bauhaus modal ── */
.report-dialog {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-lg);
  background: var(--color-overlay);
  z-index: 100;
}

.report-dialog__panel {
  width: min(520px, 100%);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-xl);
  overflow: hidden;
}

.report-dialog__panel .panel-header {
  border-bottom: 2px solid var(--color-border);
}

.report-dialog__hint {
  margin: var(--spacing-md) var(--spacing-lg) 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.report-dialog__panel textarea {
  width: calc(100% - var(--spacing-lg) * 2);
  margin: var(--spacing-md) var(--spacing-lg) 0;
  padding: 9px 12px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-family: var(--font-family);
  resize: vertical;
  box-sizing: border-box;
}

.report-dialog__panel textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-bg);
}

.report-dialog__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg) var(--spacing-lg);
}

/* ── Responsive ── */
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

<template>
  <section class="view">
    <div class="container">
      <div class="page-header">
        <div class="header-left">
          <div class="header-badges">
            <span class="eyebrow">{{ $t('backtestReport.eyebrow') }}</span>
            <span class="job-chip">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
              JOB&nbsp;<span class="job-chip__id">{{ jobId }}</span>
            </span>
          </div>
          <h1 class="page-title">{{ $t('backtestReport.title') }}</h1>
          <p class="page-subtitle">{{ $t('backtestReport.subtitle', { jobId }) }}</p>
        </div>
      </div>

      <div v-if="store.reportLoading" class="state-block">
        <div class="state-block__spinner"></div>
        <span>{{ $t('backtestReport.loading') }}</span>
      </div>
      <div v-else-if="store.reportError" class="state-block state-block--error">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        {{ store.reportError }}
      </div>

      <template v-else-if="report">
        <div v-if="isGuidedMode" class="guided-success">
          <div class="guided-success__icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          </div>
          <div class="guided-success__content">
            <strong>{{ $t('backtestReport.guidedSuccessTitle') }}</strong>
            <p>{{ $t('backtestReport.guidedSuccessHint') }}</p>
          </div>
          <button class="btn btn-primary" type="button" @click="finishGuidedOnboarding">
            {{ $t('backtestReport.finishGuidedOnboarding') }}
          </button>
        </div>

        <ErrorDisplay
          v-if="report.status === 'failed' && report.error"
          :error="report.error"
          :supported-packages="store.supportedPackages"
          :loading="store.supportedPackagesLoading"
        />

        <template v-else>
          <!-- Core Metrics Grid -->
          <div
            :class="['metrics-grid', { 'onboarding-highlight': userStore.onboardingHighlightTarget === 'backtest-results-section' }]"
            data-onboarding-target="backtest-results-section"
          >
            <StatCard
              v-for="metric in coreMetrics"
              :key="metric.label"
              :label="metric.label"
              :show-disclaimer="metric.showDisclaimer"
              :show-sign="metric.showSign"
              :suffix="metric.suffix"
              :value="metric.value"
              :variant="metric.variant"
            >
              <template #label-extra>
                <MetricTooltip :metric-key="metric.metricKey" />
              </template>
            </StatCard>
          </div>

          <!-- K-line Chart -->
          <div v-if="hasKlineData" class="chart-section">
            <div class="chart-section__header">
              <div class="chart-section__title-group">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="4" height="16"/><rect x="10" y="8" width="4" height="8"/><rect x="18" y="2" width="4" height="12"/></svg>
                <span class="chart-section__title">{{ $t('backtestReport.klineTitle') }}</span>
              </div>
              <span class="chart-section__subtitle">{{ $t('backtestReport.klineSubtitle') }}</span>
            </div>
            <div class="chart-block">
              <KlinePlaceholder
                :data="report.kline || []"
                :trades="report.trades || []"
                :symbol="report.symbol || 'BTCUSDT'"
                :timeframe="report.interval || '1d'"
              />
            </div>
          </div>

          <!-- Equity Curve -->
          <div class="chart-section">
            <div class="chart-section__header">
              <div class="chart-section__title-group">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                <span class="chart-section__title">{{ $t('backtestReport.equityCurveTitle') }}</span>
              </div>
              <span class="chart-section__subtitle">{{ $t('backtestReport.equityCurveSubtitle') }}</span>
            </div>
            <EquityCurveChart class="chart-block" :points="report.equity_curve || []" :trades="report.trades || []" />
          </div>

          <!-- Drawdown Chart -->
          <div v-if="hasDrawdownData" class="chart-section">
            <div class="chart-section__header">
              <div class="chart-section__title-group">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg>
                <span class="chart-section__title">{{ $t('backtestReport.drawdownTitle') }}</span>
              </div>
              <span class="chart-section__subtitle">{{ $t('backtestReport.drawdownSubtitle') }}</span>
            </div>
            <DrawdownChart :points="report.equity_curve || []" />
          </div>

          <!-- Trade List -->
          <TradeTable :trades="report.trades || []" />

          <!-- Detailed Metrics -->
          <details class="details-card">
            <summary class="details-summary">
              <div class="details-summary__left">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
                {{ $t('backtestReport.viewAllMetrics') }}
              </div>
              <span class="details-count">{{ $t('backtestReport.metricsCount', { count: detailedMetrics.length }) }}</span>
            </summary>
            <div class="details-grid">
              <div v-for="metric in detailedMetrics" :key="metric.label" class="detail-row">
                <span class="detail-label">
                  {{ metric.label }}
                  <MetricTooltip :metric-key="metric.metricKey" />
                </span>
                <span class="detail-value">{{ metric.value }}</span>
              </div>
            </div>
          </details>

          <DisclaimerFooter />
        </template>
      </template>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import StatCard from '../components/StatCard.vue'
import EquityCurveChart from '../components/backtest/EquityCurveChart.vue'
import DrawdownChart from '../components/backtest/DrawdownChart.vue'
import TradeTable from '../components/backtest/TradeTable.vue'
import KlinePlaceholder from '../components/KlinePlaceholder.vue'
import ErrorDisplay from '../components/backtest/ErrorDisplay.vue'
import DisclaimerFooter from '../components/disclaimer/DisclaimerFooter.vue'
import MetricTooltip from '../components/help/MetricTooltip.vue'
import { useUserStore } from '../stores'
import { useBacktestsStore } from '../stores/backtests'

const { t } = useI18n()

const route = useRoute()
const router = useRouter()
const store = useBacktestsStore()
const userStore = useUserStore()
const jobId = String(route.params.jobId || '')
const isGuidedMode = route.query.guided === 'true'

const report = computed(() => store.report)
const summary = computed(() => report.value?.result_summary ?? {})

const hasKlineData = computed(() => (report.value?.kline?.length ?? 0) > 0)
const hasDrawdownData = computed(() =>
  (report.value?.equity_curve ?? []).some((p) => p.drawdown !== undefined)
)

function formatMetric(value: number | undefined, digits = 2, suffix = '') {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return '--'
  }
  return `${Number(value).toFixed(digits)}${suffix}`
}

const coreMetrics = computed(() => ([
  {
    label: t('backtestReport.metrics.totalReturn'),
    metricKey: 'total_return',
    value: formatMetric(summary.value.totalReturn, 2),
    suffix: '%',
    variant: 'up' as const,
    showSign: true,
    showDisclaimer: true
  },
  {
    label: t('backtestReport.metrics.winRate'),
    metricKey: 'win_rate',
    value: formatMetric(summary.value.winRate, 2),
    suffix: '%',
    variant: 'info' as const,
    showSign: false,
    showDisclaimer: false
  },
  {
    label: t('backtestReport.metrics.maxDrawdown'),
    metricKey: 'max_drawdown',
    value: formatMetric(summary.value.maxDrawdown, 2),
    suffix: '%',
    variant: 'down' as const,
    showSign: true,
    showDisclaimer: false
  },
  {
    label: t('backtestReport.metrics.sharpeRatio'),
    metricKey: 'sharpe_ratio',
    value: formatMetric(summary.value.sharpeRatio, 2),
    variant: 'default' as const,
    showSign: false,
    showDisclaimer: false
  }
]))

const detailedMetrics = computed(() =>
  [
    [t('backtestReport.metrics.annualizedReturn'), 'annualized_return', formatMetric(summary.value.annualizedReturn, 2, '%')],
    [t('backtestReport.metrics.volatility'), 'volatility', formatMetric(summary.value.volatility, 2, '%')],
    [t('backtestReport.metrics.sortinoRatio'), 'sortino_ratio', formatMetric(summary.value.sortinoRatio, 2)],
    [t('backtestReport.metrics.calmarRatio'), 'calmar_ratio', formatMetric(summary.value.calmarRatio, 2)],
    [t('backtestReport.metrics.profitLossRatio'), 'profit_loss_ratio', formatMetric(summary.value.profitLossRatio, 2)],
    [t('backtestReport.metrics.maxConsecutiveLosses'), 'max_consecutive_losses', formatMetric(summary.value.maxConsecutiveLosses, 0)],
    [t('backtestReport.metrics.totalTrades'), 'total_trades', formatMetric(summary.value.totalTrades, 0)],
    [t('backtestReport.metrics.alpha'), 'alpha', formatMetric(summary.value.alpha, 2)],
    [t('backtestReport.metrics.beta'), 'beta', formatMetric(summary.value.beta, 2)]
  ].map(([label, metricKey, value]) => ({ label, metricKey, value }))
)

async function finishGuidedOnboarding() {
  await userStore.markOnboardingCompleted(true)
  userStore.finishGuidedBacktest()
  await router.push({ name: 'dashboard' })
}

onMounted(() => {
  if (jobId) {
    void store.loadReport(jobId)
  }
  void store.loadSupportedPackages()
})
</script>

<style scoped>
@keyframes spin {
  to { transform: rotate(360deg); }
}
@keyframes slide-up {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.view {
  width: 100%;
}

/* ── Page Header ── */
.page-header {
  margin-bottom: var(--spacing-xl);
}

.header-badges {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.eyebrow {
  font-size: var(--font-size-xs);
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-accent);
}

.job-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-surface-elevated);
  font-size: 11px;
  color: var(--color-text-muted);
}

.job-chip__id {
  font-family: 'Space Mono', monospace;
  color: var(--color-text-secondary);
}

.page-title {
  margin: 0;
  font-size: var(--font-size-xxl);
  font-weight: 800;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
}

.page-subtitle {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

/* ── State Blocks ── */
.state-block {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xl);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  justify-content: center;
}

.state-block--error {
  color: var(--color-danger);
  border-color: rgba(255, 59, 59, 0.2);
  background: rgba(255, 59, 59, 0.04);
}

.state-block__spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

/* ── Guided Success ── */
.guided-success {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.25);
  border-radius: var(--radius-lg);
  animation: slide-up 0.3s ease;
}

.guided-success__icon {
  color: var(--color-success);
  flex-shrink: 0;
  display: flex;
}

.guided-success__content {
  flex: 1;
}

.guided-success__content strong {
  display: block;
  color: var(--color-success);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.guided-success__content p {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

/* ── Metrics Grid ── */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
}

/* ── Chart Section ── */
.chart-section {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  margin-bottom: var(--spacing-lg);
}

.chart-section__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-border-light);
  background: var(--color-surface-elevated);
}

.chart-section__title-group {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-accent);
}

.chart-section__title {
  font-size: var(--font-size-sm);
  font-weight: 700;
  color: var(--color-text-primary);
}

.chart-section__subtitle {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.chart-block {
  padding: var(--spacing-sm);
}

/* ── Details Card ── */
.details-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  margin-bottom: var(--spacing-lg);
}

.details-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  cursor: pointer;
  user-select: none;
  background: var(--color-surface-elevated);
  border-bottom: 1px solid transparent;
  transition: background 0.15s;
  list-style: none;
  color: var(--color-text-primary);
  font-weight: 700;
  font-size: var(--font-size-sm);
}

.details-summary::-webkit-details-marker {
  display: none;
}

.details-card[open] .details-summary {
  border-bottom-color: var(--color-border-light);
}

.details-summary:hover {
  background: var(--color-surface-hover);
}

.details-summary__left {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-primary);
}

.details-count {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  background: var(--color-surface-active);
  padding: 3px 10px;
  border-radius: 999px;
}

.details-grid {
  padding: var(--spacing-md) var(--spacing-lg);
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-md);
  padding: 11px var(--spacing-sm);
  border-bottom: 1px solid var(--color-border-light);
}

.detail-row:nth-child(odd) {
  border-right: 1px solid var(--color-border-light);
  padding-right: var(--spacing-lg);
}

.detail-row:nth-last-child(-n+2) {
  border-bottom: none;
}

.detail-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.detail-value {
  color: var(--color-text-primary);
  font-weight: 700;
  font-size: var(--font-size-sm);
  font-variant-numeric: tabular-nums;
  font-family: 'Space Mono', monospace;
}

/* ── Responsive ── */
@media (max-width: 900px) {
  .metrics-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .details-grid {
    grid-template-columns: 1fr;
  }

  .detail-row:nth-child(odd) {
    border-right: none;
    padding-right: var(--spacing-sm);
  }

  .detail-row:nth-last-child(-n+2) {
    border-bottom: 1px solid var(--color-border-light);
  }

  .detail-row:last-child {
    border-bottom: none;
  }
}

@media (max-width: 640px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .guided-success {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>

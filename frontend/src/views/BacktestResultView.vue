<template>
  <section class="view">
    <div class="container">
      <div class="page-header">
        <div>
          <p class="eyebrow">Backtest Report</p>
          <h1 class="page-title">Backtest Report</h1>
          <p class="page-subtitle">Job {{ jobId }} equity curve, core metrics, and full report summary.</p>
        </div>
      </div>

      <div v-if="store.reportLoading" class="card state-card">Loading report...</div>
      <div v-else-if="store.reportError" class="card state-card error">{{ store.reportError }}</div>
      <template v-else-if="report">
        <div v-if="isGuidedMode" class="card guided-success">
          <strong>你完成了第一次量化回测。</strong>
          <p>重点先看累计收益率、最大回撤和夏普比率，理解“收益”和“波动”之间的关系。</p>
          <button class="btn btn-primary" type="button" @click="finishGuidedOnboarding">
            完成新手引导
          </button>
        </div>

        <ErrorDisplay
          v-if="report.status === 'failed' && report.error"
          :error="report.error"
          :supported-packages="store.supportedPackages"
          :loading="store.supportedPackagesLoading"
        />

        <template v-else>
          <div :class="['metrics-grid', { 'onboarding-highlight': userStore.onboardingHighlightTarget === 'backtest-results-section' }]" data-onboarding-target="backtest-results-section">
          <article v-for="metric in coreMetrics" :key="metric.label" class="metric-card">
            <span class="metric-label">
              {{ metric.label }}
              <MetricTooltip :metric-key="metric.metricKey" />
            </span>
            <strong class="metric-value" :class="metric.tone">{{ metric.value }}</strong>
          </article>
          </div>

          <EquityCurveChart class="chart-block" :points="report.equity_curve || []" :trades="report.trades || []" />

          <details class="card details-card">
            <summary>View all 11 metrics</summary>
            <div class="details-grid">
              <div v-for="metric in detailedMetrics" :key="metric.label" class="detail-item">
                <span class="detail-label">
                  {{ metric.label }}
                  <MetricTooltip :metric-key="metric.metricKey" />
                </span>
                <span class="detail-value">{{ metric.value }}</span>
              </div>
            </div>
          </details>

          <div class="card disclaimer-card">
            <p class="disclaimer-title">Disclaimer</p>
            <p class="disclaimer-text">{{ report.disclaimer }}</p>
          </div>
        </template>
      </template>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import EquityCurveChart from '../components/backtest/EquityCurveChart.vue'
import ErrorDisplay from '../components/backtest/ErrorDisplay.vue'
import MetricTooltip from '../components/help/MetricTooltip.vue'
import { useUserStore } from '../stores'
import { useBacktestsStore } from '../stores/backtests'

const route = useRoute()
const router = useRouter()
const store = useBacktestsStore()
const userStore = useUserStore()
const jobId = String(route.params.jobId || '')
const isGuidedMode = route.query.guided === 'true'

const report = computed(() => store.report)
const summary = computed(() => report.value?.result_summary ?? {})

function formatMetric(value: number | undefined, digits = 2, suffix = '') {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return '--'
  }
  return `${Number(value).toFixed(digits)}${suffix}`
}

const coreMetrics = computed(() => ([
  {
    label: 'Total Return',
    metricKey: 'total_return',
    value: formatMetric(summary.value.totalReturn, 2, '%'),
    tone: (summary.value.totalReturn ?? 0) >= 0 ? 'positive' : 'negative'
  },
  {
    label: 'Max Drawdown',
    metricKey: 'max_drawdown',
    value: formatMetric(summary.value.maxDrawdown, 2, '%'),
    tone: 'negative'
  },
  {
    label: 'Sharpe Ratio',
    metricKey: 'sharpe_ratio',
    value: formatMetric(summary.value.sharpeRatio, 2),
    tone: 'neutral'
  }
]))

const detailedMetrics = computed(() =>
  [
    ['Total Return', 'total_return', formatMetric(summary.value.totalReturn, 2, '%')],
    ['Annualized Return', 'annualized_return', formatMetric(summary.value.annualizedReturn, 2, '%')],
    ['Max Drawdown', 'max_drawdown', formatMetric(summary.value.maxDrawdown, 2, '%')],
    ['Sharpe Ratio', 'sharpe_ratio', formatMetric(summary.value.sharpeRatio, 2)],
    ['Volatility', 'volatility', formatMetric(summary.value.volatility, 2, '%')],
    ['Sortino Ratio', 'sortino_ratio', formatMetric(summary.value.sortinoRatio, 2)],
    ['Calmar Ratio', 'calmar_ratio', formatMetric(summary.value.calmarRatio, 2)],
    ['Win Rate', 'win_rate', formatMetric(summary.value.winRate, 2, '%')],
    ['Profit/Loss Ratio', 'profit_loss_ratio', formatMetric(summary.value.profitLossRatio, 2)],
    ['Max Consecutive Losses', 'max_consecutive_losses', formatMetric(summary.value.maxConsecutiveLosses, 0)],
    ['Total Trades', 'total_trades', formatMetric(summary.value.totalTrades, 0)]
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
.view {
  width: 100%;
}

.page-header {
  margin-bottom: var(--spacing-lg);
}

.eyebrow {
  margin: 0 0 6px;
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.page-title {
  margin: 0;
  font-size: var(--font-size-xl);
  color: var(--color-text-primary);
}

.page-subtitle {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-muted);
}

.state-card {
  padding: var(--spacing-lg);
}

.state-card.error {
  color: var(--color-danger);
}

.guided-success {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.guided-success p {
  margin: 6px 0 0;
  color: var(--color-text-secondary);
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.metric-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metric-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.metric-value {
  font-size: 2rem;
  line-height: 1;
  color: var(--color-text-primary);
}

.metric-value.positive {
  color: #0f766e;
}

.metric-value.negative {
  color: #b91c1c;
}

.metric-value.neutral {
  color: #1d4ed8;
}

.chart-block {
  margin-bottom: var(--spacing-lg);
}

.details-card {
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.details-card summary {
  cursor: pointer;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.details-grid {
  margin-top: var(--spacing-md);
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-sm) var(--spacing-lg);
}

.detail-item {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-sm);
  padding-bottom: var(--spacing-xs);
  border-bottom: 1px solid var(--color-border-light);
}

.detail-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--color-text-muted);
}

.detail-value {
  color: var(--color-text-primary);
  font-weight: var(--font-weight-semibold);
}

.disclaimer-card {
  padding: var(--spacing-md);
  border-left: 4px solid #f59e0b;
}

.disclaimer-title {
  margin: 0 0 var(--spacing-xs);
  color: var(--color-text-primary);
  font-weight: var(--font-weight-semibold);
}

.disclaimer-text {
  margin: 0;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

@media (max-width: 900px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .details-grid {
    grid-template-columns: 1fr;
  }
}
</style>

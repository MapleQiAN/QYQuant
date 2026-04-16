<template>
  <section ref="exportRoot" class="view">
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
        <div v-if="report && report.status !== 'failed'" class="header-actions" data-export-ignore="true">
          <button class="btn btn-secondary" type="button" data-test="export-html" @click="exportReportAsHtml">
            {{ $t('backtestReport.exportHtml') }}
          </button>
          <button class="btn btn-primary" type="button" data-test="export-pdf" @click="exportReportAsPdf">
            {{ $t('backtestReport.exportPdf') }}
          </button>
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
          <section class="report-summary">
            <div class="report-summary__hero">
              <div class="report-summary__copy">
                <div class="report-summary__meta">
                  <span class="summary-chip">{{ $t('backtestReport.generatedAt') }} · {{ completedAtLabel }}</span>
                  <span class="summary-chip">{{ $t('backtestReport.symbol') }} · {{ symbolLabel }}</span>
                  <span class="summary-chip">{{ $t('backtestReport.timeRange') }} · {{ timeRangeLabel }}</span>
                </div>
                <h2 class="report-summary__title">{{ $t('backtestReport.reportSummary') }}</h2>
                <p class="report-summary__subtitle">{{ $t('backtestReport.reportSummarySubtitle') }}</p>
              </div>

              <div class="quality-score-card">
                <span class="quality-score-card__label">{{ $t('backtestReport.qualityScore') }}</span>
                <div class="quality-score-card__value-row">
                  <strong class="quality-score-card__value">{{ qualityScore }}</strong>
                  <span class="quality-score-card__unit">{{ $t('backtestReport.scoreOutOf') }}</span>
                </div>
                <span :class="['quality-score-card__tone', toneClass(qualityTone)]">{{ qualityLabel }}</span>
              </div>
            </div>

            <div class="summary-facts">
              <article v-for="fact in snapshotFacts" :key="fact.label" class="summary-fact">
                <span class="summary-fact__label">{{ fact.label }}</span>
                <strong class="summary-fact__value">{{ fact.value }}</strong>
                <span :class="['summary-fact__note', toneClass(fact.tone)]">{{ fact.note }}</span>
              </article>
            </div>

            <article class="summary-conclusion">
              <div class="summary-conclusion__header">
                <div>
                  <span class="analysis-panel__eyebrow">{{ $t('backtestReport.executiveSummary') }}</span>
                  <h3 class="summary-conclusion__title">{{ summaryHeadline }}</h3>
                </div>
                <span :class="['summary-conclusion__pill', toneClass(qualityTone)]">{{ qualityLabel }}</span>
              </div>
              <p class="summary-conclusion__body">{{ summaryBody }}</p>
              <div class="summary-conclusion__tags">
                <span
                  v-for="tag in summaryTags"
                  :key="tag.label"
                  :class="['summary-conclusion__tag', toneClass(tag.tone)]"
                >
                  {{ tag.label }} · {{ tag.value }}
                </span>
              </div>
            </article>
          </section>

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

          <section class="analysis-grid">
            <article class="analysis-panel" data-test="report-insights">
              <div class="analysis-panel__header">
                <span class="analysis-panel__eyebrow">{{ $t('backtestReport.keyObservationsTitle') }}</span>
                <h3 class="analysis-panel__title">{{ $t('backtestReport.reportSummary') }}</h3>
                <p class="analysis-panel__subtitle">{{ $t('backtestReport.keyObservationsSubtitle') }}</p>
              </div>
              <div class="analysis-panel__body">
                <article v-for="item in insightItems" :key="item.title" :class="['insight-row', toneClass(item.tone)]">
                  <span class="insight-row__dot"></span>
                  <div class="insight-row__content">
                    <strong>{{ item.title }}</strong>
                    <p>{{ item.body }}</p>
                  </div>
                </article>
              </div>
            </article>

            <article class="analysis-panel" data-test="report-diagnostics">
              <div class="analysis-panel__header">
                <span class="analysis-panel__eyebrow">{{ $t('backtestReport.diagnosticsTitle') }}</span>
                <h3 class="analysis-panel__title">{{ $t('backtestReport.qualityScore') }}</h3>
                <p class="analysis-panel__subtitle">{{ $t('backtestReport.diagnosticsSubtitle') }}</p>
              </div>
              <div class="diagnostic-grid">
                <div v-for="row in diagnosticRows" :key="row.label" class="diagnostic-row">
                  <span class="diagnostic-row__label">{{ row.label }}</span>
                  <strong :class="['diagnostic-row__value', toneClass(row.tone)]">{{ row.value }}</strong>
                </div>
              </div>
            </article>
          </section>

          <section class="support-grid">
            <StrategyParamsPanel
              :strategy-id="strategyId"
              :version="strategyVersion"
              :symbols="strategySymbols"
              :interval="strategyInterval"
              :data-source="strategyDataSource"
              :params="strategyParamsFiltered"
            />

            <SignalStatsPanel :stats="signalStats" />

            <BenchmarkComparison :data="benchmarkComparison" />

            <RiskMetricsPanel :metrics="riskMetrics" />
          </section>

          <!-- K-line Chart -->
          <div v-if="hasKlineData" class="chart-section">
            <div class="chart-section__header">
              <div class="chart-section__title-group">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="4" height="16"/><rect x="10" y="8" width="4" height="8"/><rect x="18" y="2" width="4" height="12"/></svg>
                <span class="chart-section__title">{{ $t('backtestReport.klineTitle') }}</span>
              </div>
              <span class="chart-section__subtitle">{{ $t('backtestReport.klineSubtitle') }}</span>
            </div>
            <div class="chart-block chart-block--stacked">
              <KlinePlaceholder
                :data="report.kline || []"
                :trades="report.trades || []"
                :symbol="report.symbol || 'BTCUSDT'"
                :timeframe="report.interval || '1d'"
              />
              <TradeSignalList :signals="tradeMarkers" :holding-durations="tradeHoldingDurations" :cumulative-returns="cumulativeReturns" />
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

          <!-- Trade Distribution Charts -->
          <TradeDistributionCharts :distribution="tradeDistribution" />

          <!-- Detailed Metrics -->
          <section class="metrics-board">
            <div class="metrics-board__header">
              <div class="metrics-board__header-main">
                <span class="analysis-panel__eyebrow">{{ $t('backtestReport.metricsCount', { count: detailedMetrics.length }) }}</span>
                <h3 class="analysis-panel__title">{{ $t('backtestReport.metricBoardTitle') }}</h3>
              </div>
              <p class="metrics-board__subtitle">{{ $t('backtestReport.metricBoardSubtitle') }}</p>
            </div>
            <div class="metrics-board__grid">
              <article v-for="metric in detailedMetrics" :key="metric.label" class="metric-tile">
                <span class="metric-tile__label">
                  {{ metric.label }}
                  <MetricTooltip :metric-key="metric.metricKey" />
                </span>
                <strong :class="['metric-tile__value', toneClass(metric.tone)]">{{ metric.value }}</strong>
                <span class="metric-tile__caption">{{ metric.caption }}</span>
              </article>
            </div>
          </section>

          <DisclaimerFooter />
        </template>
      </template>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import StatCard from '../components/StatCard.vue'
import EquityCurveChart from '../components/backtest/EquityCurveChart.vue'
import DrawdownChart from '../components/backtest/DrawdownChart.vue'
import TradeSignalList from '../components/backtest/TradeSignalList.vue'
import TradeTable from '../components/backtest/TradeTable.vue'
import KlinePlaceholder from '../components/KlinePlaceholder.vue'
import ErrorDisplay from '../components/backtest/ErrorDisplay.vue'
import DisclaimerFooter from '../components/disclaimer/DisclaimerFooter.vue'
import MetricTooltip from '../components/help/MetricTooltip.vue'
import StrategyParamsPanel from '../components/backtest/StrategyParamsPanel.vue'
import SignalStatsPanel from '../components/backtest/SignalStatsPanel.vue'
import BenchmarkComparison from '../components/backtest/BenchmarkComparison.vue'
import RiskMetricsPanel from '../components/backtest/RiskMetricsPanel.vue'
import TradeDistributionCharts from '../components/backtest/TradeDistributionCharts.vue'
import { useUserStore } from '../stores'
import { mapTradesToMarkers, toEpochMs } from '../lib/chartIndicators'
import type { BacktestSummary } from '../types/Backtest'
import {
  computeSignalStats,
  computeBenchmarkComparison,
  computeRiskMetrics,
  computeTradeDistribution,
  computeTradeHoldingDurations,
  computeCumulativeReturns,
} from '../lib/backtestComputed'
import {
  downloadBacktestReportAsHtml,
  printBacktestReportAsPdf,
} from '../lib/backtestReportExport'
import { useBacktestsStore } from '../stores/backtests'

type Tone = 'positive' | 'negative' | 'warning' | 'neutral'

const { t } = useI18n()

const route = useRoute()
const router = useRouter()
const store = useBacktestsStore()
const userStore = useUserStore()
const jobId = String(route.params.jobId || '')
const isGuidedMode = route.query.guided === 'true'
const exportRoot = ref<HTMLElement | null>(null)

const report = computed(() => store.report)
const summary = computed<Partial<BacktestSummary>>(() => report.value?.result_summary ?? {})

const hasKlineData = computed(() => (report.value?.kline?.length ?? 0) > 0)
const hasDrawdownData = computed(() =>
  (report.value?.equity_curve ?? []).some((p) => p.drawdown !== undefined)
)

function formatMetric(value: number | undefined | null, digits = 2, suffix = '') {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return '--'
  }
  return `${Number(value).toFixed(digits)}${suffix}`
}

function numberOrNull(value: unknown): number | null {
  if (value === undefined || value === null || value === '') return null
  const n = Number(value)
  return Number.isFinite(n) ? n : null
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

function formatDateTime(value: string | number | undefined | null): string {
  if (!value) return '--'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return '--'
  return d.toLocaleString()
}

function formatRangeDate(value: string | number | null | undefined): string {
  if (!value) return '--'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return '--'
  return d.toLocaleDateString()
}

function formatPercent(value: number | null | undefined, digits = 2, showSign = false): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '--'
  const n = Number(value)
  const sign = showSign && n > 0 ? '+' : ''
  return `${sign}${n.toFixed(digits)}%`
}

function formatPlain(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '--'
  return Number(value).toFixed(digits)
}

function formatInteger(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '--'
  return Math.round(Number(value)).toString()
}

function toneClass(tone: Tone): string {
  return `tone-${tone}`
}

function toneFromSignedValue(value: number | null | undefined, invert = false): Tone {
  if (value === null || value === undefined) return 'neutral'
  const v = invert ? -value : value
  if (v > 0) return 'positive'
  if (v < 0) return 'negative'
  return 'neutral'
}

const points = computed(() => report.value?.equity_curve ?? [])
const trades = computed(() => report.value?.trades ?? [])
const klineBars = computed(() => report.value?.kline ?? [])
const tradeMarkers = computed(() => mapTradesToMarkers(klineBars.value, trades.value))
const reportParams = computed<Record<string, unknown>>(() => report.value?.params ?? {})
const firstPoint = computed(() => points.value[0] ?? null)
const lastPoint = computed(() => points.value[points.value.length - 1] ?? null)

const strategyReturn = computed(() => {
  const direct = numberOrNull(summary.value.totalReturn)
  if (direct !== null) {
    return direct
  }
  const start = numberOrNull(firstPoint.value?.equity)
  const end = numberOrNull(lastPoint.value?.equity)
  if (start === null || end === null || start === 0) {
    return null
  }
  return ((end - start) / start) * 100
})

const benchmarkReturn = computed(() => {
  const start = numberOrNull(firstPoint.value?.benchmark_equity)
  const end = numberOrNull(lastPoint.value?.benchmark_equity)
  if (start === null || end === null || start === 0) {
    return null
  }
  return ((end - start) / start) * 100
})

const excessReturn = computed(() => {
  if (strategyReturn.value === null || benchmarkReturn.value === null) {
    return null
  }
  return strategyReturn.value - benchmarkReturn.value
})

const currentDrawdown = computed(() => {
  const latest = numberOrNull(lastPoint.value?.drawdown)
  return latest ?? numberOrNull(summary.value.maxDrawdown)
})

const symbolLabel = computed(() => {
  const symbol = reportParams.value.symbol
  return typeof symbol === 'string' && symbol.trim() ? symbol : t('backtestReport.noSymbol')
})

const timeRangeLabel = computed(() => {
  const fromPointsStart = firstPoint.value ? formatRangeDate(firstPoint.value.timestamp) : '--'
  const fromPointsEnd = lastPoint.value ? formatRangeDate(lastPoint.value.timestamp) : '--'
  if (fromPointsStart !== '--' && fromPointsEnd !== '--') {
    return `${fromPointsStart} → ${fromPointsEnd}`
  }

  const paramsStart = formatRangeDate((reportParams.value.start_date as string | undefined) ?? null)
  const paramsEnd = formatRangeDate((reportParams.value.end_date as string | undefined) ?? null)
  if (paramsStart === '--' || paramsEnd === '--') {
    return '--'
  }
  return `${paramsStart} → ${paramsEnd}`
})

const durationDays = computed(() => {
  const start = firstPoint.value ? (toEpochMs(firstPoint.value.timestamp) ?? NaN) : NaN
  const end = lastPoint.value ? (toEpochMs(lastPoint.value.timestamp) ?? NaN) : NaN
  if (Number.isNaN(start) || Number.isNaN(end) || end < start) {
    return null
  }
  return Math.max(1, Math.round((end - start) / 86400000))
})

const buySignals = computed(() => tradeMarkers.value.filter((trade) => trade.side === 'buy').length)
const sellSignals = computed(() => tradeMarkers.value.filter((trade) => trade.side === 'sell').length)
const signalDensityLabel = computed(() => {
  if (!klineBars.value.length) {
    return '--'
  }
  return `${formatPlain((tradeMarkers.value.length / klineBars.value.length) * 100, 1)} / 100`
})

const signalStats = computed(() => computeSignalStats(trades.value, durationDays.value))
const benchmarkComparison = computed(() => computeBenchmarkComparison(points.value))
const riskMetrics = computed(() => computeRiskMetrics(trades.value))
const tradeDistribution = computed(() => computeTradeDistribution(trades.value, points.value))
const tradeHoldingDurations = computed(() => computeTradeHoldingDurations(trades.value))
const cumulativeReturns = computed(() => computeCumulativeReturns(trades.value))

const strategyId = computed(() => {
  const params = reportParams.value
  return typeof params.strategy_id === 'string' ? params.strategy_id : ''
})

const strategyVersion = computed(() => {
  const params = reportParams.value
  return typeof params.version === 'string' ? params.version : typeof params.strategy_version === 'string' ? params.strategy_version : ''
})

const strategySymbols = computed<string[]>(() => {
  const params = reportParams.value
  const symbols = params.symbols
  if (Array.isArray(symbols)) return symbols.filter((s): s is string => typeof s === 'string')
  if (typeof params.symbol === 'string') return [params.symbol]
  return []
})

const strategyInterval = computed(() => {
  const params = reportParams.value
  return typeof params.interval === 'string' ? params.interval : report.value?.interval ?? ''
})

const strategyDataSource = computed(() => {
  const params = reportParams.value
  return typeof params.data_source === 'string' ? params.data_source : ''
})

const strategyParamsFiltered = computed<Record<string, unknown>>(() => {
  const { strategy_id, version, strategy_version, symbols, symbol, interval, data_source, start_date, end_date, ...rest } = reportParams.value as Record<string, unknown>
  return rest
})

const qualityScore = computed(() => {
  const sharpe = numberOrNull(summary.value.sharpeRatio) ?? 0
  const totalReturn = strategyReturn.value ?? 0
  const drawdown = Math.abs(numberOrNull(summary.value.maxDrawdown) ?? 0)
  const winRate = numberOrNull(summary.value.winRate) ?? 50
  const profitLossRatio = numberOrNull(summary.value.profitLossRatio) ?? 1

  const raw =
    50 +
    clamp(sharpe * 12, -18, 28) +
    clamp(totalReturn * 0.35, -16, 18) -
    clamp(drawdown * 0.8, 0, 26) +
    clamp((winRate - 50) * 0.35, -8, 8) +
    clamp((profitLossRatio - 1) * 8, -6, 10)

  return Math.round(clamp(raw, 0, 100))
})

const qualityTone = computed<Tone>(() => {
  if (qualityScore.value >= 78) {
    return 'positive'
  }
  if (qualityScore.value >= 58) {
    return 'neutral'
  }
  if (qualityScore.value >= 40) {
    return 'warning'
  }
  return 'negative'
})

const qualityLabel = computed(() => {
  if (qualityScore.value >= 78) {
    return t('backtestReport.qualityExcellent')
  }
  if (qualityScore.value >= 58) {
    return t('backtestReport.qualityBalanced')
  }
  if (qualityScore.value >= 40) {
    return t('backtestReport.qualityFragile')
  }
  return t('backtestReport.qualityWeak')
})

const completedAtLabel = computed(() => formatDateTime(report.value?.completed_at))

const summaryHeadline = computed(() => {
  if (qualityScore.value >= 78 && (excessReturn.value ?? 0) > 0) {
    return t('backtestReport.executiveHeadlineStrong')
  }
  if (qualityScore.value >= 58) {
    return t('backtestReport.executiveHeadlineBalanced')
  }
  if ((strategyReturn.value ?? 0) > 0) {
    return t('backtestReport.executiveHeadlineFragile')
  }
  return t('backtestReport.executiveHeadlineWeak')
})

const summaryBody = computed(() =>
  t('backtestReport.executiveSummaryBody', {
    strategy: formatPercent(strategyReturn.value, 2, true),
    benchmark: formatPercent(benchmarkReturn.value, 2, true),
    excess: formatPercent(excessReturn.value, 2, true),
    drawdown: formatPercent(numberOrNull(summary.value.maxDrawdown), 2, true),
    winRate: formatPercent(numberOrNull(summary.value.winRate), 2),
  })
)

const summaryTags = computed(() => [
  {
    label: t('backtestReport.strategyVsBenchmark'),
    value: formatPercent(excessReturn.value, 2, true),
    tone: toneFromSignedValue(excessReturn.value),
  },
  {
    label: t('backtestReport.currentDrawdown'),
    value: formatPercent(currentDrawdown.value, 2, true),
    tone: toneFromSignedValue(currentDrawdown.value, true),
  },
  {
    label: t('backtestReport.metrics.totalTrades'),
    value: formatInteger(numberOrNull(summary.value.totalTrades) ?? trades.value.length),
    tone: 'neutral' as Tone,
  },
  {
    label: t('backtestReport.signalBalance'),
    value: signalDensityLabel.value,
    tone: 'neutral' as Tone,
  },
])

const snapshotFacts = computed(() => [
  {
    label: t('backtestReport.timeRange'),
    value: timeRangeLabel.value,
    note: durationDays.value ? `${durationDays.value} ${t('backtestReport.runningDays')}` : '--',
    tone: 'neutral' as Tone,
  },
  {
    label: t('backtestReport.benchmarkReturn'),
    value: formatPercent(benchmarkReturn.value, 2, true),
    note: `${t('backtestReport.returnSpread')} ${formatPercent(excessReturn.value, 2, true)}`,
    tone: toneFromSignedValue(excessReturn.value),
  },
  {
    label: t('backtestReport.signalBalance'),
    value: `${buySignals.value} / ${sellSignals.value}`,
    note: `${t('backtestReport.buySignals')} · ${t('backtestReport.sellSignals')}`,
    tone: 'neutral' as Tone,
  },
  {
    label: t('backtestReport.latestEquity'),
    value: formatPlain(numberOrNull(lastPoint.value?.equity), 2),
    note: `${t('backtestReport.holdingPeriod')} ${formatPlain(numberOrNull(summary.value.avgHoldingDays), 1)}`,
    tone: toneFromSignedValue(strategyReturn.value),
  },
])

const insightItems = computed(() => [
  {
    title: t('backtestReport.analysisReturnTitle'),
    body: t('backtestReport.analysisReturnBody', {
      strategy: formatPercent(strategyReturn.value, 2, true),
      benchmark: formatPercent(benchmarkReturn.value, 2, true),
      excess: formatPercent(excessReturn.value, 2, true),
    }),
    tone: toneFromSignedValue(excessReturn.value),
  },
  {
    title: t('backtestReport.analysisRiskTitle'),
    body: t('backtestReport.analysisRiskBody', {
      drawdown: formatPercent(numberOrNull(summary.value.maxDrawdown), 2, true),
      current: formatPercent(currentDrawdown.value, 2, true),
    }),
    tone: toneFromSignedValue(numberOrNull(summary.value.maxDrawdown), true),
  },
  {
    title: t('backtestReport.analysisTradeTitle'),
    body: t('backtestReport.analysisTradeBody', {
      trades: formatInteger(numberOrNull(summary.value.totalTrades) ?? trades.value.length),
      winRate: formatPercent(numberOrNull(summary.value.winRate)),
      profitLossRatio: formatMetric(numberOrNull(summary.value.profitLossRatio ?? summary.value.profitFactor), 2),
    }),
    tone: toneFromSignedValue((numberOrNull(summary.value.winRate) ?? 50) - 50),
  },
  {
    title: t('backtestReport.analysisTimingTitle'),
    body: t('backtestReport.analysisTimingBody', {
      range: timeRangeLabel.value,
      days: durationDays.value ?? '--',
    }),
    tone: 'neutral' as Tone,
  },
])

const diagnosticRows = computed(() => [
  {
    label: t('backtestReport.qualityScore'),
    value: `${qualityScore.value}${t('backtestReport.scoreOutOf')}`,
    tone: qualityTone.value,
  },
  {
    label: t('backtestReport.metrics.totalTrades'),
    value: formatInteger(numberOrNull(summary.value.totalTrades) ?? trades.value.length),
    tone: 'neutral' as Tone,
  },
  {
    label: t('backtestReport.metrics.volatility'),
    value: formatPercent(numberOrNull(summary.value.volatility)),
    tone: toneFromSignedValue(numberOrNull(summary.value.volatility), true),
  },
  {
    label: t('backtestReport.metrics.sortinoRatio'),
    value: formatMetric(numberOrNull(summary.value.sortinoRatio), 2),
    tone: toneFromSignedValue(numberOrNull(summary.value.sortinoRatio)),
  },
  {
    label: t('backtestReport.metrics.calmarRatio'),
    value: formatMetric(numberOrNull(summary.value.calmarRatio), 2),
    tone: toneFromSignedValue(numberOrNull(summary.value.calmarRatio)),
  },
  {
    label: t('backtestReport.holdingPeriod'),
    value: formatPlain(numberOrNull(summary.value.avgHoldingDays), 1),
    tone: 'neutral' as Tone,
  },
])

const coreMetrics = computed(() => ([
  {
    label: t('backtestReport.metrics.totalReturn'),
    metricKey: 'total_return',
    value: formatMetric(strategyReturn.value, 2),
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

const detailedMetrics = computed(() => [
  {
    label: t('backtestReport.metrics.annualizedReturn'),
    metricKey: 'annualized_return',
    value: formatMetric(summary.value.annualizedReturn, 2, '%'),
    tone: toneFromSignedValue(numberOrNull(summary.value.annualizedReturn)),
    caption: t('backtestReport.metricCaptionAnnualizedReturn'),
  },
  {
    label: t('backtestReport.metrics.volatility'),
    metricKey: 'volatility',
    value: formatMetric(summary.value.volatility, 2, '%'),
    tone: toneFromSignedValue(numberOrNull(summary.value.volatility), true),
    caption: t('backtestReport.metricCaptionVolatility'),
  },
  {
    label: t('backtestReport.metrics.sortinoRatio'),
    metricKey: 'sortino_ratio',
    value: formatMetric(summary.value.sortinoRatio, 2),
    tone: toneFromSignedValue(numberOrNull(summary.value.sortinoRatio)),
    caption: t('backtestReport.metricCaptionSortinoRatio'),
  },
  {
    label: t('backtestReport.metrics.calmarRatio'),
    metricKey: 'calmar_ratio',
    value: formatMetric(summary.value.calmarRatio, 2),
    tone: toneFromSignedValue(numberOrNull(summary.value.calmarRatio)),
    caption: t('backtestReport.metricCaptionCalmarRatio'),
  },
  {
    label: t('backtestReport.metrics.profitLossRatio'),
    metricKey: 'profit_loss_ratio',
    value: formatMetric(summary.value.profitLossRatio, 2),
    tone: toneFromSignedValue((numberOrNull(summary.value.profitLossRatio) ?? 1) - 1),
    caption: t('backtestReport.metricCaptionProfitLossRatio'),
  },
  {
    label: t('backtestReport.metrics.maxConsecutiveLosses'),
    metricKey: 'max_consecutive_losses',
    value: formatMetric(summary.value.maxConsecutiveLosses, 0),
    tone: toneFromSignedValue(numberOrNull(summary.value.maxConsecutiveLosses), true),
    caption: t('backtestReport.metricCaptionMaxConsecutiveLosses'),
  },
  {
    label: t('backtestReport.metrics.totalTrades'),
    metricKey: 'total_trades',
    value: formatMetric(summary.value.totalTrades, 0),
    tone: 'neutral' as Tone,
    caption: t('backtestReport.metricCaptionTotalTrades'),
  },
  {
    label: t('backtestReport.metrics.alpha'),
    metricKey: 'alpha',
    value: formatMetric(summary.value.alpha, 2),
    tone: toneFromSignedValue(numberOrNull(summary.value.alpha)),
    caption: t('backtestReport.metricCaptionAlpha'),
  },
  {
    label: t('backtestReport.metrics.beta'),
    metricKey: 'beta',
    value: formatMetric(summary.value.beta, 2),
    tone: toneFromSignedValue(Math.abs(numberOrNull(summary.value.beta) ?? 0) - 1, true),
    caption: t('backtestReport.metricCaptionBeta'),
  },
])

async function finishGuidedOnboarding() {
  await userStore.markOnboardingCompleted(true)
  userStore.finishGuidedBacktest()
  await router.push({ name: 'dashboard' })
}

function exportReportAsHtml() {
  if (!report.value || !exportRoot.value) {
    return
  }
  downloadBacktestReportAsHtml(exportRoot.value, {
    jobId,
    title: t('backtestReport.title'),
    filename: `backtest-report-${jobId}.html`,
  })
}

async function exportReportAsPdf() {
  if (!report.value || !exportRoot.value) {
    return
  }
  try {
    await printBacktestReportAsPdf(exportRoot.value, {
      jobId,
      title: t('backtestReport.title'),
      filename: `backtest-report-${jobId}.pdf`,
    })
  } catch (error) {
    console.error('Failed to export backtest PDF', error)
  }
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
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-md);
  flex-wrap: wrap;
  margin-bottom: var(--spacing-xl);
}

.header-left {
  flex: 1;
  min-width: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
  flex-shrink: 0;
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
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-primary);
}

.job-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border: 2px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-surface);
  font-size: 11px;
  font-weight: 800;
  color: var(--color-text-muted);
}

.job-chip__id {
  font-family: 'DM Mono', monospace;
  color: var(--color-primary);
}

.page-title {
  margin: 0;
  font-size: var(--font-size-xxl);
  font-weight: 900;
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
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  justify-content: center;
  box-shadow: var(--shadow-md);
}

.state-block--error {
  color: var(--color-danger);
  border-color: var(--color-danger);
  background: var(--color-danger-bg);
}

.state-block__spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--color-border-light);
  border-top-color: var(--color-primary);
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
  background: var(--color-success-bg);
  border: 2px solid var(--color-success);
  border-radius: var(--radius-lg);
  animation: slide-up 0.3s ease;
  box-shadow: var(--shadow-md);
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
  font-weight: 800;
}

.guided-success__content p {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.report-summary {
  display: grid;
  gap: var(--spacing-lg);
  padding: clamp(18px, 3vw, 28px);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-lg);
  position: relative;
  overflow: hidden;
  margin-bottom: var(--spacing-xl);
}

.report-summary::after {
  content: "";
  position: absolute;
  width: 180px;
  height: 180px;
  background: var(--color-danger);
  bottom: -70px;
  right: -50px;
  transform: rotate(25deg);
  border-radius: 22px;
  opacity: 0.12;
}

.report-summary__hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 180px;
  gap: var(--spacing-lg);
  position: relative;
  z-index: 1;
}

.report-summary__copy {
  display: grid;
  gap: var(--spacing-sm);
}

.report-summary__meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.summary-chip,
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 2px solid var(--color-border);
  background: var(--color-surface);
  font-size: var(--font-size-xs);
  font-weight: 700;
}

.report-summary__title {
  margin: 0;
  font-size: clamp(1.5rem, 2.2vw, 2.2rem);
  letter-spacing: -0.03em;
}

.report-summary__subtitle {
  max-width: 720px;
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-lg);
}

.quality-score-card {
  display: grid;
  gap: 8px;
  align-content: start;
  padding: 18px;
  border-radius: 14px;
  border: 2px solid var(--color-border);
  background: var(--color-surface);
  position: relative;
  text-align: center;
}

.quality-score-card::before {
  content: "";
  position: absolute;
  width: 40px;
  height: 40px;
  background: var(--color-primary);
  border-radius: 50%;
  top: -14px;
  right: -14px;
  opacity: 0.9;
}

.quality-score-card__label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.quality-score-card__value-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.quality-score-card__value {
  font-size: clamp(2.1rem, 4vw, 3rem);
  line-height: 1;
  letter-spacing: -0.05em;
}

.quality-score-card__unit {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.quality-score-card__tone {
  display: inline-flex;
  width: fit-content;
  padding: 5px 10px;
  border-radius: 999px;
  border: 1px solid currentColor;
  font-size: var(--font-size-xs);
  font-weight: 700;
}

.summary-facts {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border-top: 2px solid var(--color-border);
  position: relative;
  z-index: 1;
}

.summary-fact {
  display: grid;
  gap: 4px;
  padding: 18px 20px;
  border-right: 2px solid var(--color-border-light);
}

.summary-fact:last-child {
  border-right: none;
}

.summary-fact__label,
.analysis-panel__eyebrow,
.metric-tile__label,
.diagnostic-row__label {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.summary-fact__value {
  color: var(--color-text-primary);
  font-size: var(--font-size-xl);
  font-weight: 900;
  font-variant-numeric: tabular-nums;
  font-family: 'DM Mono', monospace;
}

.diagnostic-row__value {
  color: var(--color-text-primary);
  font-size: var(--font-size-lg);
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  font-family: 'DM Mono', monospace;
}

.summary-fact__note,
.metric-tile__caption {
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.summary-conclusion {
  display: grid;
  gap: 14px;
  padding: 22px 24px;
  border-top: 2px solid var(--color-border);
  position: relative;
  z-index: 1;
}

.summary-conclusion__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-md);
}

.summary-conclusion__title {
  margin: 6px 0 0;
  font-size: clamp(1.15rem, 2vw, 1.55rem);
  letter-spacing: -0.03em;
}

.summary-conclusion__pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 5px 14px;
  border-radius: 999px;
  border: 2px solid currentColor;
  font-size: var(--font-size-xs);
  font-weight: 800;
  white-space: nowrap;
}

.summary-conclusion__body {
  margin: 0;
  max-width: 900px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-lg);
  line-height: 1.7;
}

.summary-conclusion__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.summary-conclusion__tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 999px;
  border: 2px dashed #d0d0cc;
  background: var(--color-surface);
  font-size: var(--font-size-xs);
  font-weight: 700;
}

/* ── Metrics Grid ── */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

/* ── Chart Section ── */
.chart-section {
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  margin-bottom: var(--spacing-xl);
  box-shadow: var(--shadow-md);
}

.chart-section__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 2px solid var(--color-border);
  background: var(--color-surface-elevated);
}

.chart-section__header--feature {
  align-items: flex-start;
}

.chart-section__title-group {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-primary);
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

.chart-section__lead {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.chart-block {
  padding: var(--spacing-sm);
}

.chart-block--stacked {
  display: grid;
  gap: var(--spacing-md);
}

.market-stage__body {
  padding: var(--spacing-sm) var(--spacing-md);
}

.market-stage__primary {
  min-width: 0;
}

.market-stage__secondary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-md);
  padding: 0 var(--spacing-md) var(--spacing-md);
}

.signal-panel {
  display: grid;
  gap: var(--spacing-md);
  padding: 18px;
  border: 1px solid var(--color-border);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.02);
}

.signal-panel__header {
  display: grid;
  gap: 6px;
}

.signal-panel__title {
  margin: 0;
  font-size: var(--font-size-lg);
  color: var(--color-text-primary);
}

.signal-panel__subtitle,
.hover-empty {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.signal-stats,
.hover-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.signal-stat,
.hover-grid__item {
  display: grid;
  gap: 6px;
  padding: 12px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--color-border-light);
}

.signal-stat__label,
.hover-grid__item span,
.signal-latest__label,
.hover-signal__grid span,
.hover-signal__time {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.signal-stat__value,
.hover-grid__item strong {
  color: var(--color-text-primary);
  font-size: var(--font-size-lg);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.signal-latest,
.hover-card {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 18px;
  background:
    radial-gradient(circle at top right, rgba(54, 214, 182, 0.12), transparent 40%),
    rgba(6, 12, 24, 0.34);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.signal-latest__header,
.hover-card__headline,
.hover-signal__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.signal-latest__side,
.hover-signal__side {
  font-size: var(--font-size-xs);
  font-weight: 700;
}

.signal-latest__value {
  color: var(--color-text-primary);
  font-size: var(--font-size-xxl);
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.signal-latest__meta,
.hover-card__change {
  font-size: var(--font-size-sm);
}

.hover-signals {
  display: grid;
  gap: 10px;
}

.hover-signal {
  display: grid;
  gap: 10px;
  padding: 12px;
  border-radius: 16px;
  border: 1px solid var(--color-border-light);
  background: rgba(255, 255, 255, 0.03);
}

.hover-signal__grid {
  display: grid;
  grid-template-columns: auto auto;
  gap: 4px 12px;
  align-items: center;
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.analysis-panel,
.metrics-board {
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  overflow: hidden;
  box-shadow: var(--shadow-md);
  position: relative;
}

.analysis-panel {
  overflow: hidden;
}

.analysis-panel:nth-child(1)::before {
  content: "";
  position: absolute;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--color-accent);
  top: -18px;
  left: -18px;
  opacity: 0.15;
  z-index: 0;
}

.analysis-panel:nth-child(2)::before {
  content: "";
  position: absolute;
  width: 50px;
  height: 50px;
  background: var(--color-primary);
  bottom: -16px;
  right: -16px;
  transform: rotate(20deg);
  border-radius: 10px;
  opacity: 0.12;
  z-index: 0;
}

.analysis-panel__header,
.metrics-board__header {
  display: grid;
  gap: 6px;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 2px solid var(--color-border);
  background: var(--color-surface-elevated);
  position: relative;
  z-index: 1;
}

.analysis-panel__title {
  margin: 0;
  font-size: var(--font-size-xl);
}

.analysis-panel__subtitle,
.metrics-board__subtitle {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.analysis-panel__body {
  display: grid;
  gap: 0;
  padding: 4px 0 var(--spacing-md);
}

.insight-row {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr);
  gap: 12px;
  padding: 0 var(--spacing-lg) var(--spacing-md);
}

.insight-row__dot {
  width: 10px;
  height: 10px;
  margin-top: 6px;
  border-radius: 50%;
  background: var(--color-primary);
  border: 2px solid var(--color-border);
  flex-shrink: 0;
}

.insight-row.tone-positive .insight-row__dot { background: var(--color-positive); }
.insight-row.tone-negative .insight-row__dot { background: var(--color-negative); }
.insight-row.tone-warning .insight-row__dot { background: var(--color-accent); }

.insight-row__content strong {
  display: block;
  margin-bottom: 6px;
  color: var(--color-text-primary);
}

.insight-row__content p {
  margin: 0;
  color: var(--color-text-secondary);
}

.diagnostic-grid {
  display: grid;
  gap: 0;
  padding: 4px var(--spacing-md) var(--spacing-md);
}

.diagnostic-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  padding: 10px var(--spacing-sm);
  border-bottom: 2px dashed var(--color-border-light);
}

.diagnostic-row:last-child {
  border-bottom: none;
}

.support-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.metrics-board {
  margin-bottom: var(--spacing-xl);
}

.metrics-board__header {
  grid-template-columns: minmax(0, 1fr) minmax(220px, 0.72fr);
  align-items: end;
}

.metrics-board__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-lg);
  padding: var(--spacing-md) var(--spacing-lg) var(--spacing-lg);
}

.metric-tile {
  display: grid;
  gap: 10px;
  padding: 18px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.metric-tile__label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.metric-tile__value {
  color: var(--color-text-primary);
  font-size: var(--font-size-xxl);
  font-weight: 900;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
  font-family: 'DM Mono', monospace;
}

.tone-positive {
  color: var(--color-positive);
}

.tone-negative {
  color: var(--color-negative);
}

.tone-warning {
  color: var(--color-warning);
}

.tone-neutral {
  color: var(--color-text-secondary);
}

/* ── Details Card ── */
.details-card {
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  margin-bottom: var(--spacing-xl);
  box-shadow: var(--shadow-md);
}

.details-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  cursor: pointer;
  user-select: none;
  background: var(--color-surface-elevated);
  border-bottom: 2px solid transparent;
  transition: background 0.15s;
  list-style: none;
  color: var(--color-text-primary);
  font-weight: 800;
  font-size: var(--font-size-sm);
}

.details-summary::-webkit-details-marker {
  display: none;
}

.details-card[open] .details-summary {
  border-bottom-color: var(--color-border);
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
  border-bottom: 2px dashed var(--color-border-light);
}

.detail-row:nth-child(odd) {
  border-right: 2px dashed var(--color-border-light);
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
  font-weight: 800;
  font-size: var(--font-size-sm);
  font-variant-numeric: tabular-nums;
  font-family: 'DM Mono', monospace;
}

/* ── Responsive ── */
@media (max-width: 900px) {
  .page-header {
    flex-direction: column;
  }

  .metrics-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .report-summary__hero,
  .analysis-grid,
  .support-grid,
  .metrics-board__header,
  .metrics-board__grid {
    grid-template-columns: 1fr;
  }

  .market-stage__secondary {
    grid-template-columns: 1fr;
  }

  .summary-facts {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .summary-conclusion__header {
    flex-direction: column;
  }

  .signal-stats,
  .hover-grid {
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
    border-bottom: 2px dashed var(--color-border-light);
  }

  .detail-row:last-child {
    border-bottom: none;
  }
}

@media (max-width: 640px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .summary-facts {
    grid-template-columns: 1fr;
  }

  .summary-conclusion {
    padding: 16px;
  }

  .signal-stats,
  .hover-grid {
    grid-template-columns: 1fr;
  }

  .guided-success {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>

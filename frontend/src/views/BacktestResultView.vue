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

          <section v-if="report.kline?.length" class="market-stage chart-section chart-section--feature">
            <div class="chart-section__header chart-section__header--feature">
              <div class="chart-section__title-group">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="7" y1="8" x2="7" y2="16"/><line x1="7" y1="16" x2="7.01" y2="16"/><line x1="11" y1="6" x2="11" y2="18"/><line x1="11" y1="6" x2="11.01" y2="6"/><line x1="15" y1="10" x2="15" y2="14"/><line x1="15" y1="14" x2="15.01" y2="14"/></svg>
                <div>
                  <span class="chart-section__title">{{ $t('backtestReport.klineTitle') }}</span>
                  <p class="chart-section__lead">{{ $t('backtestReport.chartDeskSubtitle') }}</p>
                </div>
              </div>
              <span class="chart-section__subtitle">{{ symbolLabel }}</span>
            </div>

            <div class="market-stage__body">
              <div class="market-stage__primary">
                <BacktestKlineChart
                  class="chart-block"
                  :bars="report.kline"
                  :trades="report.trades || []"
                  :symbol="symbolLabel"
                  @hover-change="handleKlineHover"
                />
              </div>

              <aside class="market-stage__rail">
                <section class="signal-panel">
                  <div class="signal-panel__header">
                    <span class="analysis-panel__eyebrow">{{ $t('backtestReport.tradeSignalsTitle') }}</span>
                    <h3 class="signal-panel__title">{{ $t('backtestReport.tradeSignalsTitle') }}</h3>
                    <p class="signal-panel__subtitle">{{ $t('backtestReport.tradeSignalsSubtitle') }}</p>
                  </div>

                  <div class="signal-stats">
                    <article class="signal-stat">
                      <span class="signal-stat__label">{{ $t('backtestReport.totalSignals') }}</span>
                      <strong class="signal-stat__value">{{ totalSignalCount }}</strong>
                    </article>
                    <article class="signal-stat">
                      <span class="signal-stat__label">{{ $t('backtestReport.signalBalance') }}</span>
                      <strong class="signal-stat__value">{{ buySignals }} / {{ sellSignals }}</strong>
                    </article>
                    <article class="signal-stat">
                      <span class="signal-stat__label">{{ $t('backtestReport.signalDensity') }}</span>
                      <strong class="signal-stat__value">{{ signalDensityLabel }}</strong>
                    </article>
                  </div>

                  <div v-if="latestTradeMarker" class="signal-latest">
                    <div class="signal-latest__header">
                      <span class="signal-latest__label">{{ $t('backtestReport.latestSignal') }}</span>
                      <span :class="['signal-latest__side', toneClass(latestTradeMarker.side === 'buy' ? 'positive' : 'negative')]">
                        {{ latestTradeMarker.side === 'buy' ? $t('kline.buySignal') : $t('kline.sellSignal') }}
                      </span>
                    </div>
                    <strong class="signal-latest__value">{{ formatPlain(latestTradeMarker.price, 4) }}</strong>
                    <span class="signal-latest__meta">{{ formatDateTime(latestTradeMarker.timestamp) }}</span>
                  </div>
                </section>

                <section class="signal-panel">
                  <div class="signal-panel__header">
                    <span class="analysis-panel__eyebrow">{{ $t('backtestReport.hoverInspectorTitle') }}</span>
                    <h3 class="signal-panel__title">{{ $t('backtestReport.hoverInspectorTitle') }}</h3>
                    <p class="signal-panel__subtitle">{{ $t('backtestReport.hoverInspectorSubtitle') }}</p>
                  </div>

                  <div v-if="hoveredKlineSnapshot" class="hover-card">
                    <div class="hover-card__headline">
                      <strong>{{ hoveredKlineSnapshot.formattedTime }}</strong>
                      <span :class="['hover-card__change', toneClass(toneFromSignedValue(hoveredKlineSnapshot.priceChange))]">
                        {{ formatPercent(hoveredKlineSnapshot.priceChange, 2, true) }}
                      </span>
                    </div>

                    <div class="hover-grid">
                      <div class="hover-grid__item">
                        <span>{{ $t('backtestReport.openLabel') }}</span>
                        <strong>{{ formatPlain(hoveredKlineSnapshot.open, 4) }}</strong>
                      </div>
                      <div class="hover-grid__item">
                        <span>{{ $t('backtestReport.highLabel') }}</span>
                        <strong>{{ formatPlain(hoveredKlineSnapshot.high, 4) }}</strong>
                      </div>
                      <div class="hover-grid__item">
                        <span>{{ $t('backtestReport.lowLabel') }}</span>
                        <strong>{{ formatPlain(hoveredKlineSnapshot.low, 4) }}</strong>
                      </div>
                      <div class="hover-grid__item">
                        <span>{{ $t('backtestReport.closeLabel') }}</span>
                        <strong>{{ formatPlain(hoveredKlineSnapshot.close, 4) }}</strong>
                      </div>
                      <div class="hover-grid__item">
                        <span>{{ $t('backtestReport.volumeLabel') }}</span>
                        <strong>{{ formatInteger(hoveredKlineSnapshot.volume) }}</strong>
                      </div>
                      <div class="hover-grid__item">
                        <span>{{ $t('backtestReport.totalSignals') }}</span>
                        <strong>{{ hoveredKlineSnapshot.signalCount }}</strong>
                      </div>
                    </div>

                    <div v-if="hoveredKlineSnapshot.signals.length" class="hover-signals">
                      <article v-for="signal in hoveredKlineSnapshot.signals" :key="signal.id" class="hover-signal">
                        <div class="hover-signal__top">
                          <span :class="['hover-signal__side', toneClass(signal.side === 'buy' ? 'positive' : 'negative')]">
                            {{ signal.side === 'buy' ? $t('kline.buySignal') : $t('kline.sellSignal') }}
                          </span>
                          <span class="hover-signal__time">{{ formatDateTime(signal.timestamp) }}</span>
                        </div>
                        <div class="hover-signal__grid">
                          <span>{{ $t('backtestReport.tradePriceLabel') }}</span>
                          <strong>{{ formatPlain(signal.price, 4) }}</strong>
                          <span>{{ $t('backtestReport.tradeQuantityLabel') }}</span>
                          <strong>{{ formatPlain(signal.quantity, 4) }}</strong>
                          <span v-if="typeof signal.pnl === 'number'">{{ $t('backtestReport.tradePnlLabel') }}</span>
                          <strong v-if="typeof signal.pnl === 'number'">{{ formatPlain(signal.pnl, 2) }}</strong>
                        </div>
                      </article>
                    </div>
                    <p v-else class="hover-empty">{{ $t('backtestReport.hoverNoSignals') }}</p>
                  </div>

                  <p v-else class="hover-empty">{{ $t('backtestReport.hoverEmpty') }}</p>
                </section>
              </aside>
            </div>
          </section>

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

          <div class="analysis-grid">
            <section class="analysis-panel">
              <div class="analysis-panel__header">
                <span class="analysis-panel__eyebrow">{{ $t('backtestReport.reportSummary') }}</span>
                <h3 class="analysis-panel__title">{{ $t('backtestReport.reportSummary') }}</h3>
                <p class="analysis-panel__subtitle">{{ $t('backtestReport.reportSummarySubtitle') }}</p>
              </div>
              <article v-for="item in insightItems" :key="item.title" class="insight-row">
                <span :class="['insight-row__dot', toneClass(item.tone)]"></span>
                <div class="insight-row__content">
                  <strong>{{ item.title }}</strong>
                  <p>{{ item.body }}</p>
                </div>
              </article>
            </section>

            <section class="analysis-panel">
              <div class="analysis-panel__header">
                <span class="analysis-panel__eyebrow">{{ $t('backtestReport.diagnosticsTitle') }}</span>
                <h3 class="analysis-panel__title">{{ $t('backtestReport.diagnosticsTitle') }}</h3>
                <p class="analysis-panel__subtitle">{{ $t('backtestReport.diagnosticsSubtitle') }}</p>
              </div>
              <div class="diagnostic-grid">
                <div v-for="item in diagnosticRows" :key="item.label" class="diagnostic-row">
                  <span class="diagnostic-row__label">{{ item.label }}</span>
                  <span :class="['diagnostic-row__value', toneClass(item.tone)]">{{ item.value }}</span>
                </div>
              </div>
            </section>
          </div>

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
import BacktestKlineChart from '../components/backtest/BacktestKlineChart.vue'
import ErrorDisplay from '../components/backtest/ErrorDisplay.vue'
import DisclaimerFooter from '../components/disclaimer/DisclaimerFooter.vue'
import MetricTooltip from '../components/help/MetricTooltip.vue'
import { useUserStore } from '../stores'
import { mapTradesToMarkers, toEpochMs, type TradeMarker } from '../lib/chartIndicators'
import { useBacktestsStore } from '../stores/backtests'

type Tone = 'positive' | 'negative' | 'warning' | 'neutral'

interface HoveredKlineSnapshot {
  time: string | number
  formattedTime: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  priceChange: number
  signalCount: number
  signals: TradeMarker[]
}

const { t } = useI18n()

const route = useRoute()
const router = useRouter()
const store = useBacktestsStore()
const userStore = useUserStore()
const jobId = String(route.params.jobId || '')
const isGuidedMode = route.query.guided === 'true'

const report = computed(() => store.report)
const summary = computed(() => report.value?.result_summary ?? {})

function numberOrNull(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value
  }
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

function toneClass(tone: Tone): string {
  return `tone-${tone}`
}

function toneFromSignedValue(value: number | null, inverse = false): Tone {
  if (value === null || value === 0) {
    return 'neutral'
  }
  if (inverse) {
    return value < 0 ? 'positive' : 'warning'
  }
  return value > 0 ? 'positive' : 'negative'
}

function formatPercent(value: number | undefined | null, digits = 2, showSign = false) {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return '--'
  }
  const prefix = showSign && value > 0 ? '+' : ''
  return `${prefix}${Number(value).toFixed(digits)}%`
}

function formatPlain(value: number | undefined | null, digits = 2) {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return '--'
  }
  return Number(value).toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: digits,
  })
}

function formatInteger(value: number | undefined | null) {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return '--'
  }
  return Math.round(Number(value)).toLocaleString()
}

function formatRangeDate(value: string | number | undefined | null) {
  if (value === undefined || value === null || value === '') {
    return '--'
  }
  const epoch = typeof value === 'number' || typeof value === 'string' ? toEpochMs(value) : null
  const date = new Date(epoch ?? value)
  if (Number.isNaN(date.getTime())) {
    return String(value)
  }
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}

function formatDateTime(value: string | number | undefined | null) {
  if (value === undefined || value === null || value === '') {
    return t('backtestReport.noCompletedAt')
  }
  const epoch = typeof value === 'number' || typeof value === 'string' ? toEpochMs(value) : null
  const date = new Date(epoch ?? value)
  if (Number.isNaN(date.getTime())) {
    return t('backtestReport.noCompletedAt')
  }
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

function formatMetric(value: number | undefined | null, digits = 2, suffix = '') {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return '--'
  }
  return `${Number(value).toFixed(digits)}${suffix}`
}

const points = computed(() => report.value?.equity_curve ?? [])
const trades = computed(() => report.value?.trades ?? [])
const klineBars = computed(() => report.value?.kline ?? [])
const tradeMarkers = computed(() => mapTradesToMarkers(klineBars.value, trades.value))
const reportParams = computed<Record<string, unknown>>(() => report.value?.params ?? {})
const firstPoint = computed(() => points.value[0] ?? null)
const lastPoint = computed(() => points.value[points.value.length - 1] ?? null)
const hoveredKlineSnapshot = ref<HoveredKlineSnapshot | null>(null)

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
const totalSignalCount = computed(() => tradeMarkers.value.length)
const latestTradeMarker = computed(() => tradeMarkers.value[tradeMarkers.value.length - 1] ?? null)
const signalDensityLabel = computed(() => {
  if (!klineBars.value.length) {
    return '--'
  }
  return `${formatPlain((tradeMarkers.value.length / klineBars.value.length) * 100, 1)} / 100`
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
    label: t('backtestReport.metrics.annualizedReturn'),
    metricKey: 'annualized_return',
    value: formatMetric(summary.value.annualizedReturn, 2),
    suffix: '%',
    variant: 'info' as const,
    showSign: true,
    showDisclaimer: true
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
    label: t('backtestReport.metrics.totalReturn'),
    metricKey: 'total_return',
    value: formatMetric(strategyReturn.value, 2, '%'),
    tone: toneFromSignedValue(strategyReturn.value),
    caption: `${t('backtestReport.benchmarkReturn')} ${formatPercent(benchmarkReturn.value, 2, true)}`,
  },
  {
    label: t('backtestReport.metrics.annualizedReturn'),
    metricKey: 'annualized_return',
    value: formatMetric(numberOrNull(summary.value.annualizedReturn), 2, '%'),
    tone: toneFromSignedValue(numberOrNull(summary.value.annualizedReturn)),
    caption: `${t('backtestReport.runningDays')} ${durationDays.value ?? '--'}`,
  },
  {
    label: t('backtestReport.metrics.maxDrawdown'),
    metricKey: 'max_drawdown',
    value: formatMetric(numberOrNull(summary.value.maxDrawdown), 2, '%'),
    tone: toneFromSignedValue(numberOrNull(summary.value.maxDrawdown), true),
    caption: `${t('backtestReport.currentDrawdown')} ${formatPercent(currentDrawdown.value, 2, true)}`,
  },
  {
    label: t('backtestReport.metrics.sharpeRatio'),
    metricKey: 'sharpe_ratio',
    value: formatMetric(numberOrNull(summary.value.sharpeRatio), 2),
    tone: toneFromSignedValue(numberOrNull(summary.value.sharpeRatio)),
    caption: `${t('backtestReport.metrics.volatility')} ${formatPercent(numberOrNull(summary.value.volatility))}`,
  },
  {
    label: t('backtestReport.metrics.volatility'),
    metricKey: 'volatility',
    value: formatMetric(numberOrNull(summary.value.volatility), 2, '%'),
    tone: toneFromSignedValue(numberOrNull(summary.value.volatility), true),
    caption: `${t('backtestReport.qualityScore')} ${qualityScore.value}${t('backtestReport.scoreOutOf')}`,
  },
  {
    label: t('backtestReport.metrics.sortinoRatio'),
    metricKey: 'sortino_ratio',
    value: formatMetric(numberOrNull(summary.value.sortinoRatio), 2),
    tone: toneFromSignedValue(numberOrNull(summary.value.sortinoRatio)),
    caption: `${t('backtestReport.metrics.maxDrawdown')} ${formatPercent(numberOrNull(summary.value.maxDrawdown), 2, true)}`,
  },
  {
    label: t('backtestReport.metrics.calmarRatio'),
    metricKey: 'calmar_ratio',
    value: formatMetric(numberOrNull(summary.value.calmarRatio), 2),
    tone: toneFromSignedValue(numberOrNull(summary.value.calmarRatio)),
    caption: `${t('backtestReport.returnSpread')} ${formatPercent(excessReturn.value, 2, true)}`,
  },
  {
    label: t('backtestReport.metrics.winRate'),
    metricKey: 'win_rate',
    value: formatMetric(numberOrNull(summary.value.winRate), 2, '%'),
    tone: toneFromSignedValue((numberOrNull(summary.value.winRate) ?? 50) - 50),
    caption: `${t('backtestReport.metrics.totalTrades')} ${formatInteger(numberOrNull(summary.value.totalTrades) ?? trades.value.length)}`,
  },
  {
    label: t('backtestReport.metrics.profitLossRatio'),
    metricKey: 'profit_loss_ratio',
    value: formatMetric(numberOrNull(summary.value.profitLossRatio ?? summary.value.profitFactor), 2),
    tone: toneFromSignedValue((numberOrNull(summary.value.profitLossRatio ?? summary.value.profitFactor) ?? 1) - 1),
    caption: `${t('backtestReport.metrics.winRate')} ${formatPercent(numberOrNull(summary.value.winRate))}`,
  },
  {
    label: t('backtestReport.metrics.maxConsecutiveLosses'),
    metricKey: 'max_consecutive_losses',
    value: formatMetric(numberOrNull(summary.value.maxConsecutiveLosses), 0),
    tone: toneFromSignedValue(numberOrNull(summary.value.maxConsecutiveLosses), true),
    caption: `${t('backtestReport.buySignals')} ${buySignals.value} · ${t('backtestReport.sellSignals')} ${sellSignals.value}`,
  },
  {
    label: t('backtestReport.metrics.totalTrades'),
    metricKey: 'total_trades',
    value: formatMetric(numberOrNull(summary.value.totalTrades) ?? trades.value.length, 0),
    tone: 'neutral' as Tone,
    caption: `${t('backtestReport.holdingPeriod')} ${formatPlain(numberOrNull(summary.value.avgHoldingDays), 1)}`,
  }
])

const statusLabel = computed(() => {
  if (report.value?.status === 'failed' || report.value?.status === 'timeout') {
    return t('status.error')
  }
  if (report.value?.status === 'completed') {
    return t('status.completed')
  }
  if (report.value?.status === 'running') {
    return t('status.running')
  }
  return t('status.pending')
})

const statusTone = computed<Tone>(() => {
  if (report.value?.status === 'completed') {
    return 'positive'
  }
  if (report.value?.status === 'failed' || report.value?.status === 'timeout') {
    return 'negative'
  }
  return 'warning'
})

async function finishGuidedOnboarding() {
  await userStore.markOnboardingCompleted(true)
  userStore.finishGuidedBacktest()
  await router.push({ name: 'dashboard' })
}

function handleKlineHover(payload: HoveredKlineSnapshot | null) {
  hoveredKlineSnapshot.value = payload
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

.report-summary {
  display: grid;
  gap: var(--spacing-md);
  padding: clamp(18px, 3vw, 28px);
  border: 1px solid var(--color-border);
  border-radius: 24px;
  background:
    radial-gradient(circle at top left, rgba(124, 109, 216, 0.18), transparent 28%),
    radial-gradient(circle at top right, rgba(54, 214, 182, 0.14), transparent 32%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.01));
  box-shadow: var(--shadow-md);
}

.report-summary__hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 220px;
  gap: var(--spacing-lg);
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
  border: 1px solid var(--color-border);
  background: rgba(255, 255, 255, 0.04);
  font-size: var(--font-size-xs);
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
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(8, 9, 23, 0.34);
  backdrop-filter: blur(12px);
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
  gap: var(--spacing-md);
}

.summary-fact {
  display: grid;
  gap: 6px;
  padding: 16px 18px;
  border: 1px solid var(--color-border);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.02);
}

.summary-fact__label,
.analysis-panel__eyebrow,
.metric-tile__label,
.diagnostic-row__label {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.summary-fact__value {
  color: var(--color-text-primary);
  font-size: var(--font-size-xl);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.diagnostic-row__value {
  color: var(--color-text-primary);
  font-size: var(--font-size-lg);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.summary-fact__note,
.metric-tile__caption {
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

.chart-section__header--feature {
  align-items: flex-start;
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

.chart-section__lead {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.chart-block {
  padding: var(--spacing-sm);
}

.market-stage__body {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(280px, 0.9fr);
  gap: var(--spacing-lg);
  padding: var(--spacing-sm) var(--spacing-md) var(--spacing-md);
}

.market-stage__primary {
  min-width: 0;
}

.market-stage__rail {
  display: grid;
  gap: var(--spacing-md);
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
  margin-bottom: var(--spacing-lg);
}

.analysis-panel,
.metrics-board {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  background: var(--color-surface);
  overflow: hidden;
}

.analysis-panel__header,
.metrics-board__header {
  display: grid;
  gap: 6px;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-border-light);
  background: var(--color-surface-elevated);
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
  border-radius: 999px;
  background: currentColor;
}

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
  padding: 12px var(--spacing-sm);
  border-bottom: 1px solid var(--color-border-light);
}

.diagnostic-row:last-child {
  border-bottom: none;
}

.metrics-board {
  margin-bottom: var(--spacing-lg);
}

.metrics-board__header {
  grid-template-columns: minmax(0, 1fr) minmax(220px, 0.72fr);
  align-items: end;
}

.metrics-board__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg) var(--spacing-lg);
}

.metric-tile {
  display: grid;
  gap: 10px;
  padding: 18px;
  border: 1px solid var(--color-border);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.02);
}

.metric-tile__label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.metric-tile__value {
  color: var(--color-text-primary);
  font-size: var(--font-size-xxl);
  font-weight: 800;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
}

.tone-positive {
  color: var(--color-success);
}

.tone-negative {
  color: var(--color-danger);
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

  .report-summary__hero,
  .analysis-grid,
  .market-stage__body,
  .metrics-board__header,
  .metrics-board__grid {
    grid-template-columns: 1fr;
  }

  .summary-facts {
    grid-template-columns: repeat(2, minmax(0, 1fr));
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

  .summary-facts {
    grid-template-columns: 1fr;
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

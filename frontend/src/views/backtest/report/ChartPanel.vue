<template>
  <section class="chart-panel" data-test="chart-panel">
    <div v-if="hasKlineData" class="chart-section" @click="handleChartFocus">
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
          :symbol="report.symbol || ''"
          :timeframe="report.interval || '1d'"
        />
        <TradeSignalList :signals="tradeMarkers" :holding-durations="tradeHoldingDurations" :cumulative-returns="cumulativeReturns" />
      </div>
    </div>

    <div class="chart-section" @click="handleChartFocus">
      <div class="chart-section__header">
        <div class="chart-section__title-group">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
          <span class="chart-section__title">{{ $t('backtestReport.equityCurveTitle') }}</span>
        </div>
        <span class="chart-section__subtitle">{{ $t('backtestReport.equityCurveSubtitle') }}</span>
      </div>
      <EquityCurveChart class="chart-block" :points="report.equity_curve || []" :trades="report.trades || []" />
    </div>

    <div v-if="hasDrawdownData" class="chart-section" @click="handleChartFocus">
      <div class="chart-section__header">
        <div class="chart-section__title-group">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg>
          <span class="chart-section__title">{{ $t('backtestReport.drawdownTitle') }}</span>
        </div>
        <span class="chart-section__subtitle">{{ $t('backtestReport.drawdownSubtitle') }}</span>
      </div>
      <DrawdownChart :points="report.equity_curve || []" />
    </div>

    <div v-if="aiChartNarration" class="chart-ai-narration">
      <p>{{ aiChartNarration }}</p>
    </div>

    <section v-if="hasComparisonData" class="chart-comparison">
      <div class="chart-section__header">
        <span class="chart-section__title">{{ $t('backtestReport.comparisonTitle') }}</span>
      </div>
      <div class="chart-comparison__body">
        <div v-if="parameterSensitivity && parameterSensitivity.length" class="comparison-block">
          <h4>Parameter Sensitivity</h4>
          <pre>{{ JSON.stringify(parameterSensitivity, null, 2) }}</pre>
        </div>
        <div v-if="regimeAnalysis && regimeAnalysis.length" class="comparison-block">
          <h4>Regime Analysis</h4>
          <pre>{{ JSON.stringify(regimeAnalysis, null, 2) }}</pre>
        </div>
        <div v-if="monteCarlo && Object.keys(monteCarlo).length" class="comparison-block">
          <h4>Monte Carlo</h4>
          <pre>{{ JSON.stringify(monteCarlo, null, 2) }}</pre>
        </div>
      </div>
    </section>

    <TradeTable :trades="report.trades || []" />
    <TradeDetailTable :trades="report.trades || []" />
    <TradeDistributionCharts :distribution="tradeDistribution" />
  </section>
</template>

<script setup lang="ts">
import { computed, inject } from 'vue'
import KlinePlaceholder from '../../../components/KlinePlaceholder.vue'
import DrawdownChart from '../../../components/backtest/DrawdownChart.vue'
import EquityCurveChart from '../../../components/backtest/EquityCurveChart.vue'
import TradeDetailTable from '../../../components/backtest/TradeDetailTable.vue'
import TradeDistributionCharts from '../../../components/backtest/TradeDistributionCharts.vue'
import TradeSignalList from '../../../components/backtest/TradeSignalList.vue'
import TradeTable from '../../../components/backtest/TradeTable.vue'
import type { BacktestReportResponse } from '../../../types/Backtest'
import type { TradeMarker } from '../../../lib/chartIndicators'
import type { TradeDistribution } from '../../../lib/backtestComputed'

const props = defineProps<{
  report: BacktestReportResponse
  hasKlineData: boolean
  hasDrawdownData: boolean
  tradeMarkers: TradeMarker[]
  tradeHoldingDurations: Map<number, number>
  cumulativeReturns: number[]
  tradeDistribution: TradeDistribution
  aiChartNarration?: string
  parameterSensitivity?: Array<Record<string, unknown>>
  regimeAnalysis?: Array<Record<string, unknown>>
  monteCarlo?: Record<string, unknown> | null
}>()

const hasComparisonData = computed(() =>
  (props.parameterSensitivity && props.parameterSensitivity.length > 0)
  || (props.regimeAnalysis && props.regimeAnalysis.length > 0)
  || (props.monteCarlo && Object.keys(props.monteCarlo).length > 0)
)

const aiContext = inject<{
  activeSection: string
}>('aiContext', { activeSection: 'charts' })

function handleChartFocus() {
  if (aiContext) {
    aiContext.activeSection = 'charts'
  }
}
</script>

<style scoped>
.chart-panel {
  display: grid;
  gap: var(--spacing-xl);
}

.chart-section {
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
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

.chart-block {
  padding: var(--spacing-sm);
}

.chart-block--stacked {
  display: grid;
  gap: var(--spacing-md);
}

.chart-ai-narration {
  padding: 12px 16px;
  background: var(--color-surface-elevated);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-sm);
}

.chart-ai-narration p {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.6;
}

.chart-comparison {
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-md);
}

.chart-comparison__body {
  padding: var(--spacing-md);
  display: grid;
  gap: var(--spacing-md);
}

.comparison-block h4 {
  margin: 0 0 var(--spacing-sm);
  font-size: var(--font-size-sm);
}

.comparison-block pre {
  margin: 0;
  padding: var(--spacing-sm);
  background: var(--color-surface-elevated);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  overflow-x: auto;
}
</style>

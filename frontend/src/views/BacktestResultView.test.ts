import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import zh from '../i18n/messages/zh'
import BacktestResultView from './BacktestResultView.vue'

const {
  loadReportMock,
  loadSupportedPackagesMock,
  downloadBacktestReportAsHtmlMock,
  printBacktestReportAsPdfMock,
} = vi.hoisted(() => ({
  loadReportMock: vi.fn(),
  loadSupportedPackagesMock: vi.fn(),
  downloadBacktestReportAsHtmlMock: vi.fn(),
  printBacktestReportAsPdfMock: vi.fn(),
}))

const baseLegacyReport = {
  job_id: 'job-1',
  status: 'completed',
  result_summary: {
    totalReturn: 12.5,
    maxDrawdown: -3.2,
    sharpeRatio: 1.8,
    annualizedReturn: 10.4,
    volatility: 6.8,
    sortinoRatio: 2.1,
    calmarRatio: 3.2,
    winRate: 50,
    profitLossRatio: 1.6,
    maxConsecutiveLosses: 1,
    totalTrades: 2,
  },
  equity_curve: [
    { timestamp: 1700000000000, equity: 100000, benchmark_equity: 100000, drawdown: 0 },
  ],
  kline: [
    { time: 1700000000000, open: 100, high: 110, low: 95, close: 108, volume: 1000 },
    { time: 1700003600000, open: 108, high: 112, low: 104, close: 106, volume: 1200 },
  ],
  trades: [
    { symbol: 'BTCUSDT', side: 'buy', price: 100, quantity: 1, timestamp: 1700000000000 },
  ],
  disclaimer: 'For research only. Not investment advice.',
}

const storeState = {
  report: baseLegacyReport,
  legacyReport: baseLegacyReport,
  aiReport: null as null | {
    id: string
    job_id: string
    status: string
    payload: Record<string, unknown>
  },
  reportLoading: false,
  reportError: null as string | null,
  supportedPackages: [],
  supportedPackagesLoading: false,
}

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
  useRoute: () => ({
    params: {
      jobId: 'job-1',
    },
    query: {},
  }),
}))

vi.mock('../stores', () => ({
  useUserStore: () => ({
    onboardingHighlightTarget: null,
    markOnboardingCompleted: vi.fn(),
    finishGuidedBacktest: vi.fn(),
  }),
}))

vi.mock('../stores/backtests', () => ({
  useBacktestsStore: () => ({
    ...storeState,
    loadReport: loadReportMock,
    loadSupportedPackages: loadSupportedPackagesMock,
  }),
}))

vi.mock('../lib/backtestReportExport', () => ({
  downloadBacktestReportAsHtml: downloadBacktestReportAsHtmlMock,
  printBacktestReportAsPdf: printBacktestReportAsPdfMock,
}))

vi.mock('./backtest/report/ReportHeader.vue', () => ({
  default: {
    props: ['jobId', 'canExport'],
    emits: ['export-html', 'export-pdf'],
    template: `
      <div data-test="report-header">
        <span>{{ jobId }}</span>
        <button v-if="canExport" data-test="export-html" @click="$emit('export-html')" />
        <button v-if="canExport" data-test="export-pdf" @click="$emit('export-pdf')" />
      </div>
    `,
  },
}))

vi.mock('./backtest/report/MetricsPanel.vue', () => ({
  default: {
    props: ['coreMetrics'],
    template: `
      <div data-test="metrics-panel">
        <div
          v-for="metric in coreMetrics"
          :key="metric.label"
          data-test="metric-value"
        >
          {{ metric.label }} {{ metric.value }}{{ metric.suffix || '' }}
        </div>
      </div>
    `,
  },
}))

vi.mock('./backtest/report/ChartPanel.vue', () => ({
  default: {
    template: '<div data-test="chart-panel" />',
  },
}))

vi.mock('./backtest/report/AISummaryPanel.vue', () => ({
  default: {
    props: ['summary'],
    template: '<div data-test="ai-summary-panel">{{ summary }}</div>',
  },
}))

vi.mock('./backtest/report/DiagnosisPanel.vue', () => ({
  default: {
    props: ['diagnosis'],
    template: '<div data-test="diagnosis-panel">{{ diagnosis }}</div>',
  },
}))

vi.mock('./backtest/report/ComparisonPanel.vue', () => ({
  default: {
    template: '<div data-test="comparison-panel" />',
  },
}))

vi.mock('./backtest/report/AlertsPanel.vue', () => ({
  default: {
    template: '<div data-test="alerts-panel" />',
  },
}))

vi.mock('../components/disclaimer/DisclaimerFooter.vue', () => ({
  default: {
    template: '<div data-test="disclaimer-footer">基于历史数据，不构成投资建议</div>',
  },
}))

vi.mock('../components/help/MetricTooltip.vue', () => ({
  default: {
    template: '<span data-test="metric-tooltip" />',
  },
}))

vi.mock('../components/StatCard.vue', () => ({
  default: {
    props: ['label', 'value', 'suffix'],
    template: `
      <div data-test="stat-card">
        {{ label }} {{ value }}{{ suffix || '' }}
      </div>
    `,
  },
}))

vi.mock('../components/backtest/ErrorDisplay.vue', () => ({
  default: {
    props: ['error'],
    template: '<div>{{ error?.message }}</div>',
  },
}))

vi.mock('../components/backtest/StrategyParamsPanel.vue', () => ({
  default: {
    template: '<div data-test="strategy-params-panel" />',
  },
}))

vi.mock('../components/backtest/SignalStatsPanel.vue', () => ({
  default: {
    template: '<div data-test="signal-stats-panel" />',
  },
}))

vi.mock('../components/backtest/BenchmarkComparison.vue', () => ({
  default: {
    template: '<div data-test="benchmark-comparison-panel" />',
  },
}))

vi.mock('../components/backtest/RiskMetricsPanel.vue', () => ({
  default: {
    template: '<div data-test="risk-metrics-panel" />',
  },
}))

vi.mock('../components/backtest/EquityCurveChart.vue', () => ({
  default: {
    template: '<div data-test="equity-curve-chart" />',
  },
}))

vi.mock('../components/backtest/DrawdownChart.vue', () => ({
  default: {
    template: '<div data-test="drawdown-chart" />',
  },
}))

vi.mock('../components/KlinePlaceholder.vue', () => ({
  default: {
    template: '<div data-test="kline-placeholder" />',
  },
}))

vi.mock('../components/backtest/TradeSignalList.vue', () => ({
  default: {
    template: '<div data-test="trade-signal-list" />',
  },
}))

vi.mock('../components/backtest/TradeTable.vue', () => ({
  default: {
    template: '<div data-test="trade-table" />',
  },
}))

vi.mock('../components/backtest/TradeDetailTable.vue', () => ({
  default: {
    template: '<div data-test="trade-detail-table" />',
  },
}))

vi.mock('../components/backtest/TradeDistributionCharts.vue', () => ({
  default: {
    template: '<div data-test="trade-distribution-charts" />',
  },
}))

function mountView() {
  const i18n = createI18n({
    legacy: false,
    locale: 'zh',
    globalInjection: true,
    messages: { zh },
  })

  return mount(BacktestResultView, {
    global: {
      plugins: [i18n],
    },
  })
}

describe('BacktestResultView', () => {
  beforeEach(() => {
    loadReportMock.mockClear()
    loadSupportedPackagesMock.mockClear()
    downloadBacktestReportAsHtmlMock.mockClear()
    printBacktestReportAsPdfMock.mockClear()

    storeState.report = { ...baseLegacyReport }
    storeState.legacyReport = storeState.report
    storeState.aiReport = null
    storeState.reportLoading = false
    storeState.reportError = null
    storeState.supportedPackages = []
    storeState.supportedPackagesLoading = false
  })

  it('renders legacy metrics and charts when no ai report exists', () => {
    const wrapper = mountView()

    expect(loadReportMock).toHaveBeenCalledWith('job-1')
    expect(wrapper.find('[data-test="report-header"]').exists()).toBe(true)
    expect(wrapper.get('[data-test="metrics-panel"]').text()).toContain('12.50%')
    expect(wrapper.find('[data-test="chart-panel"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="ai-summary-panel"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="diagnosis-panel"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="comparison-panel"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="alerts-panel"]').exists()).toBe(false)
  })

  it('renders ai summary when executive summary exists', () => {
    storeState.aiReport = {
      id: 'report-1',
      job_id: 'job-1',
      status: 'ready',
      payload: {
        executive_summary: 'AI summary for this backtest.',
      },
    }

    const wrapper = mountView()

    expect(wrapper.get('[data-test="ai-summary-panel"]').text()).toContain('AI summary for this backtest.')
  })

  it('renders diagnosis comparison and alerts panels only when ai payload provides them', () => {
    storeState.aiReport = {
      id: 'report-1',
      job_id: 'job-1',
      status: 'ready',
      payload: {
        diagnosis_narration: 'Risk concentration is elevated.',
        parameter_sensitivity: [{ parameter: 'lookback', winner: '20' }],
        monte_carlo: { median: 0.12 },
        regime_analysis: [{ regime: 'trend', return: 0.18 }],
        anomalies: [{ title: 'Large drawdown cluster' }],
      },
    }

    const wrapper = mountView()

    expect(wrapper.get('[data-test="diagnosis-panel"]').text()).toContain('Risk concentration is elevated.')
    expect(wrapper.find('[data-test="comparison-panel"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="alerts-panel"]').exists()).toBe(true)
  })
})

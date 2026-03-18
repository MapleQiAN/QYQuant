import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import BacktestResultView from './BacktestResultView.vue'

const loadReportMock = vi.fn()
const loadSupportedPackagesMock = vi.fn()
const storeState = {
  report: {
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
      totalTrades: 2
    },
    equity_curve: [
      { timestamp: 1700000000000, equity: 100000, benchmark_equity: 100000 }
    ],
    trades: [
      { symbol: 'BTCUSDT', side: 'buy', price: 100, quantity: 1, timestamp: 1700000000000 }
    ],
    disclaimer: 'For research only. Not investment advice.'
  },
  reportLoading: false,
  reportError: null,
  supportedPackages: [],
  supportedPackagesLoading: false
}

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
  useRoute: () => ({
    params: {
      jobId: 'job-1'
    },
    query: {},
  })
}))

vi.mock('../stores', () => ({
  useUserStore: () => ({
    onboardingHighlightTarget: null,
    markOnboardingCompleted: vi.fn(),
    finishGuidedBacktest: vi.fn(),
  }),
}))

vi.mock('../components/help/MetricTooltip.vue', () => ({
  default: {
    template: '<span data-test="metric-tooltip" />',
  },
}))

vi.mock('../components/StatCard.vue', () => ({
  default: {
    props: ['label', 'value', 'suffix', 'showDisclaimer'],
    template: `
      <div
        class="stat-card-stub"
        :data-label="label"
        :data-show-disclaimer="showDisclaimer ? 'true' : 'false'"
        data-test="stat-card"
      >
        {{ label }} {{ value }}{{ suffix || '' }}
      </div>
    `,
  },
}))

vi.mock('../components/disclaimer/DisclaimerFooter.vue', () => ({
  default: {
    template: '<div data-test="disclaimer-footer">基于历史数据，不构成投资建议</div>',
  },
}))

vi.mock('../components/backtest/ErrorDisplay.vue', () => ({
  default: {
    props: ['error', 'supportedPackages'],
    template: '<div>{{ error?.type }} {{ error?.line }} {{ error?.message }} {{ error?.example_code }} {{ supportedPackages?.[0]?.name }}</div>',
  },
}))

vi.mock('../components/backtest/EquityCurveChart.vue', () => ({
  default: {
    template: '<div data-test="equity-chart" />',
  },
}))

vi.mock('../stores/backtests', () => ({
  useBacktestsStore: () => ({
    ...storeState,
    loadReport: loadReportMock,
    loadSupportedPackages: loadSupportedPackagesMock
  })
}))

describe('BacktestResultView', () => {
  beforeEach(() => {
    loadReportMock.mockClear()
    loadSupportedPackagesMock.mockClear()
    storeState.report = {
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
        totalTrades: 2
      },
      equity_curve: [
        { timestamp: 1700000000000, equity: 100000, benchmark_equity: 100000 }
      ],
      trades: [
        { symbol: 'BTCUSDT', side: 'buy', price: 100, quantity: 1, timestamp: 1700000000000 }
      ],
      disclaimer: 'For research only. Not investment advice.'
    }
    storeState.reportLoading = false
    storeState.reportError = null
    storeState.supportedPackages = []
    storeState.supportedPackagesLoading = false
  })

  it('renders core metrics with earnings disclaimers and footer disclaimer', async () => {
    const wrapper = mount(BacktestResultView)
    const statCards = wrapper.findAll('[data-test="stat-card"]')
    const disclaimerCards = statCards.filter((item) => item.attributes('data-show-disclaimer') === 'true')

    expect(loadReportMock).toHaveBeenCalledWith('job-1')
    expect(wrapper.text()).toContain('12.50%')
    expect(wrapper.text()).toContain('-3.20%')
    expect(wrapper.text()).toContain('1.80')
    expect(statCards).toHaveLength(4)
    expect(disclaimerCards).toHaveLength(2)
    expect(wrapper.get('[data-test="disclaimer-footer"]').text()).toContain('基于历史数据，不构成投资建议')
  })

  it('renders structured error details for failed report', async () => {
    storeState.report = {
      job_id: 'job-1',
      status: 'failed',
      error: {
        type: 'NameError',
        line: 15,
        message: "未定义的变量 'sma_period'",
        suggestion: '请检查变量名是否正确',
        example_code: "sma_period = ctx.params.get('sma_period', 20)"
      }
    }
    storeState.supportedPackages = [
      { name: 'pandas', version: '2.x', description: 'Data analysis' }
    ]

    const wrapper = mount(BacktestResultView)

    expect(wrapper.text()).toContain("未定义的变量 'sma_period'")
    expect(wrapper.text()).toContain('NameError')
    expect(wrapper.text()).toContain('15')
    expect(wrapper.text()).toContain("sma_period = ctx.params.get('sma_period', 20)")
    expect(wrapper.text()).toContain('pandas')
    expect(loadSupportedPackagesMock).toHaveBeenCalled()
  })
})

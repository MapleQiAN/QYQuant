import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import BacktestResultView from './BacktestResultView.vue'

const loadReportMock = vi.fn()

vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: {
      jobId: 'job-1'
    }
  })
}))

vi.mock('../stores/backtests', () => ({
  useBacktestsStore: () => ({
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
    loadReport: loadReportMock
  })
}))

describe('BacktestResultView', () => {
  it('renders core metrics and disclaimer', async () => {
    const wrapper = mount(BacktestResultView, {
      global: {
        stubs: {
          EquityCurveChart: {
            template: '<div data-test="equity-chart" />'
          }
        }
      }
    })

    expect(loadReportMock).toHaveBeenCalledWith('job-1')
    expect(wrapper.text()).toContain('12.50%')
    expect(wrapper.text()).toContain('-3.20%')
    expect(wrapper.text()).toContain('1.80')
    expect(wrapper.text()).toContain('For research only. Not investment advice.')
  })
})

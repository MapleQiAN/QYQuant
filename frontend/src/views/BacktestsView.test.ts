import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import BacktestsView from './BacktestsView.vue'

const {
  pushMock,
  fetchRecentMock,
  fetchRuntimeDescriptorMock,
  fetchMyQuotaMock,
  fetchBacktestHistoryMock,
  fetchBacktestStatusMock,
  submitBacktestMock,
} = vi.hoisted(() => ({
  pushMock: vi.fn(),
  fetchRecentMock: vi.fn(),
  fetchRuntimeDescriptorMock: vi.fn(),
  fetchMyQuotaMock: vi.fn(),
  fetchBacktestHistoryMock: vi.fn(),
  fetchBacktestStatusMock: vi.fn(),
  submitBacktestMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}))

vi.mock('../api/strategies', () => ({
  fetchRecent: fetchRecentMock,
  fetchRuntimeDescriptor: fetchRuntimeDescriptorMock,
}))

vi.mock('../api/users', () => ({
  fetchMyQuota: fetchMyQuotaMock,
}))

vi.mock('../api/backtests', async () => {
  const actual = await vi.importActual<typeof import('../api/backtests')>('../api/backtests')
  return {
    ...actual,
    fetchBacktestHistory: fetchBacktestHistoryMock,
    fetchBacktestStatus: fetchBacktestStatusMock,
    submitBacktest: submitBacktestMock,
  }
})

describe('BacktestsView', () => {
  beforeEach(() => {
    pushMock.mockReset()
    fetchRecentMock.mockReset()
    fetchRuntimeDescriptorMock.mockReset()
    fetchMyQuotaMock.mockReset()
    fetchBacktestHistoryMock.mockReset()
    fetchBacktestStatusMock.mockReset()
    submitBacktestMock.mockReset()

    fetchRecentMock.mockResolvedValue([
      { id: 'strategy-1', name: 'Alpha', symbol: 'BTCUSDT' },
    ])
    fetchRuntimeDescriptorMock.mockResolvedValue({
      strategyVersion: 'v1',
      parameters: [],
    })
    fetchMyQuotaMock.mockResolvedValue({
      plan_level: 'free',
      used_count: 3,
      plan_limit: 10,
      remaining: 7,
      reset_at: '2026-04-01T00:00:00+08:00',
    })
    fetchBacktestHistoryMock.mockResolvedValue({
      items: [
        {
          job_id: 'job-history-1',
          name: 'Alpha Breakout April',
          status: 'completed',
          symbol: 'BTCUSDT',
          strategy_name: 'Alpha',
          created_at: '2026-04-08T10:00:00+08:00',
          completed_at: '2026-04-08T10:05:00+08:00',
          has_report: true,
        },
        {
          job_id: 'job-history-2',
          name: 'ETH Mean Reversion Retry',
          status: 'failed',
          symbol: 'ETHUSDT',
          strategy_name: 'Mean Reversion',
          created_at: '2026-04-07T09:00:00+08:00',
          completed_at: '2026-04-07T09:02:00+08:00',
          has_report: true,
        },
      ],
    })
    fetchBacktestStatusMock.mockResolvedValue({ status: 'completed' })
    submitBacktestMock.mockResolvedValue({ job_id: 'job-1' })
  })

  it('shows quota information after mount', async () => {
    const wrapper = mount(BacktestsView, {
      global: {
        mocks: {
          $t: (key: string) => key,
        },
      },
    })

    await flushPromises()

    expect(fetchMyQuotaMock).toHaveBeenCalled()
    expect(wrapper.text()).toContain('backtests.remainingQuota')
    expect(wrapper.text()).toContain('7')
    expect(wrapper.text()).toContain('10')
    expect(wrapper.text()).toContain('2026-04-01')
  })

  it('disables running backtests when quota is exhausted', async () => {
    fetchMyQuotaMock.mockResolvedValueOnce({
      plan_level: 'free',
      used_count: 10,
      plan_limit: 10,
      remaining: 0,
      reset_at: '2026-04-01T00:00:00+08:00',
    })

    const wrapper = mount(BacktestsView, {
      global: {
        mocks: {
          $t: (key: string) => key,
        },
      },
    })

    await flushPromises()

    const actionButton = wrapper.get('.actions button')

    expect(actionButton.text()).toBe('backtests.upgradeForMore')
    expect(actionButton.classes()).toContain('btn-upgrade')
    expect(actionButton.attributes('disabled')).toBeUndefined()

    await actionButton.trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/pricing')
  })

  it('shows detailed failure reason when polled backtest job fails', async () => {
    fetchBacktestStatusMock.mockResolvedValueOnce({
      status: 'failed',
      error: {
        type: 'NameError',
        line: 15,
        message: "Undefined variable 'sma_period'",
      },
    })

    const wrapper = mount(BacktestsView, {
      global: {
        mocks: {
          $t: (key: string) => key,
        },
      },
    })

    await flushPromises()
    await wrapper.get('.btn-run').trigger('click')
    await flushPromises()

    expect(submitBacktestMock).toHaveBeenCalled()
    expect(wrapper.text()).toContain("Backtest failed: Undefined variable 'sma_period' (line 15)")
  })

  it('submits custom backtest names and opens the finished report', async () => {
    const wrapper = mount(BacktestsView, {
      global: {
        mocks: {
          $t: (key: string) => key,
        },
      },
    })

    await flushPromises()
    await wrapper.get('input[data-test="backtest-name-input"]').setValue('Momentum Sprint')
    await wrapper.get('[data-test="data-source-select"]').setValue('binance')
    await wrapper.get('.btn-run').trigger('click')
    await flushPromises()

    expect(submitBacktestMock).toHaveBeenCalledWith({
      strategy_id: 'strategy-1',
      symbols: ['BTCUSDT'],
      start_date: expect.any(String),
      end_date: expect.any(String),
      data_source: 'binance',
      name: 'Momentum Sprint',
    })
    expect(pushMock).toHaveBeenCalledWith({ name: 'backtest-report', params: { jobId: 'job-1' } })
  })

  it('auto-resolves A-share symbols to akshare on run page', async () => {
    fetchRecentMock.mockResolvedValueOnce([
      { id: 'strategy-1', name: 'Alpha', symbol: '002028.XSHE' },
    ])

    const wrapper = mount(BacktestsView, {
      global: {
        mocks: {
          $t: (key: string) => key,
        },
      },
    })

    await flushPromises()
    await wrapper.get('.btn-run').trigger('click')
    await flushPromises()

    expect(submitBacktestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        data_source: 'akshare',
      })
    )
  })

  it('blocks incompatible data source selection for A-share symbols', async () => {
    fetchRecentMock.mockResolvedValueOnce([
      { id: 'strategy-1', name: 'Alpha', symbol: '002028.XSHE' },
    ])

    const wrapper = mount(BacktestsView, {
      global: {
        mocks: {
          $t: (key: string) => key,
        },
      },
    })

    await flushPromises()
    await wrapper.get('[data-test="data-source-select"]').setValue('binance')
    await wrapper.get('.btn-run').trigger('click')
    await flushPromises()

    expect(submitBacktestMock).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('backtests.errorIncompatibleDataSource')
  })

  it('shows backtest history, filters by name, and opens reports from history', async () => {
    const wrapper = mount(BacktestsView, {
      global: {
        mocks: {
          $t: (key: string) => key,
        },
      },
    })

    await flushPromises()

    expect(fetchBacktestHistoryMock).toHaveBeenCalled()
    expect(wrapper.text()).toContain('Alpha Breakout April')
    expect(wrapper.text()).toContain('ETH Mean Reversion Retry')

    await wrapper.get('input[data-test="backtest-history-search"]').setValue('ETH')

    expect(wrapper.text()).not.toContain('Alpha Breakout April')
    expect(wrapper.text()).toContain('ETH Mean Reversion Retry')

    await wrapper.get('[data-test="history-open-report-job-history-2"]').trigger('click')

    expect(pushMock).toHaveBeenCalledWith({ name: 'backtest-report', params: { jobId: 'job-history-2' } })
  })
})

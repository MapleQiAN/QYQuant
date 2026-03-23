import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import BacktestsView from './BacktestsView.vue'

const {
  pushMock,
  fetchRecentMock,
  fetchRuntimeDescriptorMock,
  fetchMyQuotaMock,
  fetchBacktestStatusMock,
  submitBacktestMock,
} = vi.hoisted(() => ({
  pushMock: vi.fn(),
  fetchRecentMock: vi.fn(),
  fetchRuntimeDescriptorMock: vi.fn(),
  fetchMyQuotaMock: vi.fn(),
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

vi.mock('../api/backtests', () => ({
  fetchBacktestStatus: fetchBacktestStatusMock,
  submitBacktest: submitBacktestMock,
}))

describe('BacktestsView', () => {
  beforeEach(() => {
    pushMock.mockReset()
    fetchRecentMock.mockReset()
    fetchRuntimeDescriptorMock.mockReset()
    fetchMyQuotaMock.mockReset()
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
    expect(wrapper.text()).toContain('剩余回测次数')
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

    expect(actionButton.text()).toBe('升级套餐解锁更多次数')
    expect(actionButton.classes()).toContain('btn--upgrade')
    expect(actionButton.attributes('disabled')).toBeDefined()
  })
})

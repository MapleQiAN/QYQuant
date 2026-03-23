// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import BotDetailModal from './BotDetailModal.vue'
import type { SimulationBot } from '../../types/Simulation'

const { getSimRecordsMock, getSimTradesMock, createBotStreamMock, closeMock } = vi.hoisted(() => ({
  getSimRecordsMock: vi.fn(),
  getSimTradesMock: vi.fn(),
  createBotStreamMock: vi.fn(),
  closeMock: vi.fn(),
}))

vi.mock('../../api/simulation', () => ({
  getSimRecords: getSimRecordsMock,
  getSimTrades: getSimTradesMock,
  createBotStream: createBotStreamMock,
}))

const makeBot = (overrides: Partial<SimulationBot> = {}): SimulationBot => ({
  id: 'bot-1',
  strategy_id: 'strategy-1',
  strategy_name: '双均线策略',
  initial_capital: '100000.00',
  status: 'active',
  created_at: '2026-03-23T16:00:00+08:00',
  ...overrides,
})

describe('BotDetailModal', () => {
  beforeEach(() => {
    getSimRecordsMock.mockReset()
    getSimTradesMock.mockReset()
    createBotStreamMock.mockReset()
    closeMock.mockReset()

    getSimRecordsMock.mockResolvedValue([
      {
        trade_date: '2026-03-20',
        equity: '105000.00',
        cash: '55000.00',
        daily_return: '0.000500',
      },
    ])
    getSimTradesMock.mockResolvedValue([])
    createBotStreamMock.mockReturnValue({ close: closeMock })
    window.localStorage.setItem('qyquant-token', 'token-123')
  })

  it('loads records and trades on mount', async () => {
    mount(BotDetailModal, {
      props: { bot: makeBot() },
      global: {
        stubs: {
          SimulationChart: { template: '<div class="chart-stub" />' },
        },
      },
    })

    await flushPromises()

    expect(getSimRecordsMock).toHaveBeenCalledWith('bot-1')
    expect(getSimTradesMock).toHaveBeenCalledWith('bot-1')
  })

  it('renders chart when records are returned', async () => {
    const wrapper = mount(BotDetailModal, {
      props: { bot: makeBot() },
      global: {
        stubs: {
          SimulationChart: { template: '<div class="chart-stub" />' },
        },
      },
    })

    await flushPromises()

    expect(wrapper.find('.chart-stub').exists()).toBe(true)
  })

  it('shows empty trade hint when no trades are returned', async () => {
    const wrapper = mount(BotDetailModal, {
      props: { bot: makeBot() },
      global: {
        stubs: {
          SimulationChart: { template: '<div class="chart-stub" />' },
        },
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('暂无买卖记录')
  })

  it('emits close when overlay background is clicked', async () => {
    const wrapper = mount(BotDetailModal, {
      props: { bot: makeBot() },
      global: {
        stubs: {
          SimulationChart: { template: '<div class="chart-stub" />' },
        },
      },
    })

    await flushPromises()
    await wrapper.find('.modal-overlay').trigger('click')

    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('closes event source on unmount', async () => {
    const wrapper = mount(BotDetailModal, {
      props: { bot: makeBot() },
      global: {
        stubs: {
          SimulationChart: { template: '<div class="chart-stub" />' },
        },
      },
    })

    await flushPromises()
    wrapper.unmount()

    expect(closeMock).toHaveBeenCalledTimes(1)
  })
})

// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import MarketplaceStrategyDetailView from './MarketplaceStrategyDetailView.vue'

const {
  pushMock,
  fetchMarketplaceStrategyDetailMock,
  fetchMarketplaceStrategyEquityCurveMock,
} = vi.hoisted(() => ({
  pushMock: vi.fn(),
  fetchMarketplaceStrategyDetailMock: vi.fn(),
  fetchMarketplaceStrategyEquityCurveMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
  RouterLink: { template: '<a><slot /></a>' },
  useRouter: () => ({
    push: pushMock,
  }),
  useRoute: () => ({
    params: {
      strategyId: 'strategy-1',
    },
  }),
}))

vi.mock('../api/strategies', () => ({
  fetchMarketplaceStrategyDetail: fetchMarketplaceStrategyDetailMock,
  fetchMarketplaceStrategyEquityCurve: fetchMarketplaceStrategyEquityCurveMock,
}))

vi.mock('../components/backtest/EquityCurveChart.vue', () => ({
  default: {
    props: ['points'],
    template: '<div data-test="equity-chart">{{ points.length }}</div>',
  },
}))

describe('MarketplaceStrategyDetailView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    pushMock.mockReset()
    fetchMarketplaceStrategyDetailMock.mockReset()
    fetchMarketplaceStrategyEquityCurveMock.mockReset()
    fetchMarketplaceStrategyEquityCurveMock.mockResolvedValue({
      dates: [1700000000000, 1700086400000],
      values: [100000, 101250.5],
    })
  })

  it('renders marketplace strategy detail and routes trial CTA to import flow', async () => {
    fetchMarketplaceStrategyDetailMock.mockResolvedValue({
      id: 'strategy-1',
      title: 'Golden Breakout',
      description: 'Trend-following breakout strategy for gold.',
      category: 'trend-following',
      tags: ['gold', 'breakout'],
      display_metrics: {
        totalReturn: 18.6,
        maxDrawdown: -6.2,
        sharpeRatio: 1.54,
        winRate: 62,
      },
      is_verified: true,
      created_at: '2026-03-18T12:00:00+08:00',
      author: {
        nickname: 'QuantAlice',
        avatar_url: 'https://example.com/avatar.png',
      },
      already_imported: false,
      imported_strategy_id: null,
    })

    const wrapper = mount(MarketplaceStrategyDetailView, {
      global: {
        plugins: [createPinia()],
      },
    })
    await flushPromises()

    expect(fetchMarketplaceStrategyDetailMock).toHaveBeenCalledWith('strategy-1')
    expect(fetchMarketplaceStrategyEquityCurveMock).toHaveBeenCalledWith('strategy-1')
    expect(wrapper.text()).toContain('Golden Breakout')
    expect(wrapper.text()).toContain('QuantAlice')
    expect(wrapper.text()).toContain('18.6')
    expect(wrapper.get('[data-test="equity-chart"]').text()).toBe('2')

    await wrapper.get('[data-test="detail-cta"]').trigger('click')

    expect(pushMock).toHaveBeenCalledWith({
      name: 'strategy-library',
      query: { marketplaceStrategyId: 'strategy-1' },
    })
  })

  it('shows imported state and routes to the imported strategy configuration', async () => {
    fetchMarketplaceStrategyDetailMock.mockResolvedValue({
      id: 'strategy-1',
      title: 'Golden Breakout',
      description: 'Trend-following breakout strategy for gold.',
      category: 'trend-following',
      tags: ['gold'],
      display_metrics: {
        totalReturn: 18.6,
      },
      is_verified: false,
      created_at: '2026-03-18T12:00:00+08:00',
      author: {
        nickname: 'QuantAlice',
        avatar_url: 'https://example.com/avatar.png',
      },
      already_imported: true,
      imported_strategy_id: 'imported-1',
    })

    const wrapper = mount(MarketplaceStrategyDetailView, {
      global: {
        plugins: [createPinia()],
      },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Already in strategy library')

    await wrapper.get('[data-test="detail-cta"]').trigger('click')

    expect(pushMock).toHaveBeenCalledWith({
      name: 'strategy-parameters',
      params: { strategyId: 'imported-1' },
    })
  })
})

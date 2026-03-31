// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import MarketplaceStrategyDetailView from './MarketplaceStrategyDetailView.vue'
import { useUserStore } from '../stores/user'

const {
  pushMock,
  fetchMarketplaceStrategyDetailMock,
  fetchMarketplaceStrategyEquityCurveMock,
  fetchMarketplaceStrategyImportStatusMock,
  importMarketplaceStrategyMock,
  reportMarketplaceStrategyMock,
  toastSuccessMock,
} = vi.hoisted(() => ({
  pushMock: vi.fn(),
  fetchMarketplaceStrategyDetailMock: vi.fn(),
  fetchMarketplaceStrategyEquityCurveMock: vi.fn(),
  fetchMarketplaceStrategyImportStatusMock: vi.fn(),
  importMarketplaceStrategyMock: vi.fn(),
  reportMarketplaceStrategyMock: vi.fn(),
  toastSuccessMock: vi.fn(),
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
  fetchMarketplaceStrategyImportStatus: fetchMarketplaceStrategyImportStatusMock,
  importMarketplaceStrategy: importMarketplaceStrategyMock,
  reportMarketplaceStrategy: reportMarketplaceStrategyMock,
}))

vi.mock('../lib/toast', () => ({
  toast: {
    success: toastSuccessMock,
    error: vi.fn(),
  }
}))

vi.mock('../components/backtest/EquityCurveChart.vue', () => ({
  default: {
    props: ['points'],
    template: '<div data-test="equity-chart">{{ points.length }}</div>',
  },
}))

describe('MarketplaceStrategyDetailView', () => {
  beforeEach(() => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const userStore = useUserStore(pinia)
    userStore.profile.id = 'test-user-id'
    pushMock.mockReset()
    fetchMarketplaceStrategyDetailMock.mockReset()
    fetchMarketplaceStrategyEquityCurveMock.mockReset()
    fetchMarketplaceStrategyImportStatusMock.mockReset()
    importMarketplaceStrategyMock.mockReset()
    reportMarketplaceStrategyMock.mockReset()
    toastSuccessMock.mockReset()
    fetchMarketplaceStrategyEquityCurveMock.mockResolvedValue({
      dates: [1700000000000, 1700086400000],
      values: [100000, 101250.5],
    })
    fetchMarketplaceStrategyImportStatusMock.mockResolvedValue({
      imported: false,
      userStrategyId: null,
    })
  })

  it('renders marketplace strategy detail and imports on trial CTA click', async () => {
    fetchMarketplaceStrategyDetailMock.mockResolvedValue({
      id: 'strategy-1',
      title: 'Golden Breakout',
      description: 'Trend-following breakout strategy for gold.',
      category: 'trend-following',
      tags: ['gold', 'breakout'],
      displayMetrics: {
        totalReturn: 18.6,
        maxDrawdown: -6.2,
        sharpeRatio: 1.54,
        winRate: 62,
      },
      isVerified: true,
      createdAt: '2026-03-18T12:00:00+08:00',
      author: {
        nickname: 'QuantAlice',
        avatarUrl: 'https://example.com/avatar.png',
      },
      alreadyImported: false,
      importedStrategyId: null,
      canReport: true,
    })
    importMarketplaceStrategyMock.mockResolvedValue({
      strategyId: 'imported-1',
      redirectTo: '/backtest/configure?strategy_id=imported-1',
    })

    const wrapper = mount(MarketplaceStrategyDetailView, {
      global: {
        plugins: [createPinia()],
      },
    })
    await flushPromises()

    expect(fetchMarketplaceStrategyDetailMock).toHaveBeenCalledWith('strategy-1')
    expect(fetchMarketplaceStrategyEquityCurveMock).toHaveBeenCalledWith('strategy-1')
    expect(fetchMarketplaceStrategyImportStatusMock).toHaveBeenCalledWith('strategy-1')
    expect(wrapper.text()).toContain('Golden Breakout')
    expect(wrapper.text()).toContain('QuantAlice')
    expect(wrapper.text()).toContain('18.6')
    expect(wrapper.get('[data-test="equity-chart"]').text()).toBe('2')

    await wrapper.get('[data-test="detail-cta"]').trigger('click')
    await flushPromises()

    expect(importMarketplaceStrategyMock).toHaveBeenCalledWith('strategy-1')
    expect(pushMock).toHaveBeenCalledWith('/backtest/configure?strategy_id=imported-1')
    expect(toastSuccessMock).toHaveBeenCalledWith('策略已导入，即将跳转回测配置')
  })

  it('shows imported state and routes to the imported strategy configuration', async () => {
    fetchMarketplaceStrategyDetailMock.mockResolvedValue({
      id: 'strategy-1',
      title: 'Golden Breakout',
      description: 'Trend-following breakout strategy for gold.',
      category: 'trend-following',
      tags: ['gold'],
      displayMetrics: {
        totalReturn: 18.6,
      },
      isVerified: false,
      createdAt: '2026-03-18T12:00:00+08:00',
      author: {
        nickname: 'QuantAlice',
        avatarUrl: 'https://example.com/avatar.png',
      },
      alreadyImported: true,
      importedStrategyId: 'imported-1',
      canReport: false,
    })
    fetchMarketplaceStrategyImportStatusMock.mockResolvedValue({
      imported: true,
      userStrategyId: 'imported-1',
    })

    const wrapper = mount(MarketplaceStrategyDetailView, {
      global: {
        plugins: [createPinia()],
      },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Already in strategy library')
    expect(wrapper.find('[data-test="direct-backtest-link"]').exists()).toBe(true)

    await wrapper.get('[data-test="direct-backtest-link"]').trigger('click')
    await flushPromises()

    expect(pushMock).toHaveBeenCalledWith('/backtest/configure?strategy_id=imported-1')
  })

  it('opens report form and submits a strategy report', async () => {
    fetchMarketplaceStrategyDetailMock.mockResolvedValue({
      id: 'strategy-1',
      title: 'Golden Breakout',
      description: 'Trend-following breakout strategy for gold.',
      category: 'trend-following',
      tags: ['gold'],
      displayMetrics: {
        totalReturn: 18.6,
      },
      isVerified: false,
      createdAt: '2026-03-18T12:00:00+08:00',
      author: {
        nickname: 'QuantAlice',
        avatarUrl: 'https://example.com/avatar.png',
      },
      alreadyImported: false,
      importedStrategyId: null,
      canReport: true,
    })
    reportMarketplaceStrategyMock.mockResolvedValue({
      reportId: 'report-1',
    })

    const wrapper = mount(MarketplaceStrategyDetailView, {
      global: {
        plugins: [createPinia()],
      },
    })
    await flushPromises()

    expect(wrapper.find('[data-test="open-report"]').exists()).toBe(true)

    await wrapper.get('[data-test="open-report"]').trigger('click')
    await wrapper.get('[data-test="report-reason"]').setValue('misleading claim in description')
    await wrapper.get('[data-test="submit-report"]').trigger('click')
    await flushPromises()

    expect(reportMarketplaceStrategyMock).toHaveBeenCalledWith('strategy-1', 'misleading claim in description')
  })
})

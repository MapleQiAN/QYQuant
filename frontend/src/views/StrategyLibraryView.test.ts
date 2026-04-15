// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import StrategyLibraryView from './StrategyLibraryView.vue'
import StrategyPublishFlow from '../components/strategy/StrategyPublishFlow.vue'

const {
  pushMock,
  fetchStrategiesMock,
  fetchMarketplaceStrategiesMock,
  deleteStrategyMock,
  importStrategyMock,
  publishStrategyMock,
  getPublishStatusMock,
  toastSuccessMock,
} = vi.hoisted(() => ({
  pushMock: vi.fn(),
  fetchStrategiesMock: vi.fn(),
  fetchMarketplaceStrategiesMock: vi.fn(),
  deleteStrategyMock: vi.fn(),
  importStrategyMock: vi.fn(),
  publishStrategyMock: vi.fn(),
  getPublishStatusMock: vi.fn(),
  toastSuccessMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
  RouterLink: {
    template: '<a><slot /></a>'
  },
  useRoute: () => ({
    query: {},
  }),
  useRouter: () => ({
    push: pushMock
  })
}))

vi.mock('../api/strategies', () => ({
  fetchStrategies: fetchStrategiesMock,
  fetchMarketplaceStrategies: fetchMarketplaceStrategiesMock,
  deleteStrategy: deleteStrategyMock,
  importStrategy: importStrategyMock
}))

vi.mock('../stores', () => ({
  useUserStore: () => ({
    onboardingHighlightTarget: null,
    setGuidedBacktestStrategy: vi.fn(),
    setGuidedBacktestStep: vi.fn(),
    setOnboardingHighlightTarget: vi.fn(),
  }),
  useMarketplaceStore: () => ({
    publishStrategy: publishStrategyMock,
    getPublishStatus: getPublishStatusMock
  })
}))

vi.mock('../lib/toast', () => ({
  toast: {
    success: toastSuccessMock,
    error: vi.fn(),
  }
}))

describe('StrategyLibraryView', () => {
  beforeEach(() => {
    pushMock.mockClear()
    fetchStrategiesMock.mockReset()
    fetchMarketplaceStrategiesMock.mockReset()
    deleteStrategyMock.mockReset()
    importStrategyMock.mockReset()
    publishStrategyMock.mockReset()
    getPublishStatusMock.mockReset()
    toastSuccessMock.mockReset()
    vi.stubGlobal('confirm', vi.fn(() => true))
  })

  function mountView() {
    return mount(StrategyLibraryView, {
      global: {
        plugins: [
          createI18n({
            legacy: false,
            locale: 'en',
            messages: {
              en: {
                strategy: {
                  library: {
                    pageTitle: 'Strategy Library',
                    pageSubtitle: 'Manage your strategies',
                    backToDashboard: 'Back',
                    createStrategy: 'Create strategy',
                    openImportWizard: 'Open import wizard',
                    guidedStrategy: 'Guided strategy',
                    guidedStrategyDesc: 'Guided picks',
                    loadingGuided: 'Loading guided',
                    failedToLoadGuided: 'Failed to load guided',
                    viewDetails: 'View details',
                    useThisStrategy: 'Use this strategy',
                    importStrategy: 'Import strategy',
                    importStrategyDesc: 'Import',
                    importNote: 'Import note',
                    myStrategies: 'My strategies',
                    itemCount: '{count} items',
                    loadingLibrary: 'Loading library',
                    failedToLoadLibrary: 'Failed to load library',
                    noStrategies: 'No strategies',
                    noDescription: 'No description',
                    delete: 'Delete',
                    previous: 'Previous',
                    next: 'Next',
                    unknownTime: 'Unknown',
                    pendingReview: 'Pending review',
                    approved: 'Approved',
                    rejected: 'Rejected',
                    notPublished: 'Draft',
                    resubmit: 'Resubmit',
                    publishToMarketplace: 'Publish',
                    failedToSubmit: 'Failed to submit',
                    deleteConfirm: 'Delete?',
                  }
                }
              }
            }
          })
        ]
      }
    })
  }

  it('loads and renders strategy library rows', async () => {
    fetchStrategiesMock.mockResolvedValue({
      items: [
        {
          id: 'strategy-1',
          name: 'Golden Cross',
          description: 'Trend following',
          tags: ['gold'],
          category: 'trend-following',
          source: 'upload',
          createdAt: 123
        }
      ],
      page: 1,
      perPage: 10,
      total: 1
    })
    deleteStrategyMock.mockResolvedValue({ deletedId: 'strategy-1' })

    const wrapper = mountView()
    await flushPromises()

    expect(fetchStrategiesMock).toHaveBeenCalledWith({ page: 1, perPage: 10 })
    expect(wrapper.text()).toContain('Golden Cross')

    await wrapper.get('[data-test="delete-strategy-1"]').trigger('click')
    await flushPromises()

    expect(deleteStrategyMock).toHaveBeenCalledWith('strategy-1')
    expect(toastSuccessMock).toHaveBeenCalledWith('策略已删除')
  })

  it('opens the import wizard from the library entry point', async () => {
    fetchStrategiesMock.mockResolvedValue({ items: [], page: 1, perPage: 10, total: 0 })

    const wrapper = mountView()
    await flushPromises()

    await wrapper.get('[data-test="open-import-wizard"]').trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/strategies/import')
    expect(importStrategyMock).not.toHaveBeenCalled()
  })

  it('opens the strategy creation page from the library header', async () => {
    fetchStrategiesMock.mockResolvedValue({ items: [], page: 1, perPage: 10, total: 0 })

    const wrapper = mountView()
    await flushPromises()

    await wrapper.get('[data-test="open-create-strategy"]').trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/strategies/new')
  })

  it('shows review status and disables publish button for pending strategies', async () => {
    fetchStrategiesMock.mockResolvedValue({
      items: [
        {
          id: 'strategy-1',
          name: 'Pending Strategy',
          description: 'Trend following',
          tags: ['gold'],
          category: 'trend-following',
          source: 'upload',
          createdAt: 123,
          reviewStatus: 'pending',
          isPublic: false
        }
      ],
      page: 1,
      perPage: 10,
      total: 1
    })

    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.get('[data-test="publish-status-strategy-1"]').text()).toContain('Pending review')
    expect(wrapper.get('[data-test="publish-open-strategy-1"]').attributes('disabled')).toBeDefined()
  })

  it('submits rejected strategies for republish and refreshes row status', async () => {
    fetchStrategiesMock.mockResolvedValue({
      items: [
        {
          id: 'strategy-1',
          name: 'Rejected Strategy',
          description: 'Trend following',
          tags: ['gold'],
          category: 'trend-following',
          source: 'upload',
          createdAt: 123,
          reviewStatus: 'rejected',
          isPublic: false,
          returns: 18.4,
          maxDrawdown: -7.2,
          winRate: 0,
          status: 'draft',
          symbol: 'BTCUSDT',
          lastUpdate: 0,
          trades: 0
        }
      ],
      page: 1,
      perPage: 10,
      total: 1
    })
    publishStrategyMock.mockResolvedValue({ strategyId: 'strategy-1', reviewStatus: 'pending' })
    getPublishStatusMock.mockResolvedValue({ reviewStatus: 'pending', isPublic: false })

    const wrapper = mountView()
    await flushPromises()

    await wrapper.get('[data-test="publish-open-strategy-1"]').trigger('click')
    wrapper.getComponent(StrategyPublishFlow).vm.$emit('submit', {
      strategyId: 'strategy-1',
      title: 'Rejected Strategy',
      description: 'Updated description',
      tags: ['gold'],
      category: 'trend-following',
      displayMetrics: {
        sharpe_ratio: 1.42,
        max_drawdown: -7.2,
        total_return: 18.4
      }
    })
    await flushPromises()

    expect(publishStrategyMock).toHaveBeenCalled()
    expect(getPublishStatusMock).toHaveBeenCalledWith('strategy-1')
    expect(wrapper.get('[data-test="publish-status-strategy-1"]').text()).toContain('Pending review')
    expect(toastSuccessMock).toHaveBeenCalledWith('发布申请已提交')
  })
})

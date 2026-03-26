import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useMarketplaceStore } from './useMarketplaceStore'

const {
  fetchMarketplaceStrategiesMock,
  fetchMarketplaceStrategyDetailMock,
  fetchMarketplaceStrategyEquityCurveMock,
  importMarketplaceStrategyMock,
  fetchMarketplaceStrategyImportStatusMock,
  publishMarketplaceStrategyMock,
  fetchMarketplacePublishStatusMock,
  reportMarketplaceStrategyMock
} = vi.hoisted(() => ({
  fetchMarketplaceStrategiesMock: vi.fn(),
  fetchMarketplaceStrategyDetailMock: vi.fn(),
  fetchMarketplaceStrategyEquityCurveMock: vi.fn(),
  importMarketplaceStrategyMock: vi.fn(),
  fetchMarketplaceStrategyImportStatusMock: vi.fn(),
  publishMarketplaceStrategyMock: vi.fn(),
  fetchMarketplacePublishStatusMock: vi.fn(),
  reportMarketplaceStrategyMock: vi.fn()
}))

vi.mock('../api/strategies', () => ({
  fetchMarketplaceStrategies: fetchMarketplaceStrategiesMock,
  fetchMarketplaceStrategyDetail: fetchMarketplaceStrategyDetailMock,
  fetchMarketplaceStrategyEquityCurve: fetchMarketplaceStrategyEquityCurveMock,
  importMarketplaceStrategy: importMarketplaceStrategyMock,
  fetchMarketplaceStrategyImportStatus: fetchMarketplaceStrategyImportStatusMock,
  publishMarketplaceStrategy: publishMarketplaceStrategyMock,
  fetchMarketplacePublishStatus: fetchMarketplacePublishStatusMock,
  reportMarketplaceStrategy: reportMarketplaceStrategyMock
}))

describe('useMarketplaceStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    fetchMarketplaceStrategiesMock.mockReset()
    fetchMarketplaceStrategyDetailMock.mockReset()
    fetchMarketplaceStrategyEquityCurveMock.mockReset()
    importMarketplaceStrategyMock.mockReset()
    fetchMarketplaceStrategyImportStatusMock.mockReset()
    publishMarketplaceStrategyMock.mockReset()
    fetchMarketplacePublishStatusMock.mockReset()
    reportMarketplaceStrategyMock.mockReset()
  })

  it('loads marketplace list and stores meta state', async () => {
    fetchMarketplaceStrategiesMock.mockResolvedValue({
      data: [
        {
          id: 'strategy-1',
          title: 'Alpha Wave',
          name: 'alpha-wave',
          description: 'Momentum strategy',
          category: 'momentum',
          tags: ['gold'],
          isVerified: true,
          displayMetrics: { annualized_return: 18.4, max_drawdown: -8.6, sharpe_ratio: 1.45 },
          author: { nickname: 'Market Author', avatarUrl: 'https://example.com/avatar.png' }
        }
      ],
      meta: {
        total: 24,
        page: 2,
        pageSize: 20
      }
    })

    const store = useMarketplaceStore()
    await store.fetchStrategies(2)

    expect(fetchMarketplaceStrategiesMock).toHaveBeenCalledWith({
      page: 2,
      pageSize: 20,
      q: undefined,
      category: null,
      verified: false,
      annualReturnGte: null,
      maxDrawdownLte: null
    })
    expect(store.strategies).toHaveLength(1)
    expect(store.page).toBe(2)
    expect(store.total).toBe(24)
    expect(store.pageSize).toBe(20)
    expect(store.loading).toBe(false)
  })

  it('loads featured strategies separately', async () => {
    fetchMarketplaceStrategiesMock.mockResolvedValue({
      data: [
        {
          id: 'featured-1',
          title: 'Featured Alpha',
          name: 'featured-alpha',
          description: 'Featured strategy',
          category: 'trend',
          tags: ['featured'],
          isVerified: false,
          displayMetrics: { annualized_return: 12.2, max_drawdown: -6.4, sharpe_ratio: 1.1 },
          author: { nickname: 'Editor', avatarUrl: '' }
        }
      ],
      meta: {
        total: 1,
        page: 1,
        pageSize: 6
      }
    })

    const store = useMarketplaceStore()
    await store.fetchFeatured()

    expect(fetchMarketplaceStrategiesMock).toHaveBeenCalledWith({ featured: true, pageSize: 6 })
    expect(store.featuredStrategies).toHaveLength(1)
    expect(store.featuredLoading).toBe(false)
    expect(store.strategies).toEqual([])
  })

  it('keeps main list data available when featured request fails', async () => {
    fetchMarketplaceStrategiesMock.mockResolvedValueOnce({
      data: [
        {
          id: 'strategy-1',
          title: 'Alpha Wave',
          name: 'alpha-wave',
          description: 'Momentum strategy',
          category: 'momentum',
          tags: ['gold'],
          isVerified: true,
          displayMetrics: { annualized_return: 18.4, max_drawdown: -8.6, sharpe_ratio: 1.45 },
          author: { nickname: 'Market Author', avatarUrl: 'https://example.com/avatar.png' }
        }
      ],
      meta: {
        total: 24,
        page: 1,
        pageSize: 20
      }
    })
    fetchMarketplaceStrategiesMock.mockRejectedValueOnce(new Error('featured failed'))

    const store = useMarketplaceStore()
    await store.fetchStrategies(1)
    await store.fetchFeatured()

    expect(store.strategies).toHaveLength(1)
    expect(store.error).toBeNull()
    expect(store.featuredError).toBe('featured failed')
  })

  it('loads strategy detail and equity curve', async () => {
    fetchMarketplaceStrategyDetailMock.mockResolvedValue({
      id: 'strategy-1',
      title: 'Golden Breakout',
      author: { nickname: 'QuantAlice', avatarUrl: 'https://example.com/avatar.png' },
      displayMetrics: { sharpeRatio: 1.54 },
      alreadyImported: false
    })
    fetchMarketplaceStrategyEquityCurveMock.mockResolvedValue({
      dates: [1700000000000, 1700086400000],
      values: [100000, 101250.5]
    })

    const store = useMarketplaceStore()
    await store.fetchStrategyDetail('strategy-1')
    await store.fetchEquityCurve('strategy-1')

    expect(fetchMarketplaceStrategyDetailMock).toHaveBeenCalledWith('strategy-1')
    expect(fetchMarketplaceStrategyEquityCurveMock).toHaveBeenCalledWith('strategy-1')
    expect(store.currentStrategy?.title).toBe('Golden Breakout')
    expect(store.equityCurve.values).toEqual([100000, 101250.5])
    expect(store.error).toBeNull()
  })

  it('checks import status and merges it into the loaded strategy detail', async () => {
    fetchMarketplaceStrategyDetailMock.mockResolvedValue({
      id: 'strategy-1',
      title: 'Golden Breakout',
      author: { nickname: 'QuantAlice', avatarUrl: 'https://example.com/avatar.png' },
      displayMetrics: { sharpeRatio: 1.54 },
      alreadyImported: false,
      importedStrategyId: null
    })
    fetchMarketplaceStrategyImportStatusMock.mockResolvedValue({
      imported: true,
      userStrategyId: 'imported-1'
    })

    const store = useMarketplaceStore()
    await store.fetchStrategyDetail('strategy-1')
    await store.checkImportStatus('strategy-1')

    expect(fetchMarketplaceStrategyImportStatusMock).toHaveBeenCalledWith('strategy-1')
    expect(store.currentStrategy?.alreadyImported).toBe(true)
    expect(store.currentStrategy?.importedStrategyId).toBe('imported-1')
  })

  it('imports a marketplace strategy and updates the current strategy state', async () => {
    fetchMarketplaceStrategyDetailMock.mockResolvedValue({
      id: 'strategy-1',
      title: 'Golden Breakout',
      author: { nickname: 'QuantAlice', avatarUrl: 'https://example.com/avatar.png' },
      displayMetrics: {},
      alreadyImported: false,
      importedStrategyId: null
    })
    importMarketplaceStrategyMock.mockResolvedValue({
      strategyId: 'imported-1',
      redirectTo: '/backtest/configure?strategy_id=imported-1'
    })

    const store = useMarketplaceStore()
    await store.fetchStrategyDetail('strategy-1')

    const result = await store.importStrategy('strategy-1')

    expect(importMarketplaceStrategyMock).toHaveBeenCalledWith('strategy-1')
    expect(result).toEqual({
      strategyId: 'imported-1',
      redirectTo: '/backtest/configure?strategy_id=imported-1'
    })
    expect(store.currentStrategy?.alreadyImported).toBe(true)
    expect(store.currentStrategy?.importedStrategyId).toBe('imported-1')
  })

  it('forwards active filters when loading marketplace list', async () => {
    fetchMarketplaceStrategiesMock.mockResolvedValue({
      data: [],
      meta: {
        total: 0,
        page: 1,
        pageSize: 20
      }
    })

    const store = useMarketplaceStore()
    store.setFilter('q', '均线')
    store.setFilter('category', 'trend-following')
    store.setFilter('verified', true)
    store.setFilter('annualReturnGte', 20)

    await store.fetchStrategies(1)

    expect(fetchMarketplaceStrategiesMock).toHaveBeenCalledWith({
      page: 1,
      pageSize: 20,
      q: '均线',
      category: 'trend-following',
      verified: true,
      annualReturnGte: 20,
      maxDrawdownLte: null
    })
  })

  it('publishes a strategy and fetches latest publish status', async () => {
    publishMarketplaceStrategyMock.mockResolvedValue({
      strategyId: 'strategy-1',
      reviewStatus: 'pending'
    })
    fetchMarketplacePublishStatusMock.mockResolvedValue({
      reviewStatus: 'pending',
      isPublic: false
    })

    const store = useMarketplaceStore()
    const publishResult = await store.publishStrategy({
      strategyId: 'strategy-1',
      title: '均线趋势增强版',
      description: 'desc',
      tags: ['均线'],
      category: 'trend-following',
      displayMetrics: {
        sharpe_ratio: 1.4,
        max_drawdown: -8.2,
        total_return: 20.1
      }
    })
    const status = await store.getPublishStatus('strategy-1')

    expect(publishMarketplaceStrategyMock).toHaveBeenCalledWith({
      strategyId: 'strategy-1',
      title: '均线趋势增强版',
      description: 'desc',
      tags: ['均线'],
      category: 'trend-following',
      displayMetrics: {
        sharpe_ratio: 1.4,
        max_drawdown: -8.2,
        total_return: 20.1
      }
    })
    expect(fetchMarketplacePublishStatusMock).toHaveBeenCalledWith('strategy-1')
    expect(publishResult.reviewStatus).toBe('pending')
    expect(status).toEqual({ reviewStatus: 'pending', isPublic: false })
  })

  it('submits a report for the current marketplace strategy', async () => {
    fetchMarketplaceStrategyDetailMock.mockResolvedValue({
      id: 'strategy-1',
      title: 'Golden Breakout',
      author: { nickname: 'QuantAlice', avatarUrl: 'https://example.com/avatar.png' },
      displayMetrics: {},
      alreadyImported: false,
      importedStrategyId: null,
      canReport: true
    })
    reportMarketplaceStrategyMock.mockResolvedValue({
      reportId: 'report-1'
    })

    const store = useMarketplaceStore()
    await store.fetchStrategyDetail('strategy-1')
    const result = await store.reportStrategy('strategy-1', 'misleading claim in description')

    expect(reportMarketplaceStrategyMock).toHaveBeenCalledWith('strategy-1', 'misleading claim in description')
    expect(result).toEqual({ reportId: 'report-1' })
    expect(store.reportLoading).toBe(false)
  })
})

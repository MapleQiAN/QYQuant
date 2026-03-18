import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useMarketplaceStore } from './useMarketplaceStore'

const {
  fetchMarketplaceStrategiesMock,
  fetchMarketplaceStrategyDetailMock,
  fetchMarketplaceStrategyEquityCurveMock
} = vi.hoisted(() => ({
  fetchMarketplaceStrategiesMock: vi.fn(),
  fetchMarketplaceStrategyDetailMock: vi.fn(),
  fetchMarketplaceStrategyEquityCurveMock: vi.fn()
}))

vi.mock('../api/strategies', () => ({
  fetchMarketplaceStrategies: fetchMarketplaceStrategiesMock,
  fetchMarketplaceStrategyDetail: fetchMarketplaceStrategyDetailMock,
  fetchMarketplaceStrategyEquityCurve: fetchMarketplaceStrategyEquityCurveMock
}))

describe('useMarketplaceStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    fetchMarketplaceStrategiesMock.mockReset()
    fetchMarketplaceStrategyDetailMock.mockReset()
    fetchMarketplaceStrategyEquityCurveMock.mockReset()
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

    expect(fetchMarketplaceStrategiesMock).toHaveBeenCalledWith({ page: 2, pageSize: 20 })
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
})

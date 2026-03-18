import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useMarketplaceStore } from './useMarketplaceStore'

const {
  fetchMarketplaceStrategyDetailMock,
  fetchMarketplaceStrategyEquityCurveMock,
} = vi.hoisted(() => ({
  fetchMarketplaceStrategyDetailMock: vi.fn(),
  fetchMarketplaceStrategyEquityCurveMock: vi.fn(),
}))

vi.mock('../api/strategies', () => ({
  fetchMarketplaceStrategyDetail: fetchMarketplaceStrategyDetailMock,
  fetchMarketplaceStrategyEquityCurve: fetchMarketplaceStrategyEquityCurveMock,
}))

describe('useMarketplaceStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    fetchMarketplaceStrategyDetailMock.mockReset()
    fetchMarketplaceStrategyEquityCurveMock.mockReset()
  })

  it('loads strategy detail and equity curve', async () => {
    fetchMarketplaceStrategyDetailMock.mockResolvedValue({
      id: 'strategy-1',
      title: 'Golden Breakout',
      author: { nickname: 'QuantAlice', avatar_url: 'https://example.com/avatar.png' },
      display_metrics: { sharpeRatio: 1.54 },
    })
    fetchMarketplaceStrategyEquityCurveMock.mockResolvedValue({
      dates: [1700000000000, 1700086400000],
      values: [100000, 101250.5],
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

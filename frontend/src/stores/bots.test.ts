import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useBotsStore } from './bots'

const {
  fetchRecentMock,
  fetchBotsMock,
  createBotMock,
  updateBotStatusMock,
  fetchBotPositionsMock,
  fetchBotPerformanceMock,
} = vi.hoisted(() => ({
  fetchRecentMock: vi.fn(),
  fetchBotsMock: vi.fn(),
  createBotMock: vi.fn(),
  updateBotStatusMock: vi.fn(),
  fetchBotPositionsMock: vi.fn(),
  fetchBotPerformanceMock: vi.fn(),
}))

vi.mock('../api/bots', () => ({
  fetchRecent: fetchRecentMock,
  fetchBots: fetchBotsMock,
  createBot: createBotMock,
  updateBotStatus: updateBotStatusMock,
  fetchBotPositions: fetchBotPositionsMock,
  fetchBotPerformance: fetchBotPerformanceMock,
}))

describe('bots store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    fetchRecentMock.mockReset()
    fetchBotsMock.mockReset()
    createBotMock.mockReset()
    updateBotStatusMock.mockReset()
    fetchBotPositionsMock.mockReset()
    fetchBotPerformanceMock.mockReset()
  })

  it('loads recent bots and clears error', async () => {
    fetchRecentMock.mockResolvedValueOnce([{ id: 'bot-1' }])
    const store = useBotsStore()
    await store.loadRecent()
    expect(store.error).toBeNull()
    expect(store.recent.length).toBe(1)
  })

  it('loads managed bots, creates one, and updates status', async () => {
    fetchBotsMock.mockResolvedValueOnce([
      {
        id: 'bot-1',
        name: '沪深择时一号',
        strategy: '沪深择时',
        strategyId: 'strategy-1',
        strategyName: '沪深择时',
        integrationId: 'integration-1',
        integrationDisplayName: '主账户',
        status: 'active',
        profit: 0,
        totalReturnRate: 0,
        runtime: '0h',
        capital: 100000,
        tags: ['主账户'],
        paper: false,
        createdAt: '2026-04-18T10:00:00+08:00',
        lastErrorMessage: null,
      },
    ])
    createBotMock.mockResolvedValueOnce({
      id: 'bot-2',
      name: '商品 CTA 一号',
      strategy: '商品 CTA',
      strategyId: 'strategy-2',
      strategyName: '商品 CTA',
      integrationId: 'integration-2',
      integrationDisplayName: '港股账户',
      status: 'active',
      profit: 0,
      totalReturnRate: 0,
      runtime: '0h',
      capital: 50000,
      tags: ['港股账户'],
      paper: false,
      createdAt: '2026-04-18T11:00:00+08:00',
      lastErrorMessage: null,
    })
    updateBotStatusMock.mockResolvedValueOnce({ id: 'bot-2', status: 'paused' })

    const store = useBotsStore()
    await store.loadBots()
    await store.createBot({
      name: '商品 CTA 一号',
      strategyId: 'strategy-2',
      integrationId: 'integration-2',
      capital: 50000,
    })
    await store.pauseBot('bot-2')

    expect(store.items).toHaveLength(2)
    expect(store.items[0]?.status).toBe('paused')
    expect(store.recent[0]?.name).toBe('商品 CTA 一号')
  })

  it('loads positions and performance caches', async () => {
    fetchBotPositionsMock.mockResolvedValueOnce([
      { symbol: 'AU2406', quantity: '6.0000', avgCost: '500.0000', marketValue: '3120.0000', realizedPnl: '80.0000' },
    ])
    fetchBotPerformanceMock.mockResolvedValueOnce({
      summary: {
        latestEquity: 108000,
        totalProfit: 8000,
        totalReturnRate: 0.08,
      },
      equityCurve: [],
      orders: [],
    })

    const store = useBotsStore()
    store.items = [
      {
        id: 'bot-1',
        name: 'CTA',
        strategy: 'CTA',
        strategyId: 'strategy-1',
        strategyName: 'CTA',
        integrationId: 'integration-1',
        integrationDisplayName: '主账户',
        status: 'active',
        profit: 0,
        totalReturnRate: 0,
        runtime: '0h',
        capital: 100000,
        tags: [],
        paper: false,
        createdAt: null,
        lastErrorMessage: null,
      },
    ]

    const positions = await store.loadPositions('bot-1')
    const performance = await store.loadPerformance('bot-1')

    expect(positions[0]?.symbol).toBe('AU2406')
    expect(performance.summary.totalProfit).toBe(8000)
    expect(store.items[0]?.profit).toBe(8000)
  })
})

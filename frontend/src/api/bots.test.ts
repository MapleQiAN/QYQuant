import { beforeEach, describe, expect, it, vi } from 'vitest'

const { requestMock } = vi.hoisted(() => ({
  requestMock: vi.fn(),
}))

vi.mock('./http', () => ({
  createHttpClient: () => ({
    request: requestMock,
    requestWithMeta: requestMock,
  }),
}))

import { createBot, fetchBotPerformance, fetchBotPositions, fetchBots, fetchRecent, updateBotStatus } from './bots'

describe('bots api', () => {
  beforeEach(() => {
    requestMock.mockReset()
  })

  it('loads recent bots', async () => {
    requestMock.mockResolvedValueOnce([
      {
        id: 'bot-1',
        name: '沪深择时一号',
        strategy: '沪深择时',
        status: 'active',
        profit: 3200,
        runtime: '2d 4h',
        capital: 100000,
        tags: ['主账户', 'xtquant'],
      },
    ])

    const data = await fetchRecent()

    expect(data[0]?.name).toBe('沪深择时一号')
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/bots/recent',
    })
  })

  it('creates and normalizes managed bot', async () => {
    requestMock.mockResolvedValueOnce({
      id: 'bot-2',
      name: '商品 CTA 一号',
      strategy: '商品 CTA',
      strategy_id: 'strategy-2',
      strategy_name: '商品 CTA',
      integration_id: 'integration-1',
      integration_display_name: '主账户',
      status: 'active',
      profit: 0,
      total_return_rate: 0,
      runtime: '0h',
      capital: 50000,
      tags: ['主账户', 'xtquant'],
      paper: false,
      created_at: '2026-04-18T10:00:00+08:00',
      last_error_message: null,
    })

    const bot = await createBot({
      name: '商品 CTA 一号',
      strategyId: 'strategy-2',
      integrationId: 'integration-1',
      capital: 50000,
    })

    expect(bot.integrationDisplayName).toBe('主账户')
    expect(bot.paper).toBe(false)
    expect(requestMock).toHaveBeenCalledWith({
      method: 'post',
      url: '/bots',
      data: {
        name: '商品 CTA 一号',
        strategy_id: 'strategy-2',
        integration_id: 'integration-1',
        capital: 50000,
      },
    })
  })

  it('loads detail endpoints', async () => {
    requestMock
      .mockResolvedValueOnce([
        {
          id: 'bot-3',
          name: 'CTA',
          strategy: 'CTA',
          strategy_id: 'strategy-3',
          strategy_name: 'CTA',
          integration_id: 'integration-2',
          integration_display_name: '港股账户',
          status: 'paused',
          profit: 1200,
          total_return_rate: 0.012,
          runtime: '1d 3h',
          capital: 100000,
          tags: [],
          paper: false,
          created_at: '2026-04-18T10:00:00+08:00',
          last_error_message: null,
        },
      ])
      .mockResolvedValueOnce([
        {
          symbol: 'AU2406',
          quantity: '6.0000',
          avg_cost: '500.0000',
          market_value: '3120.0000',
          realized_pnl: '80.0000',
        },
      ])
      .mockResolvedValueOnce({
        summary: {
          latest_equity: 108000,
          total_profit: 8000,
          total_return_rate: 0.08,
        },
        equity_curve: [
          {
            snapshot_date: '2026-04-17',
            equity: 108000,
            available_cash: 38000,
            position_value: 70000,
            total_profit: 8000,
            total_return_rate: 0.08,
          },
        ],
        orders: [
          {
            id: 'order-1',
            symbol: 'AU2406',
            side: 'buy',
            price: 500,
            quantity: 10,
            status: 'filled',
            pnl: null,
            timestamp: 1713436800000,
            client_order_id: 'managed-order-1',
          },
        ],
      })
      .mockResolvedValueOnce({ id: 'bot-3', status: 'active' })

    const bots = await fetchBots()
    const positions = await fetchBotPositions('bot-3')
    const performance = await fetchBotPerformance('bot-3')
    const status = await updateBotStatus('bot-3', 'active')

    expect(bots[0]?.integrationDisplayName).toBe('港股账户')
    expect(positions[0]?.avgCost).toBe('500.0000')
    expect(performance.summary.totalProfit).toBe(8000)
    expect(performance.orders[0]?.clientOrderId).toBe('managed-order-1')
    expect(status.status).toBe('active')
  })
})

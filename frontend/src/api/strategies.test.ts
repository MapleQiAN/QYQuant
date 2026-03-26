import { beforeEach, describe, it, expect, vi } from 'vitest'
import * as strategies from './strategies'

const { requestMock, requestWithMetaMock } = vi.hoisted(() => ({
  requestMock: vi.fn().mockResolvedValue({ ok: true }),
  requestWithMetaMock: vi.fn().mockResolvedValue({
    data: [],
    meta: { total: 0, page: 1, page_size: 20 }
  })
}))

vi.mock('./http', () => ({
  createHttpClient: () => ({ request: requestMock, requestWithMeta: requestWithMetaMock }),
}))

describe('strategies api', () => {
  beforeEach(() => {
    requestMock.mockClear()
    requestWithMetaMock.mockClear()
  })

  it('calls strategy library endpoint', async () => {
    const data = await strategies.fetchStrategies({ page: 2, perPage: 10 })
    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/strategies/',
      params: { page: 2, per_page: 10 }
    })
  })

  it('calls delete strategy endpoint', async () => {
    const data = await strategies.deleteStrategy('strategy-id')
    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'delete',
      url: '/v1/strategies/strategy-id'
    })
  })

  it('calls import strategy endpoint', async () => {
    const file = new File(['package'], 'demo.qys', { type: 'application/octet-stream' })
    const data = await strategies.importStrategy(file)
    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledTimes(1)
    expect(requestMock.mock.calls[0][0].method).toBe('post')
    expect(requestMock.mock.calls[0][0].url).toBe('/v1/strategies/import')
  })

  it('calls runtime descriptor endpoint', async () => {
    const data = await strategies.fetchRuntimeDescriptor('strategy-id')
    expect(data).toEqual({ ok: true })
  })

  it('calls strategy parameters endpoint', async () => {
    const data = await strategies.fetchStrategyParameters('strategy-id')
    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/strategies/strategy-id/parameters'
    })
  })

  it('calls strategy presets endpoints', async () => {
    await strategies.fetchStrategyPresets('strategy-id')
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/strategies/strategy-id/presets'
    })

    await strategies.createStrategyPreset('strategy-id', {
      name: '稳健版',
      parameters: { window: 20 }
    })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'post',
      url: '/v1/strategies/strategy-id/presets',
      data: {
        name: '稳健版',
        parameters: { window: 20 }
      }
    })

    await strategies.updateStrategyPreset('strategy-id', 'preset-id', {
      name: '激进版',
      parameters: { window: 10 }
    })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'put',
      url: '/v1/strategies/strategy-id/presets/preset-id',
      data: {
        name: '激进版',
        parameters: { window: 10 }
      }
    })

    await strategies.deleteStrategyPreset('strategy-id', 'preset-id')
    expect(requestMock).toHaveBeenCalledWith({
      method: 'delete',
      url: '/v1/strategies/strategy-id/presets/preset-id'
    })
  })

  it('normalizes marketplace envelope and field names', async () => {
    requestWithMetaMock.mockResolvedValueOnce({
      data: [
        {
          id: 'market-1',
          title: 'Gold Prime',
          name: 'gold-prime',
          description: 'desc',
          category: 'momentum',
          tags: ['gold'],
          is_verified: true,
          display_metrics: {
            annualized_return: 18.2,
            max_drawdown: -7.3,
            sharpe_ratio: 1.44
          },
          author: {
            nickname: 'Market Author',
            avatar_url: 'https://example.com/a.png'
          }
        }
      ],
      meta: {
        total: 24,
        page: 2,
        page_size: 20
      }
    })

    const result = await strategies.fetchMarketplaceStrategies({ page: 2, pageSize: 20 })

    expect(requestWithMetaMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/marketplace/strategies',
      params: {
        page: 2,
        page_size: 20,
        featured: undefined
      }
    })
    expect(result.meta.pageSize).toBe(20)
    expect(result.data[0].isVerified).toBe(true)
    expect(result.data[0].displayMetrics).toEqual({
      annualized_return: 18.2,
      max_drawdown: -7.3,
      sharpe_ratio: 1.44
    })
    expect(result.data[0].author.avatarUrl).toBe('https://example.com/a.png')
  })

  it('forwards marketplace search and filter params', async () => {
    await strategies.fetchMarketplaceStrategies({
      page: 3,
      pageSize: 10,
      q: '均线',
      category: 'trend-following',
      verified: true,
      annualReturnGte: 20,
      maxDrawdownLte: 10
    })

    expect(requestWithMetaMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/marketplace/strategies',
      params: {
        page: 3,
        page_size: 10,
        featured: undefined,
        q: '均线',
        category: 'trend-following',
        verified: true,
        annual_return_gte: 20,
        max_drawdown_lte: 10
      }
    })
  })

  it('calls marketplace import endpoint', async () => {
    const data = await strategies.importMarketplaceStrategy('strategy-id')

    expect(data).toEqual({ strategyId: '', redirectTo: '' })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'post',
      url: '/v1/marketplace/strategies/strategy-id/import'
    })
  })

  it('calls marketplace import status endpoint', async () => {
    const data = await strategies.fetchMarketplaceStrategyImportStatus('strategy-id')

    expect(data).toEqual({ imported: false, userStrategyId: null })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/marketplace/strategies/strategy-id/import-status'
    })
  })

  it('calls marketplace publish endpoint', async () => {
    const data = await strategies.publishMarketplaceStrategy({
      strategyId: 'strategy-id',
      title: '均线趋势增强版',
      description: 'desc',
      tags: ['均线', '趋势'],
      category: 'trend-following',
      displayMetrics: {
        sharpe_ratio: 1.45,
        max_drawdown: -9.2,
        total_return: 28.4
      }
    })

    expect(data).toEqual({ strategyId: '', reviewStatus: 'draft' })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'post',
      url: '/v1/marketplace/strategies',
      data: {
        strategy_id: 'strategy-id',
        title: '均线趋势增强版',
        description: 'desc',
        tags: ['均线', '趋势'],
        category: 'trend-following',
        display_metrics: {
          sharpe_ratio: 1.45,
          max_drawdown: -9.2,
          total_return: 28.4
        }
      }
    })
  })

  it('calls marketplace publish status endpoint', async () => {
    const data = await strategies.fetchMarketplacePublishStatus('strategy-id')

    expect(data).toEqual({ reviewStatus: 'draft', isPublic: false })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/marketplace/strategies/strategy-id/publish-status'
    })
  })

  it('calls marketplace report endpoint', async () => {
    const data = await strategies.reportMarketplaceStrategy('strategy-id', 'misleading claim in description')

    expect(data).toEqual({ reportId: '' })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'post',
      url: '/v1/marketplace/strategies/strategy-id/report',
      data: {
        reason: 'misleading claim in description'
      }
    })
  })
})


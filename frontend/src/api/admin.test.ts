import { beforeEach, describe, expect, it, vi } from 'vitest'

const { requestMock, requestWithMetaMock } = vi.hoisted(() => ({
  requestMock: vi.fn(),
  requestWithMetaMock: vi.fn()
}))

vi.mock('./http', () => ({
  createHttpClient: () => ({
    request: requestMock,
    requestWithMeta: requestWithMetaMock
  })
}))

import { fetchAdminHealth, fetchPendingStrategyReviews, submitStrategyReview } from './admin'

describe('admin api', () => {
  beforeEach(() => {
    requestMock.mockReset()
    requestWithMetaMock.mockReset()
  })

  it('calls admin health endpoint', async () => {
    requestMock.mockResolvedValueOnce({ status: 'ok', scope: 'admin' })

    const data = await fetchAdminHealth()

    expect(data).toEqual({ status: 'ok', scope: 'admin' })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/admin/health'
    })
  })

  it('calls pending strategy review queue endpoint', async () => {
    requestWithMetaMock.mockResolvedValueOnce({
      data: [],
      meta: { total: 0, page: 1, per_page: 20 }
    })

    const data = await fetchPendingStrategyReviews({ page: 2, perPage: 10 })

    expect(data).toEqual({
      data: [],
      meta: { total: 0, page: 1, perPage: 20 }
    })
    expect(requestWithMetaMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/admin/strategies',
      params: { review_status: 'pending', page: 2, per_page: 10 }
    })
  })

  it('calls strategy review mutation endpoint', async () => {
    requestMock.mockResolvedValueOnce({
      strategy_id: 'strategy-1',
      review_status: 'approved'
    })

    const data = await submitStrategyReview('strategy-1', { status: 'approved' })

    expect(data).toEqual({
      strategyId: 'strategy-1',
      reviewStatus: 'approved'
    })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'patch',
      url: '/v1/admin/strategies/strategy-1/review',
      data: { status: 'approved' }
    })
  })
})

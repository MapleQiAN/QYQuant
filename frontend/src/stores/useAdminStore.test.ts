import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

const {
  fetchAdminHealthMock,
  fetchPendingStrategyReviewsMock,
  submitStrategyReviewMock
} = vi.hoisted(() => ({
  fetchAdminHealthMock: vi.fn(),
  fetchPendingStrategyReviewsMock: vi.fn(),
  submitStrategyReviewMock: vi.fn()
}))

vi.mock('../api/admin', () => ({
  fetchAdminHealth: fetchAdminHealthMock,
  fetchPendingStrategyReviews: fetchPendingStrategyReviewsMock,
  submitStrategyReview: submitStrategyReviewMock
}))

import { useAdminStore } from './useAdminStore'

describe('admin store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    fetchAdminHealthMock.mockReset()
    fetchPendingStrategyReviewsMock.mockReset()
    submitStrategyReviewMock.mockReset()
  })

  it('loads admin health overview into state', async () => {
    fetchAdminHealthMock.mockResolvedValueOnce({ status: 'ok', scope: 'admin' })
    const store = useAdminStore()

    await store.loadOverview()

    expect(fetchAdminHealthMock).toHaveBeenCalledTimes(1)
    expect(store.overview).toEqual({ status: 'ok', scope: 'admin' })
    expect(store.loading).toBe(false)
  })

  it('loads pending strategy review queue into state', async () => {
    fetchPendingStrategyReviewsMock.mockResolvedValueOnce({
      data: [
        {
          id: 'strategy-1',
          title: '均线增强版',
          name: 'ma-pro',
          description: 'desc',
          category: 'trend-following',
          tags: ['均线'],
          displayMetrics: { sharpe_ratio: 1.2 },
          ownerId: 'user-1',
          authorNickname: 'Alice',
          createdAt: '2026-03-23T12:00:00+08:00',
          reviewStatus: 'pending'
        }
      ],
      meta: {
        total: 1,
        page: 1,
        perPage: 20
      }
    })

    const store = useAdminStore()
    await store.loadPendingReviews()

    expect(fetchPendingStrategyReviewsMock).toHaveBeenCalledWith({ page: 1, perPage: 20 })
    expect(store.reviewQueue).toHaveLength(1)
    expect(store.reviewQueueMeta).toEqual({ total: 1, page: 1, perPage: 20 })
    expect(store.reviewQueueLoading).toBe(false)
  })

  it('submits a review result and removes the handled item from the queue', async () => {
    fetchPendingStrategyReviewsMock.mockResolvedValueOnce({
      data: [
        {
          id: 'strategy-1',
          title: '均线增强版',
          name: 'ma-pro',
          description: 'desc',
          category: 'trend-following',
          tags: ['均线'],
          displayMetrics: { sharpe_ratio: 1.2 },
          ownerId: 'user-1',
          authorNickname: 'Alice',
          createdAt: '2026-03-23T12:00:00+08:00',
          reviewStatus: 'pending'
        }
      ],
      meta: {
        total: 1,
        page: 1,
        perPage: 20
      }
    })
    submitStrategyReviewMock.mockResolvedValueOnce({
      strategyId: 'strategy-1',
      reviewStatus: 'approved'
    })

    const store = useAdminStore()
    await store.loadPendingReviews()
    const result = await store.reviewStrategy('strategy-1', { status: 'approved' })

    expect(submitStrategyReviewMock).toHaveBeenCalledWith('strategy-1', { status: 'approved' })
    expect(result).toEqual({ strategyId: 'strategy-1', reviewStatus: 'approved' })
    expect(store.reviewQueue).toEqual([])
    expect(store.reviewQueueMeta.total).toBe(0)
    expect(store.reviewSubmitting['strategy-1']).toBe(false)
  })
})

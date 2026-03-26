import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

const {
  fetchAdminHealthMock,
  fetchQueueStatsMock,
  fetchPendingStrategyReviewsMock,
  submitStrategyReviewMock,
  fetchPendingReportsMock,
  resolveReportMock,
  terminateJobMock
} = vi.hoisted(() => ({
  fetchAdminHealthMock: vi.fn(),
  fetchQueueStatsMock: vi.fn(),
  fetchPendingStrategyReviewsMock: vi.fn(),
  submitStrategyReviewMock: vi.fn(),
  fetchPendingReportsMock: vi.fn(),
  resolveReportMock: vi.fn(),
  terminateJobMock: vi.fn()
}))

vi.mock('../api/admin', () => ({
  fetchAdminHealth: fetchAdminHealthMock,
  fetchQueueStats: fetchQueueStatsMock,
  fetchPendingStrategyReviews: fetchPendingStrategyReviewsMock,
  submitStrategyReview: submitStrategyReviewMock,
  fetchPendingReports: fetchPendingReportsMock,
  resolveReport: resolveReportMock,
  terminateJob: terminateJobMock
}))

import { useAdminStore } from './useAdminStore'

describe('admin store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    fetchAdminHealthMock.mockReset()
    fetchQueueStatsMock.mockReset()
    fetchPendingStrategyReviewsMock.mockReset()
    submitStrategyReviewMock.mockReset()
    fetchPendingReportsMock.mockReset()
    resolveReportMock.mockReset()
    terminateJobMock.mockReset()
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

  it('loads backtest queue stats into state', async () => {
    fetchQueueStatsMock.mockResolvedValueOnce({
      stats: {
        pending: 2,
        running: 1,
        avgDuration: 120,
        failureRate1h: 0.1
      },
      stuckJobs: [
        {
          jobId: 'job-1',
          userId: 'user-1',
          strategyId: 'strategy-1',
          strategyName: 'Alpha',
          startedAt: '2026-03-26T12:00:00+08:00',
          runningDurationSeconds: 900
        }
      ]
    })

    const store = useAdminStore()
    await store.loadQueueStats()

    expect(fetchQueueStatsMock).toHaveBeenCalledTimes(1)
    expect(store.queueStats).toEqual({
      pending: 2,
      running: 1,
      avgDuration: 120,
      failureRate1h: 0.1
    })
    expect(store.stuckJobs).toHaveLength(1)
    expect(store.queueStatsLoading).toBe(false)
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

  it('loads pending reports queue into state', async () => {
    fetchPendingReportsMock.mockResolvedValueOnce({
      data: [
        {
          id: 'report-1',
          reporterId: 'user-2',
          reporterNickname: 'Watcher',
          strategyId: 'strategy-1',
          strategyTitle: 'Alpha Strategy',
          strategyAuthorId: 'user-1',
          strategyAuthorNickname: 'Author',
          reason: 'misleading claim',
          status: 'pending',
          createdAt: '2026-03-26T12:00:00+08:00'
        }
      ],
      meta: {
        total: 1,
        page: 1,
        perPage: 20
      }
    })

    const store = useAdminStore()
    await store.loadPendingReports()

    expect(fetchPendingReportsMock).toHaveBeenCalledWith({ page: 1, perPage: 20 })
    expect(store.reportQueue).toHaveLength(1)
    expect(store.reportQueueMeta).toEqual({ total: 1, page: 1, perPage: 20 })
    expect(store.reportQueueLoading).toBe(false)
  })

  it('resolves a report and removes it from the report queue', async () => {
    fetchPendingReportsMock.mockResolvedValueOnce({
      data: [
        {
          id: 'report-1',
          reporterId: 'user-2',
          reporterNickname: 'Watcher',
          strategyId: 'strategy-1',
          strategyTitle: 'Alpha Strategy',
          strategyAuthorId: 'user-1',
          strategyAuthorNickname: 'Author',
          reason: 'misleading claim',
          status: 'pending',
          createdAt: '2026-03-26T12:00:00+08:00'
        }
      ],
      meta: {
        total: 1,
        page: 1,
        perPage: 20
      }
    })
    resolveReportMock.mockResolvedValueOnce({
      reportId: 'report-1',
      status: 'reviewed',
      action: 'takedown'
    })

    const store = useAdminStore()
    await store.loadPendingReports()
    const result = await store.resolveReport('report-1', { action: 'takedown', adminNote: 'compliance issue' })

    expect(resolveReportMock).toHaveBeenCalledWith('report-1', {
      action: 'takedown',
      adminNote: 'compliance issue'
    })
    expect(result).toEqual({ reportId: 'report-1', status: 'reviewed', action: 'takedown' })
    expect(store.reportQueue).toEqual([])
    expect(store.reportQueueMeta.total).toBe(0)
    expect(store.reportResolving['report-1']).toBe(false)
  })

  it('terminates a stuck backtest job and removes it from monitor state', async () => {
    fetchQueueStatsMock.mockResolvedValueOnce({
      stats: {
        pending: 1,
        running: 2,
        avgDuration: 180,
        failureRate1h: 0.2
      },
      stuckJobs: [
        {
          jobId: 'job-1',
          userId: 'user-1',
          strategyId: 'strategy-1',
          strategyName: 'Alpha',
          startedAt: '2026-03-26T12:00:00+08:00',
          runningDurationSeconds: 901
        }
      ]
    })
    terminateJobMock.mockResolvedValueOnce({
      jobId: 'job-1',
      status: 'terminated'
    })

    const store = useAdminStore()
    await store.loadQueueStats()
    const result = await store.terminateJob('job-1', 'manual stop')

    expect(terminateJobMock).toHaveBeenCalledWith('job-1', 'manual stop')
    expect(result).toEqual({ jobId: 'job-1', status: 'terminated' })
    expect(store.stuckJobs).toEqual([])
    expect(store.queueStats.running).toBe(1)
    expect(store.terminatingJobs['job-1']).toBe(false)
  })
})

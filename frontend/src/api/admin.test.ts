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

import {
  fetchAdminHealth,
  fetchQueueStats,
  fetchPendingReports,
  fetchPendingStrategyReviews,
  resolveReport,
  terminateJob,
  submitStrategyReview,
} from './admin'

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

  it('calls pending reports queue endpoint', async () => {
    requestWithMetaMock.mockResolvedValueOnce({
      data: [],
      meta: { total: 0, page: 1, per_page: 20 }
    })

    const data = await fetchPendingReports({ page: 3, perPage: 5 })

    expect(data).toEqual({
      data: [],
      meta: { total: 0, page: 1, perPage: 20 }
    })
    expect(requestWithMetaMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/admin/reports',
      params: { status: 'pending', page: 3, per_page: 5 }
    })
  })

  it('calls report resolution mutation endpoint', async () => {
    requestMock.mockResolvedValueOnce({
      report_id: 'report-1',
      status: 'reviewed',
      action: 'takedown'
    })

    const data = await resolveReport('report-1', { action: 'takedown', adminNote: 'compliance issue' })

    expect(data).toEqual({
      reportId: 'report-1',
      status: 'reviewed',
      action: 'takedown'
    })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'patch',
      url: '/v1/admin/reports/report-1/resolve',
      data: { action: 'takedown', admin_note: 'compliance issue' }
    })
  })

  it('calls backtest queue stats endpoint', async () => {
    requestMock.mockResolvedValueOnce({
      stats: {
        pending: 3,
        running: 2,
        avg_duration: 180,
        failure_rate_1h: 0.25
      },
      stuck_jobs: [
        {
          job_id: 'job-1',
          user_id: 'user-1',
          strategy_id: 'strategy-1',
          strategy_name: 'Alpha',
          started_at: '2026-03-26T10:00:00+08:00',
          running_duration_seconds: 900
        }
      ]
    })

    const data = await fetchQueueStats()

    expect(data).toEqual({
      stats: {
        pending: 3,
        running: 2,
        avgDuration: 180,
        failureRate1h: 0.25
      },
      stuckJobs: [
        {
          jobId: 'job-1',
          userId: 'user-1',
          strategyId: 'strategy-1',
          strategyName: 'Alpha',
          startedAt: '2026-03-26T10:00:00+08:00',
          runningDurationSeconds: 900
        }
      ]
    })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/admin/backtest/queue-stats'
    })
  })

  it('calls backtest job termination endpoint', async () => {
    requestMock.mockResolvedValueOnce({
      job_id: 'job-1',
      status: 'terminated'
    })

    const data = await terminateJob('job-1', 'manual stop')

    expect(data).toEqual({
      jobId: 'job-1',
      status: 'terminated'
    })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'delete',
      url: '/v1/admin/backtest/job-1',
      data: { admin_note: 'manual stop' }
    })
  })
})

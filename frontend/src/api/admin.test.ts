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
  fetchAuditLogs,
  fetchDataSourceHealth,
  fetchQueueStats,
  fetchUsers,
  fetchPendingReports,
  fetchPendingStrategyReviews,
  fetchStrategyReviewPacket,
  resolveReport,
  terminateJob,
  submitStrategyReview,
  updateUserBanStatus,
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

  it('calls data source health endpoint', async () => {
    requestMock.mockResolvedValueOnce({
      source_name: 'jqdata',
      status: 'unhealthy',
      status_label: '异常',
      status_color: 'red',
      last_checked_at: '2026-03-27T09:00:00+08:00',
      last_success_at: '2026-03-27T08:30:00+08:00',
      last_failure_at: '2026-03-27T09:00:00+08:00',
      last_error_message: 'request timed out',
      consecutive_failures: 2
    })

    const data = await fetchDataSourceHealth()

    expect(data).toEqual({
      sourceName: 'jqdata',
      status: 'unhealthy',
      statusLabel: '异常',
      statusColor: 'red',
      lastCheckedAt: '2026-03-27T09:00:00+08:00',
      lastSuccessAt: '2026-03-27T08:30:00+08:00',
      lastFailureAt: '2026-03-27T09:00:00+08:00',
      lastErrorMessage: 'request timed out',
      consecutiveFailures: 2
    })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/admin/data-source-health'
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

  it('calls strategy review packet endpoint', async () => {
    requestMock.mockResolvedValueOnce({
      strategy: {
        id: 'strategy-1',
        title: '均线增强版',
        name: 'ma-pro',
        description: 'desc',
        category: 'trend-following',
        tags: ['均线'],
        display_metrics: { sharpe_ratio: 1.2 },
        owner_id: 'user-1',
        author_nickname: 'Alice',
        created_at: '2026-03-23T12:00:00+08:00',
        review_status: 'pending'
      },
      version: {
        version: '1.0.0',
        file_id: 'file-1',
        filename: 'ma-pro.qys',
        checksum: 'abc123',
        checksum_valid: true
      },
      latest_backtest: {
        id: 'job-1',
        status: 'completed',
        params: { symbol: 'BTCUSDT' },
        result_summary: { total_return: 24.6 },
        result_storage_key: 'backtests/job-1'
      },
      checks: {
        has_version: true,
        has_package_file: true,
        checksum_valid: true,
        has_completed_backtest: true
      }
    })

    const data = await fetchStrategyReviewPacket('strategy-1')

    expect(data.version?.filename).toBe('ma-pro.qys')
    expect(data.latestBacktest?.resultSummary).toEqual({ total_return: 24.6 })
    expect(data.checks).toEqual({
      hasVersion: true,
      hasPackageFile: true,
      checksumValid: true,
      hasCompletedBacktest: true
    })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/admin/strategies/strategy-1/review-packet'
    })
  })

  it('calls admin users list endpoint', async () => {
    requestWithMetaMock.mockResolvedValueOnce({
      data: [
        {
          user_id: 'user-1',
          nickname: 'Alice',
          phone: '138****8000',
          created_at: '2026-03-26T12:00:00+08:00',
          plan_level: 'pro',
          is_banned: true
        }
      ],
      meta: { total: 1, page: 2, per_page: 10 }
    })

    const data = await fetchUsers({ search: 'Alice', page: 2, perPage: 10 })

    expect(data).toEqual({
      data: [
        {
          userId: 'user-1',
          nickname: 'Alice',
          phone: '138****8000',
          createdAt: '2026-03-26T12:00:00+08:00',
          planLevel: 'pro',
          isBanned: true
        }
      ],
      meta: { total: 1, page: 2, perPage: 10 }
    })
    expect(requestWithMetaMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/admin/users',
      params: { search: 'Alice', page: 2, per_page: 10 }
    })
  })

  it('calls admin user ban mutation endpoint', async () => {
    requestMock.mockResolvedValueOnce({
      user_id: 'user-1',
      is_banned: false
    })

    const data = await updateUserBanStatus('user-1', { isBanned: false })

    expect(data).toEqual({
      userId: 'user-1',
      isBanned: false
    })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'patch',
      url: '/v1/admin/users/user-1',
      data: {
        is_banned: false,
        ban_reason: undefined
      }
    })
  })

  it('calls admin audit logs endpoint', async () => {
    requestWithMetaMock.mockResolvedValueOnce({
      data: [
        {
          id: 'audit-1',
          operator_id: 'admin-1',
          operator_nickname: 'Root',
          action: 'user_ban',
          target_type: 'user',
          target_id: 'user-1',
          details: { ban_reason: 'spam' },
          created_at: '2026-03-26T12:30:00+08:00'
        }
      ],
      meta: { total: 1, page: 1, per_page: 20 }
    })

    const data = await fetchAuditLogs({
      operatorId: 'admin-1',
      action: 'user_ban',
      targetType: 'user',
      targetId: 'user-1'
    })

    expect(data).toEqual({
      data: [
        {
          id: 'audit-1',
          operatorId: 'admin-1',
          operatorNickname: 'Root',
          action: 'user_ban',
          targetType: 'user',
          targetId: 'user-1',
          details: { ban_reason: 'spam' },
          createdAt: '2026-03-26T12:30:00+08:00'
        }
      ],
      meta: { total: 1, page: 1, perPage: 20 }
    })
    expect(requestWithMetaMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/admin/audit-logs',
      params: {
        operator_id: 'admin-1',
        action: 'user_ban',
        target_type: 'user',
        target_id: 'user-1',
        date_from: undefined,
        date_to: undefined,
        page: 1,
        per_page: 20
      }
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

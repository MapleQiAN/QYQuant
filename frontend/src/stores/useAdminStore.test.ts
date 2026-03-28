import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

const {
  fetchAdminHealthMock,
  fetchAuditLogsMock,
  fetchDataSourceHealthMock,
  fetchQueueStatsMock,
  fetchUsersMock,
  fetchPendingStrategyReviewsMock,
  submitStrategyReviewMock,
  fetchPendingReportsMock,
  resolveReportMock,
  terminateJobMock,
  updateUserBanStatusMock
} = vi.hoisted(() => ({
  fetchAdminHealthMock: vi.fn(),
  fetchAuditLogsMock: vi.fn(),
  fetchDataSourceHealthMock: vi.fn(),
  fetchQueueStatsMock: vi.fn(),
  fetchUsersMock: vi.fn(),
  fetchPendingStrategyReviewsMock: vi.fn(),
  submitStrategyReviewMock: vi.fn(),
  fetchPendingReportsMock: vi.fn(),
  resolveReportMock: vi.fn(),
  terminateJobMock: vi.fn(),
  updateUserBanStatusMock: vi.fn()
}))

vi.mock('../api/admin', () => ({
  fetchAdminHealth: fetchAdminHealthMock,
  fetchAuditLogs: fetchAuditLogsMock,
  fetchDataSourceHealth: fetchDataSourceHealthMock,
  fetchQueueStats: fetchQueueStatsMock,
  fetchUsers: fetchUsersMock,
  fetchPendingStrategyReviews: fetchPendingStrategyReviewsMock,
  submitStrategyReview: submitStrategyReviewMock,
  fetchPendingReports: fetchPendingReportsMock,
  resolveReport: resolveReportMock,
  terminateJob: terminateJobMock,
  updateUserBanStatus: updateUserBanStatusMock
}))

import { useAdminStore } from './useAdminStore'

describe('admin store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    fetchAdminHealthMock.mockReset()
    fetchAuditLogsMock.mockReset()
    fetchDataSourceHealthMock.mockReset()
    fetchQueueStatsMock.mockReset()
    fetchUsersMock.mockReset()
    fetchPendingStrategyReviewsMock.mockReset()
    submitStrategyReviewMock.mockReset()
    fetchPendingReportsMock.mockReset()
    resolveReportMock.mockReset()
    terminateJobMock.mockReset()
    updateUserBanStatusMock.mockReset()
  })

  it('loads admin health overview into state', async () => {
    fetchAdminHealthMock.mockResolvedValueOnce({ status: 'ok', scope: 'admin' })
    const store = useAdminStore()

    await store.loadOverview()

    expect(fetchAdminHealthMock).toHaveBeenCalledTimes(1)
    expect(store.overview).toEqual({ status: 'ok', scope: 'admin' })
    expect(store.loading).toBe(false)
  })

  it('loads data source health into state', async () => {
    fetchDataSourceHealthMock.mockResolvedValueOnce({
      sourceName: 'jqdata',
      status: 'healthy',
      statusLabel: '正常',
      statusColor: 'green',
      lastCheckedAt: '2026-03-27T09:05:00+08:00',
      lastSuccessAt: '2026-03-27T09:05:00+08:00',
      lastFailureAt: null,
      lastErrorMessage: null,
      consecutiveFailures: 0
    })

    const store = useAdminStore()
    await store.loadDataSourceHealth()

    expect(fetchDataSourceHealthMock).toHaveBeenCalledTimes(1)
    expect(store.dataSourceHealth).toEqual({
      sourceName: 'jqdata',
      status: 'healthy',
      statusLabel: '正常',
      statusColor: 'green',
      lastCheckedAt: '2026-03-27T09:05:00+08:00',
      lastSuccessAt: '2026-03-27T09:05:00+08:00',
      lastFailureAt: null,
      lastErrorMessage: null,
      consecutiveFailures: 0
    })
    expect(store.dataSourceHealthLoading).toBe(false)
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

  it('loads admin users into state', async () => {
    fetchUsersMock.mockResolvedValueOnce({
      data: [
        {
          userId: 'user-1',
          nickname: 'Alice',
          phone: '138****8000',
          createdAt: '2026-03-26T12:00:00+08:00',
          planLevel: 'pro',
          isBanned: false
        }
      ],
      meta: {
        total: 1,
        page: 2,
        perPage: 10
      }
    })

    const store = useAdminStore()
    await store.loadUsers({ search: 'Alice', page: 2, perPage: 10 })

    expect(fetchUsersMock).toHaveBeenCalledWith({ search: 'Alice', page: 2, perPage: 10 })
    expect(store.users).toHaveLength(1)
    expect(store.usersMeta).toEqual({ total: 1, page: 2, perPage: 10 })
    expect(store.userListLoading).toBe(false)
  })

  it('bans a user and updates local state', async () => {
    fetchUsersMock.mockResolvedValueOnce({
      data: [
        {
          userId: 'user-1',
          nickname: 'Alice',
          phone: '138****8000',
          createdAt: '2026-03-26T12:00:00+08:00',
          planLevel: 'pro',
          isBanned: false
        }
      ],
      meta: {
        total: 1,
        page: 1,
        perPage: 20
      }
    })
    updateUserBanStatusMock.mockResolvedValueOnce({
      userId: 'user-1',
      isBanned: true
    })

    const store = useAdminStore()
    await store.loadUsers()
    const result = await store.banUser('user-1', 'spam')

    expect(updateUserBanStatusMock).toHaveBeenCalledWith('user-1', {
      isBanned: true,
      banReason: 'spam'
    })
    expect(result).toEqual({ userId: 'user-1', isBanned: true })
    expect(store.users[0]?.isBanned).toBe(true)
    expect(store.banningUsers['user-1']).toBe(false)
  })

  it('unbans a user and updates local state', async () => {
    fetchUsersMock.mockResolvedValueOnce({
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
      meta: {
        total: 1,
        page: 1,
        perPage: 20
      }
    })
    updateUserBanStatusMock.mockResolvedValueOnce({
      userId: 'user-1',
      isBanned: false
    })

    const store = useAdminStore()
    await store.loadUsers()
    const result = await store.unbanUser('user-1')

    expect(updateUserBanStatusMock).toHaveBeenCalledWith('user-1', {
      isBanned: false,
      banReason: undefined
    })
    expect(result).toEqual({ userId: 'user-1', isBanned: false })
    expect(store.users[0]?.isBanned).toBe(false)
    expect(store.banningUsers['user-1']).toBe(false)
  })

  it('loads audit logs into state', async () => {
    fetchAuditLogsMock.mockResolvedValueOnce({
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
      meta: {
        total: 1,
        page: 1,
        perPage: 20
      }
    })

    const store = useAdminStore()
    await store.loadAuditLogs({ action: 'user_ban' })

    expect(fetchAuditLogsMock).toHaveBeenCalledWith({ action: 'user_ban', page: 1, perPage: 20 })
    expect(store.auditLogs).toHaveLength(1)
    expect(store.auditLogsMeta).toEqual({ total: 1, page: 1, perPage: 20 })
    expect(store.auditLogsLoading).toBe(false)
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

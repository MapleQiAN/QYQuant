import { defineStore } from 'pinia'
import {
  fetchAdminHealth,
  fetchPendingReports,
  fetchPendingStrategyReviews,
  fetchQueueStats,
  resolveReport,
  submitStrategyReview,
  terminateJob,
  type AdminHealthResponse,
  type AdminQueueStats,
  type AdminReport,
  type AdminResolveReportPayload,
  type AdminResolveReportResult,
  type AdminReviewMutationPayload,
  type AdminReviewMutationResult,
  type AdminReviewStrategy,
  type AdminStuckJob,
  type AdminTerminateJobResult
} from '../api/admin'

const emptyQueueStats = (): AdminQueueStats => ({
  pending: 0,
  running: 0,
  avgDuration: 0,
  failureRate1h: 0
})

export const useAdminStore = defineStore('admin', {
  state: () => ({
    overview: null as AdminHealthResponse | null,
    loading: false,
    queueStats: emptyQueueStats() as AdminQueueStats,
    stuckJobs: [] as AdminStuckJob[],
    queueStatsLoading: false,
    terminatingJobs: {} as Record<string, boolean>,
    reviewQueue: [] as AdminReviewStrategy[],
    reviewQueueLoading: false,
    reviewQueueMeta: {
      total: 0,
      page: 1,
      perPage: 20
    },
    reviewSubmitting: {} as Record<string, boolean>,
    reportQueue: [] as AdminReport[],
    reportQueueLoading: false,
    reportQueueMeta: {
      total: 0,
      page: 1,
      perPage: 20
    },
    reportResolving: {} as Record<string, boolean>
  }),
  actions: {
    async loadOverview() {
      this.loading = true
      try {
        this.overview = await fetchAdminHealth()
      } finally {
        this.loading = false
      }
    },
    async loadQueueStats() {
      this.queueStatsLoading = true
      try {
        const response = await fetchQueueStats()
        this.queueStats = response.stats
        this.stuckJobs = response.stuckJobs
      } finally {
        this.queueStatsLoading = false
      }
    },
    async terminateJob(jobId: string, adminNote?: string): Promise<AdminTerminateJobResult> {
      this.terminatingJobs[jobId] = true
      try {
        const result = await terminateJob(jobId, adminNote)
        const hadJob = this.stuckJobs.some((item) => item.jobId === jobId)
        this.stuckJobs = this.stuckJobs.filter((item) => item.jobId !== jobId)
        if (hadJob) {
          this.queueStats = {
            ...this.queueStats,
            running: Math.max(0, this.queueStats.running - 1)
          }
        }
        return result
      } finally {
        this.terminatingJobs[jobId] = false
      }
    },
    async loadPendingReviews(page?: number) {
      this.reviewQueueLoading = true
      try {
        const currentPage = page ?? this.reviewQueueMeta.page
        const response = await fetchPendingStrategyReviews({
          page: currentPage,
          perPage: this.reviewQueueMeta.perPage
        })
        this.reviewQueue = response.data
        this.reviewQueueMeta = response.meta
      } finally {
        this.reviewQueueLoading = false
      }
    },
    async reviewStrategy(
      strategyId: string,
      payload: AdminReviewMutationPayload
    ): Promise<AdminReviewMutationResult> {
      this.reviewSubmitting[strategyId] = true
      try {
        const result = await submitStrategyReview(strategyId, payload)
        this.reviewQueue = this.reviewQueue.filter((item) => item.id !== strategyId)
        this.reviewQueueMeta = {
          ...this.reviewQueueMeta,
          total: Math.max(0, this.reviewQueueMeta.total - 1)
        }
        return result
      } finally {
        this.reviewSubmitting[strategyId] = false
      }
    },
    async loadPendingReports(page?: number) {
      this.reportQueueLoading = true
      try {
        const currentPage = page ?? this.reportQueueMeta.page
        const response = await fetchPendingReports({
          page: currentPage,
          perPage: this.reportQueueMeta.perPage
        })
        this.reportQueue = response.data
        this.reportQueueMeta = response.meta
      } finally {
        this.reportQueueLoading = false
      }
    },
    async resolveReport(
      reportId: string,
      payload: AdminResolveReportPayload
    ): Promise<AdminResolveReportResult> {
      this.reportResolving[reportId] = true
      try {
        const result = await resolveReport(reportId, payload)
        this.reportQueue = this.reportQueue.filter((item) => item.id !== reportId)
        this.reportQueueMeta = {
          ...this.reportQueueMeta,
          total: Math.max(0, this.reportQueueMeta.total - 1)
        }
        return result
      } finally {
        this.reportResolving[reportId] = false
      }
    }
  }
})

import { defineStore } from 'pinia'
import {
  fetchAdminHealth,
  fetchPendingStrategyReviews,
  submitStrategyReview,
  type AdminHealthResponse,
  type AdminReviewMutationPayload,
  type AdminReviewMutationResult,
  type AdminReviewStrategy
} from '../api/admin'

export const useAdminStore = defineStore('admin', {
  state: () => ({
    overview: null as AdminHealthResponse | null,
    loading: false,
    reviewQueue: [] as AdminReviewStrategy[],
    reviewQueueLoading: false,
    reviewQueueMeta: {
      total: 0,
      page: 1,
      perPage: 20
    },
    reviewSubmitting: {} as Record<string, boolean>
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
    async loadPendingReviews(page = this.reviewQueueMeta.page) {
      this.reviewQueueLoading = true
      try {
        const response = await fetchPendingStrategyReviews({
          page,
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
    }
  }
})

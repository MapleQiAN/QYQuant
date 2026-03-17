import { defineStore } from 'pinia'
import { fetchRecent, fetchStrategies } from '../api/strategies'
import type { Strategy } from '../types/Strategy'

export const useStrategiesStore = defineStore('strategies', {
  state: () => ({
    recent: [] as Strategy[],
    library: [] as Strategy[],
    pagination: {
      page: 1,
      perPage: 10,
      total: 0
    },
    loading: false,
    error: null as string | null
  }),
  actions: {
    async loadRecent() {
      this.loading = true
      this.error = null
      try {
        this.recent = await fetchRecent()
      } catch (error: any) {
        this.error = error?.message || 'Failed to load strategies'
      } finally {
        this.loading = false
      }
    },
    async loadLibrary(params?: { page?: number; perPage?: number }) {
      this.loading = true
      this.error = null
      try {
        const result = await fetchStrategies(params)
        this.library = result.items
        this.pagination = {
          page: result.page,
          perPage: result.perPage,
          total: result.total
        }
      } catch (error: any) {
        this.error = error?.message || 'Failed to load strategy library'
      } finally {
        this.loading = false
      }
    }
  }
})

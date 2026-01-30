import { defineStore } from 'pinia'
import { fetchRecent } from '../api/strategies'
import type { Strategy } from '../types/Strategy'

export const useStrategiesStore = defineStore('strategies', {
  state: () => ({
    recent: [] as Strategy[],
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
    }
  }
})

import { defineStore } from 'pinia'
import { fetchDashboardStats } from '../api/dashboard'
import type { DashboardStats } from '../api/dashboard'

export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    stats: null as DashboardStats | null,
    loading: false,
    error: null as string | null,
  }),
  actions: {
    async loadStats() {
      this.loading = true
      this.error = null
      try {
        this.stats = await fetchDashboardStats()
      } catch (error: any) {
        this.error = error?.message || 'Failed to load dashboard stats'
      } finally {
        this.loading = false
      }
    },
  },
})

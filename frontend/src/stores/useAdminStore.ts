import { defineStore } from 'pinia'
import { fetchAdminHealth, type AdminHealthResponse } from '../api/admin'

export const useAdminStore = defineStore('admin', {
  state: () => ({
    overview: null as AdminHealthResponse | null,
    loading: false,
  }),
  actions: {
    async loadOverview() {
      this.loading = true
      try {
        this.overview = await fetchAdminHealth()
      } finally {
        this.loading = false
      }
    }
  }
})

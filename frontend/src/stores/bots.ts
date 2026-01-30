import { defineStore } from 'pinia'
import { fetchRecent } from '../api/bots'
import type { Bot } from '../types/Bot'

export const useBotsStore = defineStore('bots', {
  state: () => ({
    recent: [] as Bot[],
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
        this.error = error?.message || 'Failed to load bots'
      } finally {
        this.loading = false
      }
    }
  }
})

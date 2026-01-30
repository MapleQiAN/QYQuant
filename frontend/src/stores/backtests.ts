import { defineStore } from 'pinia'
import { fetchLatest } from '../api/backtests'
import type { BacktestLatestResponse } from '../types/Backtest'

export const useBacktestsStore = defineStore('backtests', {
  state: () => ({
    latest: null as BacktestLatestResponse | null,
    loading: false,
    error: null as string | null
  }),
  actions: {
    async loadLatest() {
      this.loading = true
      this.error = null
      try {
        this.latest = await fetchLatest()
      } catch (error: any) {
        this.error = error?.message || 'Failed to load backtest'
      } finally {
        this.loading = false
      }
    }
  }
})

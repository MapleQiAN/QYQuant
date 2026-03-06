import { defineStore } from 'pinia'
import { fetchLatest } from '../api/backtests'
import type { BacktestLatestResponse } from '../types/Backtest'

interface LoadLatestOptions {
  interval?: string
  limit?: number
}

export const useBacktestsStore = defineStore('backtests', {
  state: () => ({
    latest: null as BacktestLatestResponse | null,
    loading: false,
    error: null as string | null
  }),
  actions: {
    async loadLatest(symbol?: string, options?: LoadLatestOptions) {
      this.loading = true
      this.error = null
      try {
        this.latest = await fetchLatest(symbol, options)
      } catch (error: any) {
        this.error = error?.message || 'Failed to load backtest'
      } finally {
        this.loading = false
      }
    }
  }
})

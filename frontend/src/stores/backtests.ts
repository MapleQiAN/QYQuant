import { defineStore } from 'pinia'
import { fetchBacktestReport, fetchLatest } from '../api/backtests'
import type { FetchLatestParams } from '../api/backtests'
import type { BacktestLatestResponse, BacktestReportResponse } from '../types/Backtest'

export const useBacktestsStore = defineStore('backtests', {
  state: () => ({
    latest: null as BacktestLatestResponse | null,
    report: null as BacktestReportResponse | null,
    loading: false,
    reportLoading: false,
    error: null as string | null,
    reportError: null as string | null
  }),
  actions: {
    async loadLatest(params: FetchLatestParams = {}) {
      this.loading = true
      this.error = null
      try {
        this.latest = await fetchLatest(params)
      } catch (error: any) {
        this.error = error?.message || 'Failed to load backtest'
      } finally {
        this.loading = false
      }
    },
    async loadReport(jobId: string) {
      this.reportLoading = true
      this.reportError = null
      try {
        this.report = await fetchBacktestReport(jobId)
      } catch (error: any) {
        this.reportError = error?.message || 'Failed to load backtest report'
      } finally {
        this.reportLoading = false
      }
    }
  }
})

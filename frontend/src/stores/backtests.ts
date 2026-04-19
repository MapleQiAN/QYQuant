import { defineStore } from 'pinia'
import { fetchBacktestReport, fetchLatest, fetchLatestCompletedReport, fetchSupportedPackages } from '../api/backtests'
import { fetchReport } from '../api/reports'
import type { FetchLatestParams } from '../api/backtests'
import type {
  BacktestAiReportResponse,
  BacktestLatestResponse,
  BacktestReportResponse,
  LatestCompletedReportResponse,
  SupportedPackage,
} from '../types/Backtest'

export const useBacktestsStore = defineStore('backtests', {
  state: () => ({
    latest: null as BacktestLatestResponse | null,
    latestReport: null as LatestCompletedReportResponse | null,
    report: null as BacktestReportResponse | null,
    legacyReport: null as BacktestReportResponse | null,
    aiReport: null as BacktestAiReportResponse | null,
    supportedPackages: [] as SupportedPackage[],
    loading: false,
    latestReportLoading: false,
    reportLoading: false,
    supportedPackagesLoading: false,
    error: null as string | null,
    latestReportError: null as string | null,
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
    async loadLatestReport() {
      this.latestReportLoading = true
      this.latestReportError = null
      try {
        this.latestReport = await fetchLatestCompletedReport()
      } catch (error: any) {
        this.latestReportError = error?.message || 'Failed to load latest report'
      } finally {
        this.latestReportLoading = false
      }
    },
    async loadReport(jobId: string) {
      this.reportLoading = true
      this.reportError = null
      try {
        const legacyReport = await fetchBacktestReport(jobId)
        this.report = legacyReport
        this.legacyReport = legacyReport

        if (legacyReport.report_id) {
          this.aiReport = await fetchReport(legacyReport.report_id)
        } else {
          this.aiReport = null
        }
      } catch (error: any) {
        this.legacyReport = null
        this.aiReport = null
        this.reportError = error?.message || 'Failed to load backtest report'
      } finally {
        this.reportLoading = false
      }
    },
    async loadSupportedPackages() {
      this.supportedPackagesLoading = true
      try {
        const response = await fetchSupportedPackages()
        this.supportedPackages = response.packages ?? []
      } finally {
        this.supportedPackagesLoading = false
      }
    }
  }
})

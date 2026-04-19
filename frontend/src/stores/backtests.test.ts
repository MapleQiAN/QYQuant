import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useBacktestsStore } from './backtests'

const { fetchLatestMock, fetchBacktestReportMock, fetchReportMock } = vi.hoisted(() => ({
  fetchLatestMock: vi.fn().mockResolvedValue({ summary: { totalReturn: 1 }, kline: [], trades: [] })
  ,
  fetchBacktestReportMock: vi.fn().mockResolvedValue({
    job_id: 'job-1',
    status: 'completed',
    result_summary: { totalReturn: 12.5, maxDrawdown: -3.2, sharpeRatio: 1.8 },
    equity_curve: [{ timestamp: 1700000000000, equity: 100000 }],
    trades: [],
    report_id: 'report-1',
    report_status: 'ready'
  }),
  fetchReportMock: vi.fn().mockResolvedValue({
    id: 'report-1',
    job_id: 'job-1',
    status: 'ready',
    payload: {
      metrics: { totalReturn: 12.5 },
      executive_summary: 'summary',
    },
  }),
}))

vi.mock('../api/backtests', () => ({
  fetchLatest: fetchLatestMock,
  fetchBacktestReport: fetchBacktestReportMock
}))

vi.mock('../api/reports', () => ({
  fetchReport: fetchReportMock,
}))

describe('backtests store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    fetchLatestMock.mockClear()
    fetchBacktestReportMock.mockClear()
    fetchReportMock.mockClear()
  })

  it('loads latest and clears error', async () => {
    const store = useBacktestsStore()
    await store.loadLatest()
    expect(store.error).toBeNull()
    expect(store.latest).not.toBeNull()
  })

  it('passes interval options when loading latest', async () => {
    const store = useBacktestsStore()
    await store.loadLatest({ symbol: 'XAUUSD', interval: '1h', limit: 200 })
    expect(fetchLatestMock).toHaveBeenCalledWith({ symbol: 'XAUUSD', interval: '1h', limit: 200 })
  })

  it('loads report and exposes it on state', async () => {
    const store = useBacktestsStore()
    await store.loadReport('job-1')

    expect(fetchBacktestReportMock).toHaveBeenCalledWith('job-1')
    expect(fetchReportMock).toHaveBeenCalledWith('report-1')
    expect(store.reportError).toBeNull()
    expect(store.report?.job_id).toBe('job-1')
    expect(store.legacyReport?.report_id).toBe('report-1')
    expect(store.aiReport?.id).toBe('report-1')
  })
})

import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as backtests from './backtests'

const { requestMock } = vi.hoisted(() => ({
  requestMock: vi.fn().mockResolvedValue({ ok: true })
}))

vi.mock('./http', () => ({
  createHttpClient: () => ({ request: requestMock })
}))

describe('backtests api', () => {
  beforeEach(() => {
    requestMock.mockClear()
  })

  it('calls latest endpoint', async () => {
    const data = await backtests.fetchLatest()
    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({ method: 'get', url: '/backtests/latest', params: undefined })
  })

  it('passes timeframe params to latest endpoint', async () => {
    await backtests.fetchLatest({ symbol: 'XAUUSD', interval: '1h', limit: 300 })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/backtests/latest',
      params: { symbol: 'XAUUSD', interval: '1h', limit: 300 }
    })
  })

  it('calls run endpoint', async () => {
    const data = await backtests.runBacktest({ symbol: 'BTCUSDT' })
    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'post',
      url: '/backtests/run',
      data: { symbol: 'BTCUSDT' }
    })
  })

  it('calls job endpoint', async () => {
    const data = await backtests.fetchBacktestJob('job-id')
    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({ method: 'get', url: '/backtests/job/job-id' })
  })

  it('submits v1 backtest jobs', async () => {
    const data = await backtests.submitBacktest({
      strategy_id: 'strategy-id',
      symbols: ['BTCUSDT'],
      start_date: '2024-01-01',
      end_date: '2024-01-31',
      data_source: 'binance'
    })

    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'post',
      url: '/v1/backtest/',
      data: {
        strategy_id: 'strategy-id',
        symbols: ['BTCUSDT'],
        start_date: '2024-01-01',
        end_date: '2024-01-31',
        data_source: 'binance'
      }
    })
  })

  it('fetches v1 backtest status', async () => {
    const data = await backtests.fetchBacktestStatus('job-id')

    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({ method: 'get', url: '/v1/backtest/job-id' })
  })

  it('fetches v1 backtest history', async () => {
    const data = await backtests.fetchBacktestHistory(25)

    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/backtest/history',
      params: { limit: 25 }
    })
  })

  it('fetches v1 backtest report', async () => {
    const data = await backtests.fetchBacktestReport('job-id')

    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({ method: 'get', url: '/v1/backtest/job-id/report' })
  })

  it('returns compatibility fields from legacy report bootstrap', async () => {
    requestMock.mockResolvedValueOnce({
      job_id: 'job-id',
      status: 'completed',
      report_id: 'report-1',
      report_status: 'ready',
    })

    const data = await backtests.fetchBacktestReport('job-id')

    expect(data.report_id).toBe('report-1')
    expect(data.report_status).toBe('ready')
  })

  it('fetches supported package whitelist', async () => {
    const data = await backtests.fetchSupportedPackages()

    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({ method: 'get', url: '/v1/backtest/supported-packages' })
  })

  it('deletes a single backtest job', async () => {
    const data = await backtests.deleteBacktestJob('job-123')

    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({ method: 'delete', url: '/v1/backtest/job-123' })
  })

  it('batch deletes backtests by status', async () => {
    const data = await backtests.batchDeleteBacktests('failed')

    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({ method: 'post', url: '/v1/backtest/batch-delete', data: { status: 'failed' } })
  })
})

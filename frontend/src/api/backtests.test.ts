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
    await backtests.fetchLatest('XAUUSD', { interval: '1h', limit: 300 })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/backtests/latest',
      params: { symbol: 'XAUUSD', interval: '1h', limit: 300 }
    })
  })

  it('calls run endpoint', async () => {
    const data = await backtests.runBacktest({ symbol: 'BTCUSDT' })
    expect(data).toEqual({ ok: true })
  })

  it('calls job endpoint', async () => {
    const data = await backtests.fetchBacktestJob('job-id')
    expect(data).toEqual({ ok: true })
  })
})

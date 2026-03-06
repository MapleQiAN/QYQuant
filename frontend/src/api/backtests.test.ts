import { describe, it, expect, vi } from 'vitest'
import * as backtests from './backtests'

vi.mock('./http', () => ({
  createHttpClient: () => ({ request: vi.fn().mockResolvedValue({ ok: true }) })
}))

describe('backtests api', () => {
  it('calls latest endpoint', async () => {
    const data = await backtests.fetchLatest()
    expect(data).toEqual({ ok: true })
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

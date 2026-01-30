import { createHttpClient } from './http'
import type { BacktestLatestResponse } from '../types/Backtest'

const client = createHttpClient()

export function fetchLatest(): Promise<BacktestLatestResponse> {
  return client.request({ method: 'get', url: '/backtests/latest' })
}

import { createHttpClient } from './http'
import type { BacktestLatestResponse } from '../types/Backtest'

const client = createHttpClient()

export function fetchLatest(symbol?: string): Promise<BacktestLatestResponse> {
  const params = symbol ? { symbol } : undefined
  return client.request({ method: 'get', url: '/backtests/latest', params })
}

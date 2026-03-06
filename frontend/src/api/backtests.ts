import { createHttpClient } from './http'
import type {
  BacktestJobResponse,
  BacktestLatestResponse,
  RunBacktestPayload,
  RunBacktestResponse,
} from '../types/Backtest'

const client = createHttpClient()

export function fetchLatest(symbol?: string): Promise<BacktestLatestResponse> {
  const params = symbol ? { symbol } : undefined
  return client.request({ method: 'get', url: '/backtests/latest', params })
}

export function runBacktest(payload: RunBacktestPayload): Promise<RunBacktestResponse> {
  return client.request({ method: 'post', url: '/backtests/run', data: payload })
}

export function fetchBacktestJob(jobId: string): Promise<BacktestJobResponse> {
  return client.request({ method: 'get', url: `/backtests/job/${jobId}` })
}

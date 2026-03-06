import { createHttpClient } from './http'
import type {
  BacktestJobResponse,
  BacktestLatestResponse,
  RunBacktestPayload,
  RunBacktestResponse,
} from '../types/Backtest'

const client = createHttpClient()

export interface FetchLatestParams {
  interval?: string
  limit?: number
}

export function fetchLatest(symbol?: string, query?: FetchLatestParams): Promise<BacktestLatestResponse> {
  const composed = {
    ...(symbol ? { symbol } : {}),
    ...(query?.interval ? { interval: query.interval } : {}),
    ...(query?.limit ? { limit: query.limit } : {})
  }
  const params = Object.keys(composed).length ? composed : undefined

  return client.request({ method: 'get', url: '/backtests/latest', params })
}

export function runBacktest(payload: RunBacktestPayload): Promise<RunBacktestResponse> {
  return client.request({ method: 'post', url: '/backtests/run', data: payload })
}

export function fetchBacktestJob(jobId: string): Promise<BacktestJobResponse> {
  return client.request({ method: 'get', url: `/backtests/job/${jobId}` })
}

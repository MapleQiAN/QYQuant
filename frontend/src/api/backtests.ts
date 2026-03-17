import { createHttpClient } from './http'
import type {
  BacktestReportResponse,
  BacktestStatusResponse,
  BacktestJobResponse,
  BacktestLatestResponse,
  RunBacktestPayload,
  RunBacktestResponse,
  SubmitBacktestPayload,
} from '../types/Backtest'

const client = createHttpClient()

export interface FetchLatestParams {
  symbol?: string
  interval?: string
  limit?: number
  startTime?: string | number
  endTime?: string | number
  dataSource?: string
}

export function fetchLatest(params?: FetchLatestParams): Promise<BacktestLatestResponse> {
  return client.request({ method: 'get', url: '/backtests/latest', params })
}

export function runBacktest(payload: RunBacktestPayload): Promise<RunBacktestResponse> {
  return client.request({ method: 'post', url: '/backtests/run', data: payload })
}

export function fetchBacktestJob(jobId: string): Promise<BacktestJobResponse> {
  return client.request({ method: 'get', url: `/backtests/job/${jobId}` })
}

export function submitBacktest(payload: SubmitBacktestPayload): Promise<RunBacktestResponse> {
  return client.request({ method: 'post', url: '/v1/backtest/', data: payload })
}

export function fetchBacktestStatus(jobId: string): Promise<BacktestStatusResponse> {
  return client.request({ method: 'get', url: `/v1/backtest/${jobId}` })
}

export function fetchBacktestReport(jobId: string): Promise<BacktestReportResponse> {
  return client.request({ method: 'get', url: `/v1/backtest/${jobId}/report` })
}

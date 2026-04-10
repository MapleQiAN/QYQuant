import { createHttpClient } from './http'
import type {
  BacktestHistoryResponse,
  BacktestReportResponse,
  BacktestStatusResponse,
  BacktestJobResponse,
  BacktestLatestResponse,
  RunBacktestPayload,
  RunBacktestResponse,
  SubmitBacktestPayload,
  SupportedPackagesResponse,
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

export function fetchBacktestHistory(limit = 50): Promise<BacktestHistoryResponse> {
  return client.request({ method: 'get', url: '/v1/backtest/history', params: { limit } })
}

const STATUS_ERROR_MESSAGES: Record<string, string> = {
  quota_exceeded: 'Backtest quota exhausted. Upgrade your plan or wait for the quota reset before retrying.',
  strategy_timeout: 'Backtest timed out. Reduce the date range or simplify the strategy and try again.',
  soft_time_limit_exceeded: 'Backtest timed out. Reduce the date range or simplify the strategy and try again.',
}

export function getBacktestFailureMessage(status: BacktestStatusResponse): string {
  const rawError = status.error?.raw_error || status.error_message || ''
  if (rawError && STATUS_ERROR_MESSAGES[rawError]) {
    return STATUS_ERROR_MESSAGES[rawError]
  }

  if (status.error?.message) {
    const lineSuffix = status.error.line ? ` (line ${status.error.line})` : ''
    return `Backtest failed: ${status.error.message}${lineSuffix}`
  }

  if (status.error_message) {
    return `Backtest failed: ${status.error_message}`
  }

  if (status.status === 'timeout') {
    return STATUS_ERROR_MESSAGES.strategy_timeout
  }

  return `Backtest job failed: ${status.status}`
}

export function fetchBacktestReport(jobId: string): Promise<BacktestReportResponse> {
  return client.request({ method: 'get', url: `/v1/backtest/${jobId}/report` })
}

export function fetchSupportedPackages(): Promise<SupportedPackagesResponse> {
  return client.request({ method: 'get', url: '/v1/backtest/supported-packages' })
}

import type { KlineBar } from './KlineBar'
import type { Trade } from './Trade'

export interface BacktestSummary {
  totalReturn: number
  annualizedReturn?: number
  sharpeRatio?: number
  maxDrawdown?: number
  winRate?: number
  profitFactor?: number
  totalTrades?: number
  avgHoldingDays?: number
}

export interface BacktestLatestResponse {
  summary: BacktestSummary
  kline: KlineBar[]
  trades: Trade[]
  runtime?: {
    strategyId: string
    strategyVersion: string
    params?: Record<string, unknown>
    logs?: string[]
  }
}

export interface RunBacktestPayload {
  symbol: string
  interval?: string
  limit?: number
  strategyId?: string
  strategyVersion?: string
  strategyParams?: Record<string, unknown>
}

export interface RunBacktestResponse {
  job_id: string
}

export interface BacktestJobResponse {
  status: string
  result?: BacktestLatestResponse
}

export interface Backtest {
  id: string
  name: string
  symbol: string
  status: 'running' | 'completed' | 'failed' | 'queued'
  startedAt: string
  finishedAt?: string
  summary?: BacktestSummary
}

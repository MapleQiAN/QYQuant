import type { KlineBar } from './KlineBar'
import type { Trade } from './Trade'

export interface BacktestSummary {
  totalReturn: number
  annualizedReturn?: number
  sharpeRatio?: number
  maxDrawdown?: number
  volatility?: number
  sortinoRatio?: number
  calmarRatio?: number
  winRate?: number
  profitFactor?: number
  profitLossRatio?: number
  maxConsecutiveLosses?: number
  totalTrades?: number
  avgHoldingDays?: number
  alpha?: number
  beta?: number
}

export interface BacktestLatestResponse {
  summary: BacktestSummary
  kline: KlineBar[]
  trades: Trade[]
  dataSource?: string
  data_range_notice?: string
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

export interface SubmitBacktestPayload {
  strategy_id: string
  symbols: string[]
  start_date: string
  end_date: string
  parameters?: Record<string, unknown>
}

export interface BacktestStatusResponse {
  job_id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'timeout'
  created_at?: string | null
  started_at?: string | null
  completed_at?: string | null
  estimated_wait_time?: number
}

export interface BacktestReportPoint {
  timestamp: number
  equity: number
  benchmark_equity: number
  drawdown?: number
}

export interface BacktestReportResponse {
  job_id: string
  status: string
  params?: Record<string, unknown>
  result_summary: BacktestSummary
  equity_curve: BacktestReportPoint[]
  trades: Trade[]
  completed_at?: string | null
  disclaimer: string
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

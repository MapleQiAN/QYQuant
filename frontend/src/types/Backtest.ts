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

export interface StructuredBacktestError {
  type: string
  line?: number | null
  message: string
  suggestion?: string
  example_code?: string
  raw_error?: string
}

export interface SupportedPackage {
  name: string
  version: string
  description: string
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
  name?: string
  parameters?: Record<string, unknown>
}

export interface BacktestStatusResponse {
  job_id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'timeout'
  created_at?: string | null
  started_at?: string | null
  completed_at?: string | null
  estimated_wait_time?: number
  error?: StructuredBacktestError | null
  error_message?: string | null
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
  result_summary?: BacktestSummary
  equity_curve?: BacktestReportPoint[]
  kline?: KlineBar[]
  trades?: Trade[]
  error?: StructuredBacktestError
  completed_at?: string | null
  disclaimer?: string
}

export interface BacktestHistoryItem {
  job_id: string
  name: string
  strategy_id?: string | null
  strategy_name?: string | null
  symbol?: string | null
  status: 'pending' | 'running' | 'completed' | 'failed' | 'timeout'
  created_at?: string | null
  started_at?: string | null
  completed_at?: string | null
  result_summary?: BacktestSummary | null
  has_report: boolean
}

export interface BacktestHistoryResponse {
  items: BacktestHistoryItem[]
}

export interface SupportedPackagesResponse {
  packages: SupportedPackage[]
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

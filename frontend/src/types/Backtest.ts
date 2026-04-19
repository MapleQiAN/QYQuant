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
  enableAi?: boolean
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
  data_source?: string
  name?: string
  parameters?: Record<string, unknown>
  enable_ai?: boolean
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
  symbol?: string
  interval?: string
  error?: StructuredBacktestError
  completed_at?: string | null
  disclaimer?: string
  report_id?: string | null
  report_status?: string | null
}

export interface BacktestAiChatMessage {
  id: string
  role: string
  message: string
  created_at?: string | null
}

export interface BacktestAiChatHistoryResponse {
  messages: BacktestAiChatMessage[]
}

export interface BacktestAiAlert {
  id: string
  level: string
  title: string
  message: string
  status?: string
  created_at?: string | null
}

export interface BacktestAiAlertsResponse {
  alerts: BacktestAiAlert[]
}

export interface BacktestAiReportPayload {
  metrics?: BacktestSummary
  equity_curve?: BacktestReportPoint[]
  drawdown_series?: Array<{ timestamp: number; drawdown: number }>
  monthly_returns?: Array<{ month: string; return: number }>
  trade_details?: Trade[]
  executive_summary?: string
  metric_narrations?: Record<string, string>
  anomalies?: Array<Record<string, unknown>>
  parameter_sensitivity?: Array<Record<string, unknown>>
  monte_carlo?: Record<string, unknown>
  regime_analysis?: Array<Record<string, unknown>>
  diagnosis_narration?: string
  advisor_narration?: string
}

export interface BacktestAiReportResponse {
  id: string
  job_id: string
  status: string
  payload: BacktestAiReportPayload
}

export interface BacktestAiReportStatusResponse {
  id: string
  job_id: string
  status: string
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

export interface LatestCompletedReportResponse extends BacktestLatestResponse {
  job_id: string
  strategy_name?: string | null
  symbol?: string | null
  interval?: string | null
  completed_at?: string | null
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

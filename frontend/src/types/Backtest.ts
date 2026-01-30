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

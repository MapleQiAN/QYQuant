import { createHttpClient } from './http'

const client = createHttpClient()

export interface DashboardQuota {
  used: number
  limit: number | 'unlimited'
}

export interface LatestSummary {
  total_return: number
  win_rate: number | null
  avg_holding_days: number | null
  sharpe_ratio: number | null
  annualized_return: number | null
  max_drawdown: number | null
  total_trades: number | null
  profit_factor: number | null
}

export interface DashboardStats {
  total_backtests: number
  completed_backtests: number
  strategy_count: number
  active_bots: number
  total_bots: number
  backtest_quota: DashboardQuota
  latest_summary: LatestSummary
  profit_change: number
  profit_history: number[]
}

export function fetchDashboardStats(): Promise<DashboardStats> {
  return client.request({
    method: 'get',
    url: '/v1/dashboard/stats',
  })
}

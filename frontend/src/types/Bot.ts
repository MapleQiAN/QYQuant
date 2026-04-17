export type BotStatus = 'active' | 'paused' | 'error' | 'offline'

export interface Bot {
  id: string
  name: string
  strategy: string
  status: BotStatus
  profit: number
  runtime: string
  capital: number
  tags: string[]
}

export interface ManagedBot extends Bot {
  strategyId: string
  strategyName: string
  integrationId: string
  integrationDisplayName: string
  totalReturnRate: number
  paper: boolean
  createdAt: string | null
  lastErrorMessage: string | null
}

export interface CreateManagedBotPayload {
  name: string
  strategyId: string
  integrationId: string
  capital: number
}

export interface BotPosition {
  symbol: string
  quantity: string
  avgCost: string
  marketValue: string
  realizedPnl: string
}

export interface BotOrder {
  id: string
  symbol: string
  side: string
  price: number
  quantity: number
  status: string
  pnl: number | null
  timestamp: number
  clientOrderId: string | null
}

export interface BotPerformanceSummary {
  latestEquity: number
  totalProfit: number
  totalReturnRate: number
}

export interface BotEquityPoint {
  snapshotDate: string
  equity: number
  availableCash: number
  positionValue: number
  totalProfit: number
  totalReturnRate: number
}

export interface BotPerformance {
  summary: BotPerformanceSummary
  equityCurve: BotEquityPoint[]
  orders: BotOrder[]
}

export interface SimulationBot {
  id: string
  strategy_id: string
  strategy_name: string
  initial_capital: string
  status: 'active' | 'paused' | 'stopped'
  created_at: string
}

export interface SimulationPosition {
  symbol: string
  quantity: string
  avg_cost: string
  updated_at: string
}

export interface CreateBotPayload {
  strategy_id: string
  initial_capital: number
}

export interface SimulationRecord {
  trade_date: string
  equity: string
  cash: string
  daily_return: string
}

export interface SimulationTrade {
  trade_date: string
  symbol: string
  side: 'buy' | 'sell'
  price: string
  quantity: string
}

export interface SimBotStreamPayload {
  records: Pick<SimulationRecord, 'trade_date' | 'equity' | 'daily_return'>[]
  positions: Pick<SimulationPosition, 'symbol' | 'quantity' | 'avg_cost'>[]
}

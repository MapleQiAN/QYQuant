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

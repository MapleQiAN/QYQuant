export interface SimulationBot {
  id: string
  strategy_id: string
  initial_capital: string
  status: 'active' | 'paused' | 'stopped'
  created_at: string
}

export interface CreateBotPayload {
  strategy_id: string
  initial_capital: number
}

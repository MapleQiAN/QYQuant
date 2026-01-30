export type StrategyStatus = 'running' | 'paused' | 'stopped' | 'completed'

export interface Strategy {
  id: string
  name: string
  symbol: string
  status: StrategyStatus
  returns: number
  winRate: number
  maxDrawdown: number
  tags: string[]
  lastUpdate: string
  trades: number
}

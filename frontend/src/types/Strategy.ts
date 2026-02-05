export type StrategyStatus = 'draft' | 'running' | 'paused' | 'stopped' | 'completed'

export interface Strategy {
  id: string
  name: string
  symbol: string
  status: StrategyStatus
  returns: number
  winRate: number
  maxDrawdown: number
  tags: string[]
  lastUpdate: string | number
  trades: number
}

export interface StrategyImportResult {
  strategy: Strategy
  version: {
    id: string
    version: string
    checksum: string
    fileId: string
  }
  file: {
    id: string
    filename: string
    size: number
    path: string
  }
}

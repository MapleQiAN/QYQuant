export type StrategyStatus = 'draft' | 'running' | 'paused' | 'stopped' | 'completed'

export interface Strategy {
  id: string
  name: string
  symbol: string
  status: StrategyStatus
  description?: string | null
  category?: string | null
  source?: string | null
  returns: number
  winRate: number
  maxDrawdown: number
  tags: string[]
  lastUpdate: string | number
  trades: number
  createdAt?: string | number
}

export interface StrategyListResult {
  items: Strategy[]
  page: number
  perPage: number
  total: number
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
  next?: string
}

export type StrategyParamType = 'integer' | 'number' | 'string' | 'boolean' | 'enum' | 'array' | 'object'

export interface StrategyParameter {
  key: string
  type: StrategyParamType
  default?: unknown
  required?: boolean
  min?: number
  max?: number
  step?: number
  enum?: Array<string | number | boolean>
  description?: string
}

export interface StrategyRuntimeDescriptor {
  strategyId: string
  strategyVersion: string
  name?: string
  interface: string
  parameters: StrategyParameter[]
}

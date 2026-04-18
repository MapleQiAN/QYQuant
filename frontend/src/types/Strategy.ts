export type StrategyStatus = 'draft' | 'running' | 'paused' | 'stopped' | 'completed'
export type MarketplaceReviewStatus = 'draft' | 'pending' | 'approved' | 'rejected'

export interface Strategy {
  id: string
  name: string
  title?: string | null
  symbol: string
  status: StrategyStatus
  description?: string | null
  category?: string | null
  source?: string | null
  sourceStrategyId?: string | null
  importMode?: string | null
  reviewStatus?: MarketplaceReviewStatus
  isPublic?: boolean
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

export type StrategyImportSourceType = 'python_file' | 'source_zip' | 'qys_package'

export interface StrategyImportEntrypointCandidate {
  path: string
  callable: string
  interface?: string | null
  confidence?: number | null
}

export interface StrategyImportAnalysis {
  draftImportId: string
  sourceType: StrategyImportSourceType
  fileSummary?: {
    filename: string
    size: number
    entries?: string[]
  } | null
  entrypointCandidates: StrategyImportEntrypointCandidate[]
  metadataCandidates?: Record<string, unknown> | null
  parameterCandidates: StrategyParameter[]
  validation?: {
    entrypointFound?: boolean
    pythonSyntaxValid?: boolean | null
    orderListReturnLikely?: boolean | null
    metadataDetected?: boolean
  } | null
  warnings: string[]
  errors: string[]
}

export interface StrategyImportConfirmPayload {
  draftImportId: string
  selectedEntrypoint: {
    path: string
    callable: string
    interface?: string
  }
  metadata: {
    name: string
    description?: string
    category?: string
    tags?: string[]
    symbol?: string
    version?: string
  }
  parameterDefinitions?: StrategyParameter[]
}

export interface AiStrategyMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface AiStrategyDraftResult {
  reply: string
  analysis: StrategyImportAnalysis | null
}

export type StrategyParameterValue = string | number | boolean | null
export type StrategyParameterDefinitionType = 'int' | 'float' | 'string' | 'enum'

export interface StrategyParameterDefinition {
  name: string
  type: StrategyParameterDefinitionType
  default?: StrategyParameterValue
  required: boolean
  min?: number | null
  max?: number | null
  step?: number | null
  description?: string | null
  options?: StrategyParameterValue[] | null
  userFacing?: Record<string, unknown> | null
}

export interface StrategyPreset {
  id: string
  strategyId: string
  userId?: string
  name: string
  parameters: Record<string, unknown>
  createdAt?: string
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
  user_facing?: Record<string, unknown>
}

export interface StrategyRuntimeDescriptor {
  strategyId: string
  strategyVersion: string
  name?: string
  interface: string
  parameters: StrategyParameter[]
}

export interface MarketplaceStrategyAuthor {
  nickname: string
  avatarUrl: string
}

export type MarketplaceDisplayMetrics = Record<string, number | string | boolean | null>

export interface MarketplaceStrategy {
  id: string
  title: string
  name: string
  description?: string | null
  category?: string | null
  tags: string[]
  isVerified: boolean
  displayMetrics: MarketplaceDisplayMetrics
  author: MarketplaceStrategyAuthor
}

export interface MarketplaceMeta {
  total: number
  page: number
  pageSize: number
}

export interface MarketplaceStrategyListResult {
  data: MarketplaceStrategy[]
  meta: MarketplaceMeta
}

export interface MarketplaceStrategyDetail {
  id: string
  title: string
  description?: string | null
  category?: string | null
  tags: string[]
  shareMode?: string | null
  importMode?: string | null
  trialBacktestEnabled?: boolean
  displayMetrics: MarketplaceDisplayMetrics
  isVerified: boolean
  createdAt?: string | null
  author: MarketplaceStrategyAuthor
  alreadyImported: boolean
  importedStrategyId?: string | null
  hasEquityCurve?: boolean
  canReport?: boolean
}

export interface MarketplaceStrategyEquityCurve {
  dates: Array<number | string>
  values: number[]
}

export interface MarketplaceStrategyImportStatus {
  imported: boolean
  userStrategyId: string | null
}

export interface MarketplaceStrategyImportResult {
  strategyId: string
  redirectTo: string
}

export interface MarketplaceTrialBacktestPayload {
  params?: Record<string, unknown>
  timeRange?: {
    start?: string | null
    end?: string | null
  }
  interval?: string | null
  limit?: number | null
  symbol?: string | null
  strategyVersion?: string | null
  dataSource?: string | null
}

export interface MarketplaceTrialBacktestResult {
  jobId: string
  mode: 'trial'
}

export interface MarketplaceStrategyReportResult {
  reportId: string
}

export interface MarketplacePublishStatus {
  reviewStatus: MarketplaceReviewStatus
  isPublic: boolean
}

export interface MarketplacePublishPayload {
  strategyId: string
  title: string
  description: string
  tags: string[]
  category: string
  displayMetrics: Record<string, number>
}

export interface MarketplacePublishResult {
  strategyId: string
  reviewStatus: MarketplaceReviewStatus
}

export interface MarketplaceFilters {
  q: string
  category: string | null
  verified: boolean
  annualReturnGte: number | null
  maxDrawdownLte: number | null
}

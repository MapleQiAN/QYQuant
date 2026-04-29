import { createHttpClient } from './http'
import type {
  MarketplaceDisplayMetrics,
  MarketplaceMeta,
  MarketplacePublishPayload,
  MarketplacePublishResult,
  MarketplacePublishStatus,
  MarketplaceStrategy,
  MarketplaceStrategyDetail,
  MarketplaceStrategyEquityCurve,
  MarketplaceStrategyImportResult,
  MarketplaceStrategyReportResult,
  MarketplaceStrategyImportStatus,
  MarketplaceTrialBacktestPayload,
  MarketplaceTrialBacktestResult,
  AiStrategyDraftResult,
  AiStrategyMessage,
  AiSessionDetail,
  AiSessionSummary,
  Strategy,
  StrategyCodePayload,
  StrategyCodeResult,
  StrategyCodeUpdateResult,
  StrategyImportAnalysis,
  StrategyImportConfirmPayload,
  StrategyParameterDefinition,
  StrategyPreset,
  StrategyImportResult,
  StrategyListResult,
  StrategyRuntimeDescriptor,
  MarketplaceStrategyListResult
} from '../types/Strategy'
import type { PaginatedCommunityPosts } from '../types/community'

const client = createHttpClient()

export function fetchRecent(): Promise<Strategy[]> {
  return client.request({ method: 'get', url: '/strategies/recent' })
}

export function fetchStrategies(params?: {
  page?: number
  perPage?: number
  sort?: string
  order?: 'asc' | 'desc'
}): Promise<StrategyListResult> {
  return client.request({
    method: 'get',
    url: '/v1/strategies/',
    params: params
      ? {
          page: params.page,
          per_page: params.perPage,
          sort: params.sort,
          order: params.order
        }
      : undefined
  })
}

interface MarketplaceStrategyDto {
  id: string
  title?: string | null
  name: string
  description?: string | null
  category?: string | null
  tags?: string[]
  is_verified?: boolean
  display_metrics?: MarketplaceDisplayMetrics
  author?: {
    nickname?: string
    avatar_url?: string
  }
}

interface MarketplaceStrategyDetailDto {
  id: string
  title?: string | null
  description?: string | null
  category?: string | null
  tags?: string[]
  share_mode?: string | null
  import_mode?: string | null
  trial_backtest_enabled?: boolean
  display_metrics?: MarketplaceDisplayMetrics
  is_verified?: boolean
  created_at?: string | null
  author?: {
    nickname?: string
    avatar_url?: string
  }
  already_imported?: boolean
  imported_strategy_id?: string | null
  has_equity_curve?: boolean
  can_report?: boolean
}

interface MarketplaceParams {
  page?: number
  pageSize?: number
  featured?: boolean
  q?: string
  category?: string | null
  verified?: boolean
  annualReturnGte?: number | null
  maxDrawdownLte?: number | null
}

interface MarketplaceStrategyImportDto {
  strategy_id?: string
  redirect_to?: string
}

interface MarketplaceStrategyImportStatusDto {
  imported?: boolean
  user_strategy_id?: string | null
}

interface MarketplaceTrialBacktestDto {
  job_id?: string
  mode?: string
}

interface MarketplacePublishDto {
  strategy_id?: string
  review_status?: string
}

interface MarketplacePublishStatusDto {
  review_status?: string
  is_public?: boolean
}

interface MarketplaceStrategyReportDto {
  report_id?: string
}

export function fetchMarketplaceStrategies(params: { tag: string }): Promise<Strategy[]>
export function fetchMarketplaceStrategies(params?: MarketplaceParams): Promise<MarketplaceStrategyListResult>
export async function fetchMarketplaceStrategies(
  params?: { tag: string } | MarketplaceParams
): Promise<Strategy[] | MarketplaceStrategyListResult> {
  if (params && 'tag' in params) {
    return client.request({
      method: 'get',
      url: '/v1/marketplace/strategies',
      params
    })
  }

  const page = params?.page ?? 1
  const pageSize = params?.pageSize ?? 20
  const response = await client.requestWithMeta<MarketplaceStrategyDto[]>({
    method: 'get',
    url: '/v1/marketplace/strategies',
    params: {
      page,
      page_size: pageSize,
      featured: params?.featured,
      q: params?.q,
      category: params?.category ?? undefined,
      verified: params?.verified || undefined,
      annual_return_gte: params?.annualReturnGte ?? undefined,
      max_drawdown_lte: params?.maxDrawdownLte ?? undefined
    }
  })

  return {
    data: (response.data ?? []).map((item) => mapMarketplaceStrategy(item)),
    meta: normalizeMarketplaceMeta(response.meta, page, pageSize)
  }
}

function normalizeMarketplaceMeta(
  meta: Record<string, unknown> | undefined,
  fallbackPage: number,
  fallbackPageSize: number
): MarketplaceMeta {
  const total = toNumber(meta?.total, 0)
  const page = toNumber(meta?.page, fallbackPage)
  const pageSize = toNumber(meta?.page_size ?? meta?.pageSize, fallbackPageSize)
  return { total, page, pageSize }
}

function toNumber(value: unknown, fallback: number): number {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value
  }
  if (typeof value === 'string') {
    const parsed = Number(value)
    if (Number.isFinite(parsed)) {
      return parsed
    }
  }
  return fallback
}

function normalizeMarketplaceTrialBacktest(response: MarketplaceTrialBacktestDto): MarketplaceTrialBacktestResult {
  if (typeof response.job_id !== 'string' || response.job_id.trim() === '') {
    throw new Error('Invalid marketplace trial backtest response: missing job_id')
  }
  if (response.mode !== 'trial') {
    throw new Error(`Invalid marketplace trial backtest response: unexpected mode "${String(response.mode)}"`)
  }

  return {
    jobId: response.job_id,
    mode: response.mode
  }
}

function mapMarketplaceStrategy(item: MarketplaceStrategyDto): MarketplaceStrategy {
  return {
    id: item.id,
    title: item.title || item.name,
    name: item.name,
    description: item.description ?? '',
    category: item.category ?? '',
    tags: Array.isArray(item.tags) ? item.tags : [],
    isVerified: Boolean(item.is_verified),
    displayMetrics: normalizeMarketplaceDisplayMetrics(item.display_metrics),
    author: {
      nickname: item.author?.nickname ?? '',
      avatarUrl: item.author?.avatar_url ?? ''
    }
  }
}

function mapMarketplaceStrategyDetail(item: MarketplaceStrategyDetailDto): MarketplaceStrategyDetail {
  return {
    id: item.id,
    title: item.title || '',
    description: item.description ?? '',
    category: item.category ?? '',
    tags: Array.isArray(item.tags) ? item.tags : [],
    shareMode: item.share_mode ?? null,
    importMode: item.import_mode ?? null,
    trialBacktestEnabled: Boolean(item.trial_backtest_enabled),
    displayMetrics: normalizeMarketplaceDisplayMetrics(item.display_metrics),
    isVerified: Boolean(item.is_verified),
    createdAt: item.created_at ?? null,
    author: {
      nickname: item.author?.nickname ?? '',
      avatarUrl: item.author?.avatar_url ?? ''
    },
    alreadyImported: Boolean(item.already_imported),
    importedStrategyId: item.imported_strategy_id ?? null,
    hasEquityCurve: Boolean(item.has_equity_curve),
    canReport: Boolean(item.can_report)
  }
}

export async function fetchMarketplaceStrategyDetail(strategyId: string): Promise<MarketplaceStrategyDetail> {
  const response = await client.request<MarketplaceStrategyDetailDto>({
    method: 'get',
    url: `/v1/marketplace/strategies/${strategyId}`
  })
  return mapMarketplaceStrategyDetail(response)
}

export function fetchMarketplaceStrategyEquityCurve(strategyId: string): Promise<MarketplaceStrategyEquityCurve> {
  return client.request({
    method: 'get',
    url: `/v1/marketplace/strategies/${strategyId}/equity-curve`
  })
}

export function fetchMarketplaceStrategyPosts(strategyId: string): Promise<PaginatedCommunityPosts> {
  return client.request({
    method: 'get',
    url: `/v1/marketplace/strategies/${strategyId}/posts`
  })
}

export async function importMarketplaceStrategy(strategyId: string): Promise<MarketplaceStrategyImportResult> {
  const response = await client.request<MarketplaceStrategyImportDto>({
    method: 'post',
    url: `/v1/marketplace/strategies/${strategyId}/import`
  })

  return {
    strategyId: response.strategy_id || '',
    redirectTo: response.redirect_to || ''
  }
}

export async function fetchMarketplaceStrategyImportStatus(strategyId: string): Promise<MarketplaceStrategyImportStatus> {
  const response = await client.request<MarketplaceStrategyImportStatusDto>({
    method: 'get',
    url: `/v1/marketplace/strategies/${strategyId}/import-status`
  })

  return {
    imported: Boolean(response.imported),
    userStrategyId: response.user_strategy_id ?? null
  }
}

export async function launchMarketplaceTrialBacktest(
  strategyId: string,
  payload: MarketplaceTrialBacktestPayload
): Promise<MarketplaceTrialBacktestResult> {
  const response = await client.request<MarketplaceTrialBacktestDto>({
    method: 'post',
    url: `/v1/marketplace/strategies/${strategyId}/trial-backtest`,
    data: {
      params: payload.params ?? {},
      time_range: payload.timeRange
        ? {
            start: payload.timeRange.start ?? undefined,
            end: payload.timeRange.end ?? undefined
          }
        : undefined,
      interval: payload.interval ?? undefined,
      limit: payload.limit ?? undefined,
      symbol: payload.symbol ?? undefined,
      strategy_version: payload.strategyVersion ?? undefined,
      data_source: payload.dataSource ?? undefined
    }
  })

  return normalizeMarketplaceTrialBacktest(response)
}

export async function publishMarketplaceStrategy(payload: MarketplacePublishPayload): Promise<MarketplacePublishResult> {
  const response = await client.request<MarketplacePublishDto>({
    method: 'post',
    url: '/v1/marketplace/strategies',
    data: {
      strategy_id: payload.strategyId,
      title: payload.title,
      description: payload.description,
      tags: payload.tags,
      category: payload.category,
      display_metrics: payload.displayMetrics
    }
  })

  return {
    strategyId: response.strategy_id || '',
    reviewStatus: normalizeReviewStatus(response.review_status)
  }
}

export async function fetchMarketplacePublishStatus(strategyId: string): Promise<MarketplacePublishStatus> {
  const response = await client.request<MarketplacePublishStatusDto>({
    method: 'get',
    url: `/v1/marketplace/strategies/${strategyId}/publish-status`
  })

  return {
    reviewStatus: normalizeReviewStatus(response.review_status),
    isPublic: Boolean(response.is_public)
  }
}

export async function reportMarketplaceStrategy(
  strategyId: string,
  reason: string
): Promise<MarketplaceStrategyReportResult> {
  const response = await client.request<MarketplaceStrategyReportDto>({
    method: 'post',
    url: `/v1/marketplace/strategies/${strategyId}/report`,
    data: {
      reason
    }
  })

  return {
    reportId: response.report_id || ''
  }
}

export function createStrategy(payload: {
  name: string
  symbol: string
  tags?: string[]
  status?: string
}): Promise<Strategy> {
  return client.request({ method: 'post', url: '/strategies', data: payload })
}

export function importStrategy(file: File): Promise<StrategyImportResult> {
  const form = new FormData()
  form.append('file', file)
  return client.request({
    method: 'post',
    url: '/v1/strategies/import',
    data: form,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function analyzeStrategyImport(file: File): Promise<StrategyImportAnalysis> {
  const form = new FormData()
  form.append('file', file)
  return client.request({
    method: 'post',
    url: '/v1/strategy-imports/analyze',
    data: form,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function confirmStrategyImport(payload: StrategyImportConfirmPayload): Promise<StrategyImportResult> {
  return client.request({
    method: 'post',
    url: '/v1/strategy-imports/confirm',
    data: payload
  })
}

export function fetchDraftCode(draftImportId: string): Promise<{ code: string; filename: string }> {
  return client.request({
    method: 'get',
    url: `/v1/strategy-imports/${draftImportId}/code`,
  })
}

export function generateAiStrategyDraft(payload: {
  integrationId: string
  messages: AiStrategyMessage[]
  locale?: string
  sessionId?: string
  mode?: 'direct' | 'qsga'
  options?: Record<string, unknown>
}): Promise<AiStrategyDraftResult> {
  const data: Record<string, unknown> = {
    integrationId: payload.integrationId,
    messages: payload.messages,
  }
  if (payload.locale) data.locale = payload.locale
  if (payload.sessionId) data.sessionId = payload.sessionId
  if (payload.mode) data.mode = payload.mode
  if (payload.options) data.options = payload.options

  return client.request({
    method: 'post',
    url: '/v1/strategy-ai/generate',
    timeout: 60000,
    data
  })
}

export function listAiSessions(params?: {
  page?: number
  perPage?: number
}): Promise<{ data: AiSessionSummary[]; meta?: Record<string, unknown> }> {
  return client.requestWithMeta({
    method: 'get',
    url: '/v1/ai-sessions',
    params,
  })
}

export function getAiSession(sessionId: string): Promise<AiSessionDetail> {
  return client.request({
    method: 'get',
    url: `/v1/ai-sessions/${sessionId}`,
  })
}

export function deleteAiSession(sessionId: string): Promise<{ deletedId: string }> {
  return client.request({
    method: 'delete',
    url: `/v1/ai-sessions/${sessionId}`,
  })
}

export function deleteStrategy(strategyId: string): Promise<{ deletedId: string }> {
  return client.request({
    method: 'delete',
    url: `/v1/strategies/${strategyId}`
  })
}

export interface IntentClassificationResult {
  strategy_type: string
  direction: string
  timeframe: string
  confidence: number
}

export function classifyStrategyIntent(payload: {
  integrationId: string
  description: string
}): Promise<IntentClassificationResult> {
  return client.request({
    method: 'post',
    url: '/v1/strategy-ai/classify',
    timeout: 60000,
    data: payload
  })
}

export interface RiskProfileResult {
  profile: {
    max_single_loss_pct: number
    position_ratio: number
    drawdown_tolerance: string
    consecutive_loss_patience: number
    style: string
  }
  generatorContext: Record<string, unknown>
}

export function buildRiskProfile(payload: {
  max_single_loss_pct: number
  position_ratio: number
  drawdown_tolerance: string
  consecutive_loss_patience: number
  style: string
}): Promise<RiskProfileResult> {
  return client.request({
    method: 'post',
    url: '/v1/strategy-risk-profile',
    data: payload
  })
}

export interface StrategySummaryResult {
  summary: string
  explanation: string
  parameters: Array<{ key: string; label: string; purpose: string }>
}

export function fetchStrategySummary(payload: {
  integrationId: string
  code: string
  parameters: Array<Record<string, unknown>>
}): Promise<StrategySummaryResult> {
  return client.request({
    method: 'post',
    url: '/v1/strategy-ai/summary',
    timeout: 60000,
    data: payload
  })
}

export interface OptimizationResult {
  topResults: Array<{
    params: Record<string, unknown>
    inSampleScore: number
    outOfSampleScore: number
    combinedScore: number
    summary: Record<string, unknown>
    outOfSampleSummary?: Record<string, unknown>
  }>
  overfittingRisk: string
  searchSpaceSize: number
  evaluations: number
}

export function optimizeStrategy(
  strategyId: string,
  payload: {
    parameters: Array<Record<string, unknown>>
    level?: 'quick' | 'standard' | 'deep'
    riskStyle?: string
    symbol?: string
    interval?: string
    limit?: number
    startTime?: number
    endTime?: number
    strategyVersion?: string
    dataSource?: string
  }
): Promise<OptimizationResult> {
  return client.request({
    method: 'post',
    url: `/v1/strategies/${strategyId}/optimize`,
    timeout: 60000,
    data: payload
  })
}

export function generateUserFacing(payload: {
  integrationId: string
  parameters: Array<Record<string, unknown>>
}): Promise<{ parameters: Array<Record<string, unknown>> }> {
  return client.request({
    method: 'post',
    url: '/v1/strategy-ai/user-facing',
    timeout: 60000,
    data: payload
  })
}

export async function exportStrategy(payload: {
  draftImportId: string
  format: 'qys' | 'py'
  metadata?: Record<string, unknown>
  parameterDefinitions?: Array<Record<string, unknown>>
  codeOverride?: string
}): Promise<Blob> {
  const response = await fetch('/api/v1/strategy-ai/export', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(_authHeaders())
    },
    body: JSON.stringify(payload)
  })
  if (!response.ok) {
    const errorBody = await response.text()
    throw new Error(errorBody || 'Export failed')
  }
  return response.blob()
}

function _authHeaders(): Record<string, string> {
  const token = localStorage.getItem('qyquant-token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export function fetchRuntimeDescriptor(strategyId: string, version?: string): Promise<StrategyRuntimeDescriptor> {
  const params = version ? { version } : undefined
  return client.request({ method: 'get', url: `/strategies/${strategyId}/runtime`, params })
}

export function fetchStrategyParameters(strategyId: string): Promise<StrategyParameterDefinition[]> {
  return client.request({
    method: 'get',
    url: `/v1/strategies/${strategyId}/parameters`
  })
}

export function fetchStrategyPresets(strategyId: string): Promise<StrategyPreset[]> {
  return client.request({
    method: 'get',
    url: `/v1/strategies/${strategyId}/presets`
  })
}

export function createStrategyPreset(
  strategyId: string,
  payload: { name: string; parameters: Record<string, unknown> }
): Promise<StrategyPreset> {
  return client.request({
    method: 'post',
    url: `/v1/strategies/${strategyId}/presets`,
    data: payload
  })
}

export function updateStrategyPreset(
  strategyId: string,
  presetId: string,
  payload: { name: string; parameters: Record<string, unknown> }
): Promise<StrategyPreset> {
  return client.request({
    method: 'put',
    url: `/v1/strategies/${strategyId}/presets/${presetId}`,
    data: payload
  })
}

export function deleteStrategyPreset(strategyId: string, presetId: string): Promise<{ deletedId: string }> {
  return client.request({
    method: 'delete',
    url: `/v1/strategies/${strategyId}/presets/${presetId}`
  })
}

export function createStrategyWithCode(payload: StrategyCodePayload): Promise<Strategy> {
  return client.request({
    method: 'post',
    url: '/v1/strategies/code',
    data: payload
  })
}

export function fetchStrategyCode(strategyId: string): Promise<StrategyCodeResult> {
  return client.request({
    method: 'get',
    url: `/v1/strategies/${strategyId}/code`
  })
}

export function updateStrategyCode(
  strategyId: string,
  payload: { code?: string; metadata?: { name?: string; description?: string; category?: string; tags?: string[] } }
): Promise<StrategyCodeUpdateResult> {
  return client.request({
    method: 'put',
    url: `/v1/strategies/${strategyId}/code`,
    data: payload
  })
}

function normalizeMarketplaceDisplayMetrics(
  metrics: MarketplaceDisplayMetrics | undefined
): MarketplaceDisplayMetrics {
  if (!metrics || typeof metrics !== 'object') {
    return {}
  }

  const normalized = { ...metrics }
  if (normalized.annualized_return == null && normalized.annual_return != null) {
    normalized.annualized_return = normalized.annual_return
  }
  return normalized
}

function normalizeReviewStatus(value: unknown): MarketplacePublishStatus['reviewStatus'] {
  return value === 'pending' || value === 'approved' || value === 'rejected' ? value : 'draft'
}

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
  MarketplaceStrategyImportStatus,
  Strategy,
  StrategyParameterDefinition,
  StrategyPreset,
  StrategyImportResult,
  StrategyListResult,
  StrategyRuntimeDescriptor,
  MarketplaceStrategyListResult
} from '../types/Strategy'

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

interface MarketplacePublishDto {
  strategy_id?: string
  review_status?: string
}

interface MarketplacePublishStatusDto {
  review_status?: string
  is_public?: boolean
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
    displayMetrics: normalizeMarketplaceDisplayMetrics(item.display_metrics),
    isVerified: Boolean(item.is_verified),
    createdAt: item.created_at ?? null,
    author: {
      nickname: item.author?.nickname ?? '',
      avatarUrl: item.author?.avatar_url ?? ''
    },
    alreadyImported: Boolean(item.already_imported),
    importedStrategyId: item.imported_strategy_id ?? null,
    hasEquityCurve: Boolean(item.has_equity_curve)
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

export function deleteStrategy(strategyId: string): Promise<{ deletedId: string }> {
  return client.request({
    method: 'delete',
    url: `/v1/strategies/${strategyId}`
  })
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

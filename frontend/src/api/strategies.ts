import { createHttpClient } from './http'
import type {
  MarketplaceDisplayMetrics,
  MarketplaceMeta,
  MarketplaceStrategy,
  MarketplaceStrategyDetail,
  MarketplaceStrategyEquityCurve,
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
      featured: params?.featured
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
    displayMetrics: item.display_metrics && typeof item.display_metrics === 'object' ? item.display_metrics : {},
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
    displayMetrics: item.display_metrics && typeof item.display_metrics === 'object' ? item.display_metrics : {},
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

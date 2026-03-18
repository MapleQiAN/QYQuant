import { createHttpClient } from './http'
import type {
  MarketplaceStrategyDetail,
  MarketplaceStrategyEquityCurve,
  Strategy,
  StrategyParameterDefinition,
  StrategyPreset,
  StrategyImportResult,
  StrategyListResult,
  StrategyRuntimeDescriptor
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

export function fetchMarketplaceStrategies(params?: { tag?: string }): Promise<Strategy[]> {
  return client.request({
    method: 'get',
    url: '/v1/marketplace/strategies',
    params,
  })
}

export function fetchMarketplaceStrategyDetail(strategyId: string): Promise<MarketplaceStrategyDetail> {
  return client.request({
    method: 'get',
    url: `/v1/marketplace/strategies/${strategyId}`,
  })
}

export function fetchMarketplaceStrategyEquityCurve(strategyId: string): Promise<MarketplaceStrategyEquityCurve> {
  return client.request({
    method: 'get',
    url: `/v1/marketplace/strategies/${strategyId}/equity-curve`,
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

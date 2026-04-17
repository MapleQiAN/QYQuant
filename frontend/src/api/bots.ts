import { createHttpClient } from './http'
import type { Bot, BotEquityPoint, BotOrder, BotPerformance, BotPosition, BotStatus, CreateManagedBotPayload, ManagedBot } from '../types/Bot'

const client = createHttpClient()

interface BotDto {
  id: string
  name?: string | null
  strategy?: string | null
  strategy_id?: string | null
  strategy_name?: string | null
  integration_id?: string | null
  integration_display_name?: string | null
  status?: string | null
  profit?: number | null
  total_return_rate?: number | null
  runtime?: string | null
  capital?: number | null
  tags?: string[] | null
  paper?: boolean | null
  created_at?: string | null
  last_error_message?: string | null
}

interface BotPositionDto {
  symbol: string
  quantity?: string | null
  avg_cost?: string | null
  market_value?: string | null
  realized_pnl?: string | null
}

interface BotOrderDto {
  id: string
  symbol?: string | null
  side?: string | null
  price?: number | null
  quantity?: number | null
  status?: string | null
  pnl?: number | null
  timestamp?: number | null
  client_order_id?: string | null
}

interface BotPerformanceDto {
  summary?: {
    latest_equity?: number | null
    total_profit?: number | null
    total_return_rate?: number | null
  } | null
  equity_curve?: Array<{
    snapshot_date: string
    equity?: number | null
    available_cash?: number | null
    position_value?: number | null
    total_profit?: number | null
    total_return_rate?: number | null
  }> | null
  orders?: BotOrderDto[] | null
}

export function fetchRecent(): Promise<Bot[]> {
  return client.request<BotDto[]>({ method: 'get', url: '/bots/recent' }).then((items) => (items ?? []).map(normalizeRecentBot))
}

export function fetchBots(): Promise<ManagedBot[]> {
  return client.request<BotDto[]>({ method: 'get', url: '/bots' }).then((items) => (items ?? []).map(normalizeManagedBot))
}

export function createBot(payload: CreateManagedBotPayload): Promise<ManagedBot> {
  return client.request<BotDto>({
    method: 'post',
    url: '/bots',
    data: {
      name: payload.name,
      strategy_id: payload.strategyId,
      integration_id: payload.integrationId,
      capital: payload.capital,
    },
  }).then(normalizeManagedBot)
}

export function updateBotStatus(botId: string, status: Extract<BotStatus, 'active' | 'paused'>): Promise<{ id: string; status: BotStatus }> {
  return client.request<{ id: string; status?: string | null }>({
    method: 'patch',
    url: `/bots/${botId}/status`,
    data: { status },
  }).then((item) => ({
    id: item.id,
    status: normalizeStatus(item.status),
  }))
}

export function fetchBotPositions(botId: string): Promise<BotPosition[]> {
  return client.request<BotPositionDto[]>({
    method: 'get',
    url: `/bots/${botId}/positions`,
  }).then((items) => (items ?? []).map(normalizePosition))
}

export function fetchBotPerformance(botId: string): Promise<BotPerformance> {
  return client.request<BotPerformanceDto>({
    method: 'get',
    url: `/bots/${botId}/performance`,
  }).then(normalizePerformance)
}

function normalizeStatus(status?: string | null): BotStatus {
  if (status === 'paused' || status === 'error' || status === 'offline') {
    return status
  }
  return 'active'
}

function normalizeRecentBot(item: BotDto): Bot {
  return {
    id: item.id,
    name: item.name ?? '',
    strategy: item.strategy ?? item.strategy_name ?? '',
    status: normalizeStatus(item.status),
    profit: item.profit ?? 0,
    runtime: item.runtime ?? '0h',
    capital: item.capital ?? 0,
    tags: item.tags ?? [],
  }
}

function normalizeManagedBot(item: BotDto): ManagedBot {
  const base = normalizeRecentBot(item)
  return {
    ...base,
    strategyId: item.strategy_id ?? '',
    strategyName: item.strategy_name ?? item.strategy ?? '',
    integrationId: item.integration_id ?? '',
    integrationDisplayName: item.integration_display_name ?? '',
    totalReturnRate: item.total_return_rate ?? 0,
    paper: item.paper !== false,
    createdAt: item.created_at ?? null,
    lastErrorMessage: item.last_error_message ?? null,
  }
}

function normalizePosition(item: BotPositionDto): BotPosition {
  return {
    symbol: item.symbol,
    quantity: item.quantity ?? '0.0000',
    avgCost: item.avg_cost ?? '0.0000',
    marketValue: item.market_value ?? '0.0000',
    realizedPnl: item.realized_pnl ?? '0.0000',
  }
}

function normalizeOrder(item: BotOrderDto): BotOrder {
  return {
    id: item.id,
    symbol: item.symbol ?? '',
    side: item.side ?? '',
    price: item.price ?? 0,
    quantity: item.quantity ?? 0,
    status: item.status ?? '',
    pnl: item.pnl ?? null,
    timestamp: item.timestamp ?? 0,
    clientOrderId: item.client_order_id ?? null,
  }
}

function normalizeEquityPoint(item: NonNullable<BotPerformanceDto['equity_curve']>[number]): BotEquityPoint {
  return {
    snapshotDate: item.snapshot_date,
    equity: item.equity ?? 0,
    availableCash: item.available_cash ?? 0,
    positionValue: item.position_value ?? 0,
    totalProfit: item.total_profit ?? 0,
    totalReturnRate: item.total_return_rate ?? 0,
  }
}

function normalizePerformance(item: BotPerformanceDto): BotPerformance {
  return {
    summary: {
      latestEquity: item.summary?.latest_equity ?? 0,
      totalProfit: item.summary?.total_profit ?? 0,
      totalReturnRate: item.summary?.total_return_rate ?? 0,
    },
    equityCurve: (item.equity_curve ?? []).map(normalizeEquityPoint),
    orders: (item.orders ?? []).map(normalizeOrder),
  }
}

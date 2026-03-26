import { createHttpClient } from './http'

const client = createHttpClient()

export interface AdminHealthResponse {
  status: string
  scope: string
}

export interface AdminQueueStats {
  pending: number
  running: number
  avgDuration: number
  failureRate1h: number
}

export interface AdminStuckJob {
  jobId: string
  userId: string
  strategyId: string
  strategyName: string
  startedAt: string | null
  runningDurationSeconds: number
}

export interface AdminQueueStatsResult {
  stats: AdminQueueStats
  stuckJobs: AdminStuckJob[]
}

export interface AdminTerminateJobResult {
  jobId: string
  status: 'terminated'
}

export interface AdminReviewStrategy {
  id: string
  title: string
  name: string
  description: string
  category: string
  tags: string[]
  displayMetrics: Record<string, unknown>
  ownerId: string
  authorNickname: string
  createdAt: string | null
  reviewStatus: 'pending' | 'approved' | 'rejected'
}

export interface AdminReviewQueueResult {
  data: AdminReviewStrategy[]
  meta: {
    total: number
    page: number
    perPage: number
  }
}

export interface AdminReviewMutationPayload {
  status: 'approved' | 'rejected'
  reason?: string
}

export interface AdminReviewMutationResult {
  strategyId: string
  reviewStatus: 'pending' | 'approved' | 'rejected'
}

export interface AdminReport {
  id: string
  reporterId: string
  reporterNickname: string
  strategyId: string
  strategyTitle: string
  strategyAuthorId: string
  strategyAuthorNickname: string
  reason: string
  status: 'pending' | 'reviewed' | 'dismissed'
  createdAt: string | null
}

export interface AdminReportQueueResult {
  data: AdminReport[]
  meta: {
    total: number
    page: number
    perPage: number
  }
}

export interface AdminResolveReportPayload {
  action: 'takedown' | 'dismiss'
  adminNote?: string
}

export interface AdminResolveReportResult {
  reportId: string
  status: 'pending' | 'reviewed' | 'dismissed'
  action: 'takedown' | 'dismiss'
}

export interface AdminUser {
  userId: string
  nickname: string
  phone: string
  createdAt: string | null
  planLevel: string
  isBanned: boolean
}

export interface AdminUserListResult {
  data: AdminUser[]
  meta: {
    total: number
    page: number
    perPage: number
  }
}

export interface AdminUserListParams {
  search?: string
  page?: number
  perPage?: number
}

export interface AdminUserBanStatusPayload {
  isBanned: boolean
  banReason?: string
}

export interface AdminUserBanStatusResult {
  userId: string
  isBanned: boolean
}

export interface AdminAuditLog {
  id: string
  operatorId: string
  operatorNickname: string
  action: string
  targetType: string
  targetId: string
  details: Record<string, unknown>
  createdAt: string | null
}

export interface AdminAuditLogListResult {
  data: AdminAuditLog[]
  meta: {
    total: number
    page: number
    perPage: number
  }
}

export interface AdminAuditLogFilters {
  operatorId?: string
  action?: string
  targetType?: string
  targetId?: string
  dateFrom?: string
  dateTo?: string
  page?: number
  perPage?: number
}

interface AdminQueueStatsDto {
  stats?: {
    pending?: number | string | null
    running?: number | string | null
    avg_duration?: number | string | null
    failure_rate_1h?: number | string | null
  } | null
  stuck_jobs?: AdminStuckJobDto[] | null
}

interface AdminStuckJobDto {
  job_id?: string | null
  user_id?: string | null
  strategy_id?: string | null
  strategy_name?: string | null
  started_at?: string | null
  running_duration_seconds?: number | string | null
}

interface AdminTerminateJobDto {
  job_id?: string
  status?: string | null
}

interface AdminReviewStrategyDto {
  id: string
  title?: string | null
  name: string
  description?: string | null
  category?: string | null
  tags?: string[]
  display_metrics?: Record<string, unknown>
  owner_id?: string | null
  author_nickname?: string | null
  created_at?: string | null
  review_status?: string | null
}

interface AdminReviewMutationDto {
  strategy_id?: string
  review_status?: string | null
}

interface AdminReportDto {
  id: string
  reporter_id?: string | null
  reporter_nickname?: string | null
  strategy_id?: string | null
  strategy_title?: string | null
  strategy_author_id?: string | null
  strategy_author_nickname?: string | null
  reason?: string | null
  status?: string | null
  created_at?: string | null
}

interface AdminResolveReportDto {
  report_id?: string
  status?: string | null
  action?: string | null
}

interface AdminUserDto {
  user_id?: string | null
  nickname?: string | null
  phone?: string | null
  created_at?: string | null
  plan_level?: string | null
  is_banned?: boolean | null
}

interface AdminUserBanStatusDto {
  user_id?: string | null
  is_banned?: boolean | null
}

interface AdminAuditLogDto {
  id?: string | null
  operator_id?: string | null
  operator_nickname?: string | null
  action?: string | null
  target_type?: string | null
  target_id?: string | null
  details?: Record<string, unknown> | null
  created_at?: string | null
}

export function fetchAdminHealth(): Promise<AdminHealthResponse> {
  return client.request({
    method: 'get',
    url: '/v1/admin/health'
  })
}

export async function fetchQueueStats(): Promise<AdminQueueStatsResult> {
  const response = await client.request<AdminQueueStatsDto>({
    method: 'get',
    url: '/v1/admin/backtest/queue-stats'
  })

  return {
    stats: {
      pending: toNumber(response.stats?.pending, 0),
      running: toNumber(response.stats?.running, 0),
      avgDuration: toNumber(response.stats?.avg_duration, 0),
      failureRate1h: toNumber(response.stats?.failure_rate_1h, 0)
    },
    stuckJobs: (response.stuck_jobs ?? []).map((item) => ({
      jobId: item.job_id ?? '',
      userId: item.user_id ?? '',
      strategyId: item.strategy_id ?? '',
      strategyName: item.strategy_name ?? '',
      startedAt: item.started_at ?? null,
      runningDurationSeconds: toNumber(item.running_duration_seconds, 0)
    }))
  }
}

export async function terminateJob(
  jobId: string,
  adminNote?: string
): Promise<AdminTerminateJobResult> {
  const response = await client.request<AdminTerminateJobDto>({
    method: 'delete',
    url: `/v1/admin/backtest/${jobId}`,
    data: {
      admin_note: adminNote
    }
  })

  return {
    jobId: response.job_id || '',
    status: normalizeTerminateStatus(response.status)
  }
}

export async function fetchPendingStrategyReviews(params?: {
  page?: number
  perPage?: number
}): Promise<AdminReviewQueueResult> {
  const page = params?.page ?? 1
  const perPage = params?.perPage ?? 20
  const response = await client.requestWithMeta<AdminReviewStrategyDto[]>({
    method: 'get',
    url: '/v1/admin/strategies',
    params: {
      review_status: 'pending',
      page,
      per_page: perPage
    }
  })

  return {
    data: (response.data ?? []).map((item) => ({
      id: item.id,
      title: item.title || item.name,
      name: item.name,
      description: item.description ?? '',
      category: item.category ?? '',
      tags: Array.isArray(item.tags) ? item.tags : [],
      displayMetrics: item.display_metrics ?? {},
      ownerId: item.owner_id ?? '',
      authorNickname: item.author_nickname ?? '',
      createdAt: item.created_at ?? null,
      reviewStatus: normalizeReviewStatus(item.review_status)
    })),
    meta: {
      total: toNumber(response.meta?.total, 0),
      page: toNumber(response.meta?.page, page),
      perPage: toNumber(response.meta?.per_page, perPage)
    }
  }
}

export async function submitStrategyReview(
  strategyId: string,
  payload: AdminReviewMutationPayload
): Promise<AdminReviewMutationResult> {
  const response = await client.request<AdminReviewMutationDto>({
    method: 'patch',
    url: `/v1/admin/strategies/${strategyId}/review`,
    data: {
      status: payload.status,
      reason: payload.reason
    }
  })

  return {
    strategyId: response.strategy_id || '',
    reviewStatus: normalizeReviewStatus(response.review_status)
  }
}

export async function fetchPendingReports(params?: {
  page?: number
  perPage?: number
}): Promise<AdminReportQueueResult> {
  const page = params?.page ?? 1
  const perPage = params?.perPage ?? 20
  const response = await client.requestWithMeta<AdminReportDto[]>({
    method: 'get',
    url: '/v1/admin/reports',
    params: {
      status: 'pending',
      page,
      per_page: perPage
    }
  })

  return {
    data: (response.data ?? []).map((item) => ({
      id: item.id,
      reporterId: item.reporter_id ?? '',
      reporterNickname: item.reporter_nickname ?? '',
      strategyId: item.strategy_id ?? '',
      strategyTitle: item.strategy_title ?? '',
      strategyAuthorId: item.strategy_author_id ?? '',
      strategyAuthorNickname: item.strategy_author_nickname ?? '',
      reason: item.reason ?? '',
      status: normalizeReportStatus(item.status),
      createdAt: item.created_at ?? null
    })),
    meta: {
      total: toNumber(response.meta?.total, 0),
      page: toNumber(response.meta?.page, page),
      perPage: toNumber(response.meta?.per_page, perPage)
    }
  }
}

export async function resolveReport(
  reportId: string,
  payload: AdminResolveReportPayload
): Promise<AdminResolveReportResult> {
  const response = await client.request<AdminResolveReportDto>({
    method: 'patch',
    url: `/v1/admin/reports/${reportId}/resolve`,
    data: {
      action: payload.action,
      admin_note: payload.adminNote
    }
  })

  return {
    reportId: response.report_id || '',
    status: normalizeReportStatus(response.status),
    action: normalizeResolveAction(response.action)
  }
}

export async function fetchUsers(params?: AdminUserListParams): Promise<AdminUserListResult> {
  const page = params?.page ?? 1
  const perPage = params?.perPage ?? 20
  const response = await client.requestWithMeta<AdminUserDto[]>({
    method: 'get',
    url: '/v1/admin/users',
    params: {
      search: params?.search ?? '',
      page,
      per_page: perPage
    }
  })

  return {
    data: (response.data ?? []).map((item) => ({
      userId: item.user_id ?? '',
      nickname: item.nickname ?? '',
      phone: item.phone ?? '',
      createdAt: item.created_at ?? null,
      planLevel: item.plan_level ?? '',
      isBanned: Boolean(item.is_banned)
    })),
    meta: {
      total: toNumber(response.meta?.total, 0),
      page: toNumber(response.meta?.page, page),
      perPage: toNumber(response.meta?.per_page, perPage)
    }
  }
}

export async function updateUserBanStatus(
  userId: string,
  payload: AdminUserBanStatusPayload
): Promise<AdminUserBanStatusResult> {
  const response = await client.request<AdminUserBanStatusDto>({
    method: 'patch',
    url: `/v1/admin/users/${userId}`,
    data: {
      is_banned: payload.isBanned,
      ban_reason: payload.banReason
    }
  })

  return {
    userId: response.user_id ?? '',
    isBanned: Boolean(response.is_banned)
  }
}

export async function fetchAuditLogs(filters?: AdminAuditLogFilters): Promise<AdminAuditLogListResult> {
  const page = filters?.page ?? 1
  const perPage = filters?.perPage ?? 20
  const response = await client.requestWithMeta<AdminAuditLogDto[]>({
    method: 'get',
    url: '/v1/admin/audit-logs',
    params: {
      operator_id: filters?.operatorId,
      action: filters?.action,
      target_type: filters?.targetType,
      target_id: filters?.targetId,
      date_from: filters?.dateFrom,
      date_to: filters?.dateTo,
      page,
      per_page: perPage
    }
  })

  return {
    data: (response.data ?? []).map((item) => ({
      id: item.id ?? '',
      operatorId: item.operator_id ?? '',
      operatorNickname: item.operator_nickname ?? '',
      action: item.action ?? '',
      targetType: item.target_type ?? '',
      targetId: item.target_id ?? '',
      details: item.details ?? {},
      createdAt: item.created_at ?? null
    })),
    meta: {
      total: toNumber(response.meta?.total, 0),
      page: toNumber(response.meta?.page, page),
      perPage: toNumber(response.meta?.per_page, perPage)
    }
  }
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

function normalizeReviewStatus(value: unknown): AdminReviewMutationResult['reviewStatus'] {
  return value === 'approved' || value === 'rejected' || value === 'pending' ? value : 'pending'
}

function normalizeReportStatus(value: unknown): AdminResolveReportResult['status'] {
  return value === 'reviewed' || value === 'dismissed' || value === 'pending' ? value : 'pending'
}

function normalizeResolveAction(value: unknown): AdminResolveReportResult['action'] {
  return value === 'dismiss' ? 'dismiss' : 'takedown'
}

function normalizeTerminateStatus(value: unknown): AdminTerminateJobResult['status'] {
  if (value !== 'terminated') {
    console.warn(`Unexpected terminate status: ${String(value)}, defaulting to 'terminated'`)
  }
  return 'terminated'
}

import { createHttpClient } from './http'

const client = createHttpClient()

export interface AdminHealthResponse {
  status: string
  scope: string
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

export function fetchAdminHealth(): Promise<AdminHealthResponse> {
  return client.request({
    method: 'get',
    url: '/v1/admin/health'
  })
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

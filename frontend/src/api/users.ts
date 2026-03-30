import { createHttpClient } from './http'
import type {
  PaginatedPosts,
  PaginatedStrategies,
  UserProfileResponse,
  UserPublicProfile
} from '../types/User'

const client = createHttpClient()

interface PaginationParams {
  page?: number
  per_page?: number
}

export interface UserQuotaResponse {
  plan_level: string
  used_count: number
  plan_limit: number | 'unlimited'
  remaining: number | 'unlimited'
  reset_at: string | null
  first_purchase_eligible: boolean
}

export function fetchProfile(): Promise<UserProfileResponse> {
  return client.request({
    method: 'get',
    url: '/v1/auth/profile',
  })
}

export function updateOnboardingCompleted(userId: string, completed: boolean): Promise<UserProfileResponse> {
  return client.request({
    method: 'put',
    url: `/v1/users/${userId}/onboarding-completed`,
    data: { completed },
  })
}

export function getUserProfile(userId: string): Promise<UserPublicProfile> {
  return client.request({
    method: 'get',
    url: `/v1/users/${userId}`
  })
}

export function getUserStrategies(userId: string, params?: PaginationParams): Promise<PaginatedStrategies> {
  return client.request({
    method: 'get',
    url: `/v1/users/${userId}/strategies`,
    params
  })
}

export function getUserPosts(userId: string, params?: PaginationParams): Promise<PaginatedPosts> {
  return client.request({
    method: 'get',
    url: `/v1/users/${userId}/posts`,
    params
  })
}

export function fetchMyQuota(): Promise<UserQuotaResponse> {
  return client.request({
    method: 'get',
    url: '/v1/users/me/quota'
  })
}

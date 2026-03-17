import { createHttpClient } from './http'
import type { UserProfileResponse } from '../types/User'

const client = createHttpClient()

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

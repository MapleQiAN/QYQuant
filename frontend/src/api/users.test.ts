import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as users from './users'

const { requestMock } = vi.hoisted(() => ({
  requestMock: vi.fn().mockResolvedValue({ ok: true })
}))

vi.mock('./http', () => ({
  createHttpClient: () => ({ request: requestMock })
}))

describe('users api', () => {
  beforeEach(() => {
    requestMock.mockClear()
    requestMock.mockResolvedValue({ ok: true })
  })

  it('calls current user profile endpoint', async () => {
    const data = await users.fetchProfile()

    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/auth/profile'
    })
  })

  it('calls onboarding completion endpoint', async () => {
    const data = await users.updateOnboardingCompleted('user-1', true)

    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'put',
      url: '/v1/users/user-1/onboarding-completed',
      data: { completed: true }
    })
  })

  it('calls public user profile endpoint and forwards 404 errors', async () => {
    const notFoundError = Object.assign(new Error('user not found'), { status: 404 })
    requestMock.mockRejectedValueOnce(notFoundError)

    await expect(users.getUserProfile('missing-user')).rejects.toBe(notFoundError)
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/users/missing-user'
    })
  })

  it('calls user strategies endpoint with pagination params', async () => {
    const data = await users.getUserStrategies('user-1', { page: 2, per_page: 10 })

    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/users/user-1/strategies',
      params: { page: 2, per_page: 10 }
    })
  })

  it('calls user posts endpoint with pagination params', async () => {
    const data = await users.getUserPosts('user-1', { page: 3, per_page: 5 })

    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/users/user-1/posts',
      params: { page: 3, per_page: 5 }
    })
  })

  it('calls get my quota endpoint', async () => {
    requestMock.mockResolvedValueOnce({
      plan_level: 'free',
      used_count: 3,
      plan_limit: 10,
      remaining: 7,
      reset_at: '2026-04-01T00:00:00+08:00',
    })

    const data = await users.fetchMyQuota()

    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/users/me/quota'
    })
    expect(data.plan_level).toBe('free')
    expect(data.remaining).toBe(7)
  })
})

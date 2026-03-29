import { beforeEach, describe, expect, it, vi } from 'vitest'
import { forgotPassword, login, loginWithPassword, registerWithPassword, resetPassword } from './auth'

const { postMock } = vi.hoisted(() => ({
  postMock: vi.fn(),
}))

vi.mock('axios', () => ({
  default: {
    create: () => ({
      post: postMock,
      interceptors: { response: { use: vi.fn() } },
    }),
  },
}))

describe('auth api', () => {
  beforeEach(() => {
    postMock.mockReset()
  })

  it('supports email login payload', async () => {
    postMock.mockResolvedValueOnce({
      data: {
        data: {
          user_id: 'user-1',
          email: 'al***@example.com',
          nickname: 'Alice',
          plan_level: 'free',
        },
        access_token: 'token-1',
      },
    })

    const result = await login({
      email: 'alice@example.com',
      password: 'Secret123!',
    })

    expect(postMock).toHaveBeenCalledWith('/v1/auth/login', {
      email: 'alice@example.com',
      password: 'Secret123!',
    })
    expect(result.access_token).toBe('token-1')
    expect(result.data.email).toBe('al***@example.com')
  })

  it('registers with password', async () => {
    postMock.mockResolvedValueOnce({
      data: {
        data: {
          user_id: 'user-1',
          email: 'pa***@example.com',
          nickname: 'Alice',
          plan_level: 'free',
        },
        access_token: 'token-1',
      },
    })

    const result = await registerWithPassword({
      email: 'alice@example.com',
      password: 'Secret123!',
      nickname: 'Alice',
    })

    expect(postMock).toHaveBeenCalledWith('/v1/auth/register', {
      email: 'alice@example.com',
      password: 'Secret123!',
      nickname: 'Alice',
    })
    expect(result.access_token).toBe('token-1')
  })

  it('logs in with password', async () => {
    postMock.mockResolvedValueOnce({
      data: {
        data: {
          user_id: 'user-1',
          email: 'pa***@example.com',
          nickname: 'Alice',
          plan_level: 'free',
        },
        access_token: 'token-1',
      },
    })

    await loginWithPassword({
      email: 'alice@example.com',
      password: 'Secret123!',
    })

    expect(postMock).toHaveBeenCalledWith('/v1/auth/login', {
      email: 'alice@example.com',
      password: 'Secret123!',
    })
  })

  it('requests forgot password email', async () => {
    postMock.mockResolvedValueOnce({ data: { data: { message: 'ok' } } })

    const result = await forgotPassword('alice@example.com')

    expect(postMock).toHaveBeenCalledWith('/v1/auth/forgot-password', {
      email: 'alice@example.com',
    })
    expect(result.message).toBe('ok')
  })

  it('submits password reset', async () => {
    postMock.mockResolvedValueOnce({ data: { data: { message: 'reset-ok' } } })

    const result = await resetPassword('token-1', 'NewSecret123!')

    expect(postMock).toHaveBeenCalledWith('/v1/auth/reset-password', {
      token: 'token-1',
      password: 'NewSecret123!',
    })
    expect(result.message).toBe('reset-ok')
  })
})

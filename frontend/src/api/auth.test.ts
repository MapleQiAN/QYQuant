import { beforeEach, describe, expect, it, vi } from 'vitest'
import { login, loginWithPassword, registerWithPassword, sendCode } from './auth'

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

  it('sends phone verification code with legacy signature', async () => {
    postMock.mockResolvedValueOnce({ data: { data: { message: 'ok' } } })

    const data = await sendCode('13800138000')

    expect(data).toEqual({ message: 'ok' })
    expect(postMock).toHaveBeenCalledWith('/v1/auth/send-code', { phone: '13800138000' })
  })

  it('sends email verification code', async () => {
    postMock.mockResolvedValueOnce({ data: { data: { message: 'ok' } } })

    await sendCode({ email: 'alice@example.com' })

    expect(postMock).toHaveBeenCalledWith('/v1/auth/send-code', { email: 'alice@example.com' })
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
      code: '123456',
      nickname: 'Alice',
    })

    expect(postMock).toHaveBeenCalledWith('/v1/auth/login', {
      email: 'alice@example.com',
      code: '123456',
      nickname: 'Alice',
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

    expect(postMock).toHaveBeenCalledWith('/v1/auth/register/password', {
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

    expect(postMock).toHaveBeenCalledWith('/v1/auth/login/password', {
      email: 'alice@example.com',
      password: 'Secret123!',
    })
  })
})

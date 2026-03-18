import { beforeEach, describe, it, expect, vi } from 'vitest'
import { createHttpClient } from './http'

const { requestMock } = vi.hoisted(() => ({
  requestMock: vi.fn()
}))

vi.mock('axios', () => {
  return {
    default: {
      create: () => ({
        request: requestMock,
        interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } }
      })
    }
  }
})

describe('http client', () => {
  beforeEach(() => {
    requestMock.mockReset()
  })

  it('retries GET requests by default', async () => {
    requestMock
      .mockRejectedValueOnce(new Error('temporary'))
      .mockResolvedValueOnce({
        data: { code: 0, message: 'ok', data: { ok: true } }
      })

    const client = createHttpClient()
    const data = await client.request({ method: 'get', url: '/ping' })

    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledTimes(2)
  })

  it('does not retry POST requests by default', async () => {
    requestMock.mockRejectedValueOnce(new Error('boom'))

    const client = createHttpClient()
    await expect(client.request({ method: 'post', url: '/strategies' })).rejects.toThrow('boom')
    expect(requestMock).toHaveBeenCalledTimes(1)
  })

  it('allows explicit retry opt-in for POST', async () => {
    requestMock
      .mockRejectedValueOnce(new Error('temporary'))
      .mockResolvedValueOnce({
        data: { code: 0, message: 'ok', data: { ok: true } }
      })

    const client = createHttpClient()
    const data = await client.request({ method: 'post', url: '/strategies', retry: true } as any)

    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledTimes(2)
  })

  it('unwraps api envelope', async () => {
    requestMock.mockResolvedValueOnce({
      data: {
        code: 0,
        message: 'ok',
        data: { ok: true }
      }
    })

    const client = createHttpClient()
    const data = await client.request({ method: 'get', url: '/ping' })
    expect(data).toEqual({ ok: true })
  })

  it('returns data with meta when requested', async () => {
    requestMock.mockResolvedValueOnce({
      data: {
        code: 0,
        message: 'ok',
        data: { ok: true },
        meta: { total: 24, page: 2, page_size: 20 }
      }
    })

    const client = createHttpClient()
    const result = await client.requestWithMeta({ method: 'get', url: '/v1/marketplace/strategies' })
    expect(result).toEqual({
      data: { ok: true },
      meta: { total: 24, page: 2, page_size: 20 }
    })
  })
})

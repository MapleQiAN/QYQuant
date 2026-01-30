import { describe, it, expect, vi } from 'vitest'
import { createHttpClient } from './http'

vi.mock('axios', () => {
  return {
    default: {
      create: () => ({
        request: vi.fn().mockResolvedValue({ data: { ok: true } }),
        interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } }
      })
    }
  }
})

describe('http client', () => {
  it('returns data from request', async () => {
    const client = createHttpClient()
    const data = await client.request({ method: 'get', url: '/ping' })
    expect(data).toEqual({ ok: true })
  })
})

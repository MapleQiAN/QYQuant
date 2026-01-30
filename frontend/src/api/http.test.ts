import { describe, it, expect, vi } from 'vitest'
import { createHttpClient } from './http'

vi.mock('axios', () => {
  return {
    default: {
      create: () => ({
        request: vi.fn().mockResolvedValue({
          data: { code: 0, message: 'ok', data: { ok: true } }
        }),
        interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } }
      })
    }
  }
})

describe('http client', () => {
  it('unwraps api envelope', async () => {
    const client = createHttpClient()
    const data = await client.request({ method: 'get', url: '/ping' })
    expect(data).toEqual({ ok: true })
  })
})

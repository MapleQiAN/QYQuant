import { describe, it, expect, vi } from 'vitest'
import * as strategies from './strategies'

vi.mock('./http', () => ({
  createHttpClient: () => ({ request: vi.fn().mockResolvedValue({ ok: true }) }),
}))

describe('strategies api', () => {
  it('calls runtime descriptor endpoint', async () => {
    const data = await strategies.fetchRuntimeDescriptor('strategy-id')
    expect(data).toEqual({ ok: true })
  })
})


import { beforeEach, describe, it, expect, vi } from 'vitest'
import * as strategies from './strategies'

const { requestMock } = vi.hoisted(() => ({
  requestMock: vi.fn().mockResolvedValue({ ok: true })
}))

vi.mock('./http', () => ({
  createHttpClient: () => ({ request: requestMock }),
}))

describe('strategies api', () => {
  beforeEach(() => {
    requestMock.mockClear()
  })

  it('calls strategy library endpoint', async () => {
    const data = await strategies.fetchStrategies({ page: 2, perPage: 10 })
    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/strategies/',
      params: { page: 2, per_page: 10 }
    })
  })

  it('calls delete strategy endpoint', async () => {
    const data = await strategies.deleteStrategy('strategy-id')
    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'delete',
      url: '/v1/strategies/strategy-id'
    })
  })

  it('calls import strategy endpoint', async () => {
    const file = new File(['package'], 'demo.qys', { type: 'application/octet-stream' })
    const data = await strategies.importStrategy(file)
    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledTimes(1)
    expect(requestMock.mock.calls[0][0].method).toBe('post')
    expect(requestMock.mock.calls[0][0].url).toBe('/v1/strategies/import')
  })

  it('calls runtime descriptor endpoint', async () => {
    const data = await strategies.fetchRuntimeDescriptor('strategy-id')
    expect(data).toEqual({ ok: true })
  })
})


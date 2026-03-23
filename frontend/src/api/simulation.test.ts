import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as simulation from './simulation'

const { requestMock } = vi.hoisted(() => ({
  requestMock: vi.fn().mockResolvedValue({ ok: true })
}))

vi.mock('./http', () => ({
  createHttpClient: () => ({ request: requestMock })
}))

describe('simulation api', () => {
  beforeEach(() => {
    requestMock.mockClear()
    requestMock.mockResolvedValue({ ok: true })
  })

  it('calls disclaimer accept endpoint', async () => {
    const data = await simulation.acceptSimDisclaimer()

    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'post',
      url: '/v1/simulation/disclaimer/accept'
    })
  })

  it('calls create bot endpoint', async () => {
    const data = await simulation.createSimBot({
      strategy_id: 'strategy-1',
      initial_capital: 100000,
    })

    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'post',
      url: '/v1/simulation/bots',
      data: {
        strategy_id: 'strategy-1',
        initial_capital: 100000,
      }
    })
  })

  it('calls get bots endpoint', async () => {
    await simulation.getSimBots()

    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/simulation/bots',
    })
  })

  it('calls get positions endpoint with bot id', async () => {
    await simulation.getSimPositions('bot-42')

    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/simulation/bots/bot-42/positions',
    })
  })
})

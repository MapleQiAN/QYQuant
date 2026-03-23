import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useSimulationStore } from './useSimulationStore'

const { acceptSimDisclaimerMock, createSimBotMock } = vi.hoisted(() => ({
  acceptSimDisclaimerMock: vi.fn().mockResolvedValue(undefined),
  createSimBotMock: vi.fn().mockResolvedValue({
    id: 'bot-1',
    strategy_id: 'strategy-1',
    initial_capital: '100000.00',
    status: 'active',
    created_at: '2026-03-23T16:00:00+08:00',
  }),
}))

vi.mock('../api/simulation', () => ({
  acceptSimDisclaimer: acceptSimDisclaimerMock,
  createSimBot: createSimBotMock,
}))

describe('simulation store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    acceptSimDisclaimerMock.mockClear()
    createSimBotMock.mockClear()
  })

  it('accepts disclaimer via api', async () => {
    const store = useSimulationStore()

    await store.acceptDisclaimer()

    expect(acceptSimDisclaimerMock).toHaveBeenCalledTimes(1)
  })

  it('creates a bot and prepends it to state', async () => {
    const store = useSimulationStore()

    const bot = await store.createBot({
      strategy_id: 'strategy-1',
      initial_capital: 100000,
    })

    expect(createSimBotMock).toHaveBeenCalledWith({
      strategy_id: 'strategy-1',
      initial_capital: 100000,
    })
    expect(bot.id).toBe('bot-1')
    expect(store.bots[0]?.id).toBe('bot-1')
    expect(store.error).toBeNull()
  })

  it('captures backend error code when slot limit is reached', async () => {
    const store = useSimulationStore()
    const error = {
      status: 403,
      code: 'SIMULATION_SLOT_LIMIT_REACHED',
      message: 'Current plan supports at most 1 active simulation bots',
    }
    createSimBotMock.mockRejectedValueOnce(error)

    await expect(store.createBot({
      strategy_id: 'strategy-1',
      initial_capital: 100000,
    })).rejects.toBe(error)

    expect(store.error).toBe('Current plan supports at most 1 active simulation bots')
    expect(store.errorCode).toBe('SIMULATION_SLOT_LIMIT_REACHED')
  })
})

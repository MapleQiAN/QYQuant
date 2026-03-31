import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useSimulationStore } from './useSimulationStore'

const {
  acceptSimDisclaimerMock,
  createSimBotMock,
  getSimBotsMock,
  getSimPositionsMock,
  patchSimBotMock,
  deleteSimBotMock,
  toastSuccessMock,
} = vi.hoisted(() => ({
  acceptSimDisclaimerMock: vi.fn().mockResolvedValue(undefined),
  createSimBotMock: vi.fn().mockResolvedValue({
    id: 'bot-1',
    strategy_id: 'strategy-1',
    strategy_name: '双均线策略',
    initial_capital: '100000.00',
    status: 'active',
    created_at: '2026-03-23T16:00:00+08:00',
  }),
  getSimBotsMock: vi.fn().mockResolvedValue([]),
  getSimPositionsMock: vi.fn().mockResolvedValue([]),
  patchSimBotMock: vi.fn().mockResolvedValue(undefined),
  deleteSimBotMock: vi.fn().mockResolvedValue(undefined),
  toastSuccessMock: vi.fn(),
}))

vi.mock('../api/simulation', () => ({
  acceptSimDisclaimer: acceptSimDisclaimerMock,
  createSimBot: createSimBotMock,
  getSimBots: getSimBotsMock,
  getSimPositions: getSimPositionsMock,
  patchSimBot: patchSimBotMock,
  deleteSimBot: deleteSimBotMock,
}))

vi.mock('../lib/toast', () => ({
  toast: {
    success: toastSuccessMock,
  }
}))

describe('simulation store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    acceptSimDisclaimerMock.mockClear()
    createSimBotMock.mockClear()
    getSimBotsMock.mockClear()
    getSimPositionsMock.mockClear()
    patchSimBotMock.mockClear()
    deleteSimBotMock.mockClear()
    toastSuccessMock.mockClear()
  })

  it('accepts disclaimer via api', async () => {
    const store = useSimulationStore()

    await store.acceptDisclaimer()

    expect(acceptSimDisclaimerMock).toHaveBeenCalledTimes(1)
    expect(toastSuccessMock).toHaveBeenCalledWith('免责声明已确认')
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
    expect(toastSuccessMock).toHaveBeenCalledWith('模拟机器人已创建')
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

  it('fetchBots updates state.bots from api', async () => {
    const bots = [
      {
        id: 'bot-1',
        strategy_id: 'strategy-1',
        strategy_name: '双均线策略',
        initial_capital: '50000.00',
        status: 'active' as const,
        created_at: '2026-03-23T16:00:00+08:00',
      },
    ]
    getSimBotsMock.mockResolvedValueOnce(bots)

    const store = useSimulationStore()
    await store.fetchBots()

    expect(getSimBotsMock).toHaveBeenCalledTimes(1)
    expect(store.bots).toEqual(bots)
    expect(store.isLoading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchBots sets error on failure', async () => {
    getSimBotsMock.mockRejectedValueOnce(new Error('网络错误'))

    const store = useSimulationStore()
    await store.fetchBots()

    expect(store.error).toBe('网络错误')
    expect(store.bots).toEqual([])
  })

  it('fetchPositions calls api and returns positions', async () => {
    const positions = [
      {
        symbol: '000001.XSHG',
        quantity: '1000.0000',
        avg_cost: '52.0000',
        updated_at: '2026-03-22T16:00:00+08:00',
      },
    ]
    getSimPositionsMock.mockResolvedValueOnce(positions)

    const store = useSimulationStore()
    const result = await store.fetchPositions('bot-1')

    expect(getSimPositionsMock).toHaveBeenCalledWith('bot-1')
    expect(result).toEqual(positions)
  })

  it('updates bot state for pause, resume, and delete with feedback', async () => {
    const store = useSimulationStore()
    store.bots = [
      {
        id: 'bot-1',
        strategy_id: 'strategy-1',
        strategy_name: '双均线策略',
        initial_capital: '50000.00',
        status: 'active',
        created_at: '2026-03-23T16:00:00+08:00',
      },
    ]

    await store.pauseBot('bot-1')
    await store.resumeBot('bot-1')
    await store.deleteBot('bot-1')

    expect(patchSimBotMock).toHaveBeenNthCalledWith(1, 'bot-1', { status: 'paused' })
    expect(patchSimBotMock).toHaveBeenNthCalledWith(2, 'bot-1', { status: 'active' })
    expect(deleteSimBotMock).toHaveBeenCalledWith('bot-1')
    expect(store.bots).toEqual([])
    expect(toastSuccessMock).toHaveBeenNthCalledWith(1, '模拟机器人已暂停')
    expect(toastSuccessMock).toHaveBeenNthCalledWith(2, '模拟机器人已恢复')
    expect(toastSuccessMock).toHaveBeenNthCalledWith(3, '模拟机器人已删除')
  })
})

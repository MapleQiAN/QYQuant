import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { usePresetsStore } from './usePresetsStore'

const {
  fetchStrategyPresetsMock,
  createStrategyPresetMock,
  deleteStrategyPresetMock,
} = vi.hoisted(() => ({
  fetchStrategyPresetsMock: vi.fn(),
  createStrategyPresetMock: vi.fn(),
  deleteStrategyPresetMock: vi.fn(),
}))

vi.mock('../api/strategies', () => ({
  fetchStrategyPresets: fetchStrategyPresetsMock,
  createStrategyPreset: createStrategyPresetMock,
  deleteStrategyPreset: deleteStrategyPresetMock,
}))

describe('usePresetsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    fetchStrategyPresetsMock.mockReset()
    createStrategyPresetMock.mockReset()
    deleteStrategyPresetMock.mockReset()
  })

  it('loads presets for a strategy', async () => {
    fetchStrategyPresetsMock.mockResolvedValue([
      { id: 'preset-1', name: '稳健版', parameters: { window: 20 } },
    ])

    const store = usePresetsStore()
    await store.loadPresets('strategy-1')

    expect(fetchStrategyPresetsMock).toHaveBeenCalledWith('strategy-1')
    expect(store.error).toBeNull()
    expect(store.presets).toHaveLength(1)
  })

  it('creates and removes presets', async () => {
    createStrategyPresetMock.mockResolvedValue({
      id: 'preset-2',
      name: '激进版',
      parameters: { window: 10 },
    })
    deleteStrategyPresetMock.mockResolvedValue({ deletedId: 'preset-2' })

    const store = usePresetsStore()
    await store.savePreset('strategy-1', {
      name: '激进版',
      parameters: { window: 10 },
    })

    expect(store.presets[0]?.id).toBe('preset-2')

    await store.removePreset('strategy-1', 'preset-2')
    expect(deleteStrategyPresetMock).toHaveBeenCalledWith('strategy-1', 'preset-2')
    expect(store.presets).toEqual([])
  })
})

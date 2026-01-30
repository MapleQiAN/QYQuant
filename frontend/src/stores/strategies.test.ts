import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useStrategiesStore } from './strategies'

vi.mock('../api/strategies', () => ({
  fetchRecent: vi.fn().mockResolvedValue([{ id: 'str-1' }])
}))

describe('strategies store', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('loads recent strategies and clears error', async () => {
    const store = useStrategiesStore()
    await store.loadRecent()
    expect(store.error).toBeNull()
    expect(store.recent.length).toBe(1)
  })
})

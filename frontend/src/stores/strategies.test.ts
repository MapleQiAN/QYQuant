import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useStrategiesStore } from './strategies'

vi.mock('../api/strategies', () => ({
  fetchRecent: vi.fn().mockResolvedValue([{ id: 'str-1' }]),
  fetchStrategies: vi.fn().mockResolvedValue({
    items: [{ id: 'str-1' }, { id: 'str-2' }],
    page: 2,
    perPage: 10,
    total: 12
  })
}))

describe('strategies store', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('loads recent strategies and clears error', async () => {
    const store = useStrategiesStore()
    await store.loadRecent()
    expect(store.error).toBeNull()
    expect(store.recent.length).toBe(1)
  })

  it('loads strategy library page', async () => {
    const store = useStrategiesStore()
    await store.loadLibrary({ page: 2, perPage: 10 })
    expect(store.error).toBeNull()
    expect(store.library.length).toBe(2)
    expect(store.pagination.page).toBe(2)
    expect(store.pagination.total).toBe(12)
  })
})

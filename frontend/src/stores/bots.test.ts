import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useBotsStore } from './bots'

vi.mock('../api/bots', () => ({
  fetchRecent: vi.fn().mockResolvedValue([{ id: 'bot-1' }])
}))

describe('bots store', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('loads recent bots and clears error', async () => {
    const store = useBotsStore()
    await store.loadRecent()
    expect(store.error).toBeNull()
    expect(store.recent.length).toBe(1)
  })
})

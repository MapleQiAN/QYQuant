import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useForumStore } from './forum'

vi.mock('../api/forum', () => ({
  fetchHot: vi.fn().mockResolvedValue([{ id: 'post-1' }])
}))

describe('forum store', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('loads hot posts and clears error', async () => {
    const store = useForumStore()
    await store.loadHot()
    expect(store.error).toBeNull()
    expect(store.posts.length).toBe(1)
  })
})

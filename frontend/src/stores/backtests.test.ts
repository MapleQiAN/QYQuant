import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useBacktestsStore } from './backtests'

vi.mock('../api/backtests', () => ({
  fetchLatest: vi.fn().mockResolvedValue({ summary: { totalReturn: 1 }, kline: [], trades: [] })
}))

describe('backtests store', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('loads latest and clears error', async () => {
    const store = useBacktestsStore()
    await store.loadLatest()
    expect(store.error).toBeNull()
    expect(store.latest).not.toBeNull()
  })
})

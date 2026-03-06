import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useBacktestsStore } from './backtests'

const { fetchLatestMock } = vi.hoisted(() => ({
  fetchLatestMock: vi.fn().mockResolvedValue({ summary: { totalReturn: 1 }, kline: [], trades: [] })
}))

vi.mock('../api/backtests', () => ({
  fetchLatest: fetchLatestMock
}))

describe('backtests store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    fetchLatestMock.mockClear()
  })

  it('loads latest and clears error', async () => {
    const store = useBacktestsStore()
    await store.loadLatest()
    expect(store.error).toBeNull()
    expect(store.latest).not.toBeNull()
  })

  it('passes interval options when loading latest', async () => {
    const store = useBacktestsStore()
    await store.loadLatest('XAUUSD', { interval: '1h', limit: 200 })
    expect(fetchLatestMock).toHaveBeenCalledWith('XAUUSD', { interval: '1h', limit: 200 })
  })
})

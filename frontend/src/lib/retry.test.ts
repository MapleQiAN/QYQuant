import { describe, it, expect, vi, afterEach } from 'vitest'
import { retry } from './retry'

describe('retry', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('retries with exponential backoff and succeeds', async () => {
    const fn = vi.fn()
      .mockRejectedValueOnce(new Error('fail'))
      .mockRejectedValueOnce(new Error('fail'))
      .mockResolvedValueOnce('ok')

    vi.useFakeTimers()
    const promise = retry(fn, { retries: 3, delays: [200, 400, 800] })

    await vi.advanceTimersByTimeAsync(200)
    await vi.advanceTimersByTimeAsync(400)

    await expect(promise).resolves.toBe('ok')
    expect(fn).toHaveBeenCalledTimes(3)
  })
})

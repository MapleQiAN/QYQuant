import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from './user'

const { fetchProfileMock } = vi.hoisted(() => ({
  fetchProfileMock: vi.fn(),
}))

vi.mock('../api/users', () => ({
  fetchProfile: fetchProfileMock,
  updateOnboardingCompleted: vi.fn(),
}))

describe('user store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    fetchProfileMock.mockReset()
    localStorage.clear()
  })

  it('updates locale', () => {
    const store = useUserStore()
    store.setLocale('zh')
    expect(store.locale).toBe('zh')
  })

  it('keeps token and marks profile settled when profile loading fails without auth status', async () => {
    localStorage.setItem('qyquant-token', 'token-1')
    fetchProfileMock.mockRejectedValueOnce({ status: 500, message: 'server unavailable' })

    const store = useUserStore()
    await store.loadProfile()

    expect(localStorage.getItem('qyquant-token')).toBe('token-1')
    expect(store.profileLoaded).toBe(true)
    expect(store.profileLoading).toBe(false)
  })

  it('clears token when profile loading fails with unauthorized status', async () => {
    localStorage.setItem('qyquant-token', 'token-1')
    fetchProfileMock.mockRejectedValueOnce({ status: 401, message: 'unauthorized' })

    const store = useUserStore()
    await store.loadProfile()

    expect(localStorage.getItem('qyquant-token')).toBeNull()
    expect(store.profileLoaded).toBe(true)
    expect(store.profileLoading).toBe(false)
  })
})

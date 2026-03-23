import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useUserProfileStore } from './useUserProfileStore'

const {
  getUserProfileMock,
  getUserStrategiesMock,
  getUserPostsMock
} = vi.hoisted(() => ({
  getUserProfileMock: vi.fn(),
  getUserStrategiesMock: vi.fn(),
  getUserPostsMock: vi.fn()
}))

vi.mock('../api/users', async () => {
  const actual = await vi.importActual<typeof import('../api/users')>('../api/users')
  return {
    ...actual,
    getUserProfile: getUserProfileMock,
    getUserStrategies: getUserStrategiesMock,
    getUserPosts: getUserPostsMock
  }
})

describe('useUserProfileStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    getUserProfileMock.mockReset()
    getUserStrategiesMock.mockReset()
    getUserPostsMock.mockReset()
  })

  it('fetchProfile stores the public profile by id', async () => {
    getUserProfileMock.mockResolvedValue({
      id: 'user-1',
      nickname: 'Quant Alice',
      avatar_url: 'https://example.com/avatar.png',
      bio: 'Systematic trader',
      is_banned: false,
      created_at: '2026-03-20T20:00:00+08:00'
    })

    const store = useUserProfileStore()
    const result = await store.fetchProfile('user-1')

    expect(getUserProfileMock).toHaveBeenCalledWith('user-1')
    expect(result.nickname).toBe('Quant Alice')
    expect(store.profileById['user-1']?.bio).toBe('Systematic trader')
    expect(store.loadingProfile).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchProfile stores error and rethrows failures', async () => {
    getUserProfileMock.mockRejectedValue(new Error('user not found'))

    const store = useUserProfileStore()

    await expect(store.fetchProfile('missing-user')).rejects.toThrow('user not found')
    expect(store.error).toBe('user not found')
    expect(store.loadingProfile).toBe(false)
  })

  it('fetchUserStrategies appends paginated results', async () => {
    getUserStrategiesMock
      .mockResolvedValueOnce({
        items: [
          {
            id: 'strategy-1',
            name: 'Alpha',
            category: 'trend',
            returns: 12.4,
            max_drawdown: -5.1,
            win_rate: 58,
            tags: ['alpha']
          }
        ],
        total: 2,
        page: 1,
        per_page: 20
      })
      .mockResolvedValueOnce({
        items: [
          {
            id: 'strategy-2',
            name: 'Beta',
            category: 'swing',
            returns: 8.9,
            max_drawdown: -3.2,
            win_rate: 61,
            tags: ['beta']
          }
        ],
        total: 2,
        page: 2,
        per_page: 20
      })

    const store = useUserProfileStore()
    await store.fetchUserStrategies('user-1', 1)
    await store.fetchUserStrategies('user-1', 2)

    expect(getUserStrategiesMock).toHaveBeenNthCalledWith(1, 'user-1', { page: 1, per_page: 20 })
    expect(getUserStrategiesMock).toHaveBeenNthCalledWith(2, 'user-1', { page: 2, per_page: 20 })
    expect(store.strategiesByUserId['user-1'].items.map((item: any) => item.id)).toEqual(['strategy-1', 'strategy-2'])
    expect(store.strategiesByUserId['user-1'].total).toBe(2)
    expect(store.loadingStrategies).toBe(false)
  })

  it('fetchUserPosts stores empty results', async () => {
    getUserPostsMock.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      per_page: 20
    })

    const store = useUserProfileStore()
    const result = await store.fetchUserPosts('user-1')

    expect(getUserPostsMock).toHaveBeenCalledWith('user-1', { page: 1, per_page: 20 })
    expect(result.items).toEqual([])
    expect(store.postsByUserId['user-1']).toEqual({
      items: [],
      total: 0,
      page: 1,
      per_page: 20
    })
    expect(store.loadingPosts).toBe(false)
  })
})

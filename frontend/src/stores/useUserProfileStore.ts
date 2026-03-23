import { defineStore } from 'pinia'
import { getUserPosts, getUserProfile, getUserStrategies } from '../api/users'
import type {
  PaginatedPosts,
  PaginatedStrategies,
  UserPublicProfile
} from '../types/User'

function mergePaginatedItems<T extends { id: string }>(
  current: T[],
  incoming: T[]
): T[] {
  const items = [...current]
  const seen = new Set(current.map((item) => item.id))

  for (const item of incoming) {
    if (seen.has(item.id)) {
      continue
    }
    items.push(item)
    seen.add(item.id)
  }

  return items
}

export const useUserProfileStore = defineStore('userProfile', {
  state: () => ({
    profileById: {} as Record<string, UserPublicProfile>,
    strategiesByUserId: {} as Record<string, PaginatedStrategies>,
    postsByUserId: {} as Record<string, PaginatedPosts>,
    loadingProfile: false,
    loadingStrategies: false,
    loadingPosts: false,
    error: null as string | null
  }),
  actions: {
    async fetchProfile(userId: string) {
      this.loadingProfile = true
      this.error = null
      try {
        const profile = await getUserProfile(userId)
        this.profileById[userId] = profile
        return profile
      } catch (error: any) {
        this.error = error?.message || 'Failed to load user profile'
        throw error
      } finally {
        this.loadingProfile = false
      }
    },
    async fetchUserStrategies(userId: string, page = 1, perPage = 20) {
      this.loadingStrategies = true
      this.error = null
      try {
        const response = await getUserStrategies(userId, { page, per_page: perPage })
        const current = this.strategiesByUserId[userId]
        this.strategiesByUserId[userId] = page === 1 || !current
          ? response
          : {
              ...response,
              items: mergePaginatedItems(current.items, response.items)
            }
        return this.strategiesByUserId[userId]
      } catch (error: any) {
        this.error = error?.message || 'Failed to load user strategies'
        throw error
      } finally {
        this.loadingStrategies = false
      }
    },
    async fetchUserPosts(userId: string, page = 1, perPage = 20) {
      this.loadingPosts = true
      this.error = null
      try {
        const response = await getUserPosts(userId, { page, per_page: perPage })
        const current = this.postsByUserId[userId]
        this.postsByUserId[userId] = page === 1 || !current
          ? response
          : {
              ...response,
              items: mergePaginatedItems(current.items, response.items)
            }
        return this.postsByUserId[userId]
      } catch (error: any) {
        this.error = error?.message || 'Failed to load user posts'
        throw error
      } finally {
        this.loadingPosts = false
      }
    }
  }
})

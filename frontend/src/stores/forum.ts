import { defineStore } from 'pinia'
import { getPosts } from '../api/community'
import type { CommunityPost } from '../types/community'

export const useForumStore = defineStore('forum', {
  state: () => ({
    posts: [] as CommunityPost[],
    loading: false,
    error: null as string | null
  }),
  actions: {
    async loadHot() {
      this.loading = true
      this.error = null
      try {
        const res = await getPosts({ page: 1, per_page: 5 })
        this.posts = res.items
      } catch (error: any) {
        this.error = error?.message || 'Failed to load posts'
      } finally {
        this.loading = false
      }
    }
  }
})

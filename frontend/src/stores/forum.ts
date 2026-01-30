import { defineStore } from 'pinia'
import { fetchHot } from '../api/forum'
import type { Post } from '../types/Post'

export const useForumStore = defineStore('forum', {
  state: () => ({
    posts: [] as Post[],
    loading: false,
    error: null as string | null
  }),
  actions: {
    async loadHot() {
      this.loading = true
      this.error = null
      try {
        this.posts = await fetchHot()
      } catch (error: any) {
        this.error = error?.message || 'Failed to load posts'
      } finally {
        this.loading = false
      }
    }
  }
})

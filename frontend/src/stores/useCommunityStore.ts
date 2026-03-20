import { defineStore } from 'pinia'
import {
  collectPost as apiCollectPost,
  createComment as apiCreateComment,
  createPost as apiCreatePost,
  getComments,
  getPostDetail,
  getPosts,
  likePost as apiLikePost
} from '../api/community'
import type { CommunityComment, CommunityPost } from '../types/community'
import { useUserStore } from './user'

function upsertUniquePosts(posts: CommunityPost[]): CommunityPost[] {
  const seen = new Set<string>()
  return posts.filter((post) => {
    if (seen.has(post.id)) {
      return false
    }
    seen.add(post.id)
    return true
  })
}

function upsertUniqueComments(comments: CommunityComment[]): CommunityComment[] {
  const seen = new Set<string>()
  return comments.filter((comment) => {
    if (seen.has(comment.id)) {
      return false
    }
    seen.add(comment.id)
    return true
  })
}

export const useCommunityStore = defineStore('community', {
  state: () => ({
    posts: [] as CommunityPost[],
    postsTotal: 0,
    currentPage: 1,
    perPage: 20,
    hasMorePosts: true,
    postDetailById: {} as Record<string, CommunityPost>,
    likedPostIds: {} as Record<string, boolean>,
    collectedPostIds: {} as Record<string, boolean>,
    commentsByPostId: {} as Record<string, CommunityComment[]>,
    commentTotalsByPostId: {} as Record<string, number>,
    commentPagesByPostId: {} as Record<string, number>,
    loadingFeed: false,
    loadingPostDetail: false,
    submittingPost: false,
    submittingComment: false,
    error: null as string | null
  }),
  actions: {
    syncPostFlags(post: CommunityPost) {
      if (post.liked) {
        this.likedPostIds[post.id] = true
      } else {
        delete this.likedPostIds[post.id]
      }
      if (post.collected) {
        this.collectedPostIds[post.id] = true
      } else {
        delete this.collectedPostIds[post.id]
      }
    },
    patchPost(postId: string, updater: (post: CommunityPost) => void) {
      const listPost = this.posts.find((post) => post.id === postId)
      if (listPost) {
        updater(listPost)
      }
      const detailPost = this.postDetailById[postId]
      if (detailPost) {
        updater(detailPost)
      }
    },
    async fetchPosts(page = 1) {
      this.loadingFeed = true
      this.error = null
      try {
        const response = await getPosts({ page, per_page: this.perPage })
        response.items.forEach((post) => this.syncPostFlags(post))
        this.posts = page === 1
          ? response.items
          : upsertUniquePosts([...this.posts, ...response.items])
        this.postsTotal = response.total
        this.currentPage = response.page
        this.perPage = response.per_page
        this.hasMorePosts = response.page * response.per_page < response.total
      } catch (error: any) {
        this.error = error?.message || 'Failed to load community posts'
        throw error
      } finally {
        this.loadingFeed = false
      }
    },
    async createPost(content: string, strategyId?: string) {
      this.submittingPost = true
      this.error = null
      try {
        const post = await apiCreatePost({
          content,
          strategy_id: strategyId
        })
        this.syncPostFlags(post)
        this.posts = [post, ...this.posts]
        this.postsTotal += 1
        return post
      } catch (error: any) {
        this.error = error?.message || 'Failed to create post'
        throw error
      } finally {
        this.submittingPost = false
      }
    },
    async fetchPostDetail(postId: string) {
      this.loadingPostDetail = true
      this.error = null
      try {
        const post = await getPostDetail(postId)
        this.syncPostFlags(post)
        this.postDetailById[postId] = post
        return post
      } catch (error: any) {
        this.error = error?.message || 'Failed to load post detail'
        throw error
      } finally {
        this.loadingPostDetail = false
      }
    },
    async toggleLike(postId: string) {
      const wasLiked = Boolean(this.likedPostIds[postId])
      const delta = wasLiked ? -1 : 1

      this.patchPost(postId, (post) => {
        post.likes_count = Math.max(0, (post.likes_count || 0) + delta)
        post.liked = !wasLiked
      })
      if (wasLiked) {
        delete this.likedPostIds[postId]
      } else {
        this.likedPostIds[postId] = true
      }

      try {
        const result = await apiLikePost(postId)
        this.patchPost(postId, (post) => {
          post.likes_count = result.likes_count
          post.liked = result.liked
        })
        if (result.liked) {
          this.likedPostIds[postId] = true
        } else {
          delete this.likedPostIds[postId]
        }
        return result
      } catch (error: any) {
        this.patchPost(postId, (post) => {
          post.likes_count = Math.max(0, (post.likes_count || 0) - delta)
          post.liked = wasLiked
        })
        if (wasLiked) {
          this.likedPostIds[postId] = true
        } else {
          delete this.likedPostIds[postId]
        }
        this.error = error?.message || 'Failed to like post'
        throw error
      }
    },
    async toggleCollect(postId: string) {
      const wasCollected = Boolean(this.collectedPostIds[postId])

      this.patchPost(postId, (post) => {
        post.collected = !wasCollected
      })
      if (wasCollected) {
        delete this.collectedPostIds[postId]
      } else {
        this.collectedPostIds[postId] = true
      }

      try {
        const result = await apiCollectPost(postId)
        this.patchPost(postId, (post) => {
          post.collected = result.collected
        })
        if (result.collected) {
          this.collectedPostIds[postId] = true
        } else {
          delete this.collectedPostIds[postId]
        }
        return result
      } catch (error: any) {
        this.patchPost(postId, (post) => {
          post.collected = wasCollected
        })
        if (wasCollected) {
          this.collectedPostIds[postId] = true
        } else {
          delete this.collectedPostIds[postId]
        }
        this.error = error?.message || 'Failed to collect post'
        throw error
      }
    },
    async fetchComments(postId: string, page = 1) {
      this.error = null
      try {
        const response = await getComments(postId, { page, per_page: 20 })
        this.commentsByPostId[postId] = page === 1
          ? response.items
          : upsertUniqueComments([...(this.commentsByPostId[postId] || []), ...response.items])
        this.commentTotalsByPostId[postId] = response.total
        this.commentPagesByPostId[postId] = response.page
        return response
      } catch (error: any) {
        this.error = error?.message || 'Failed to load comments'
        throw error
      }
    },
    async createComment(postId: string, content: string) {
      const userStore = useUserStore()
      if (!userStore.profile.id) {
        throw new Error('Authentication required')
      }

      this.submittingComment = true
      this.error = null

      const tempId = `temp-${Date.now()}`
      const tempComment: CommunityComment = {
        id: tempId,
        content,
        user_id: userStore.profile.id,
        created_at: new Date().toISOString(),
        author: {
          nickname: userStore.profile.nickname || userStore.profile.name,
          avatar_url: userStore.profile.avatar_url || ''
        }
      }

      this.commentsByPostId[postId] = [...(this.commentsByPostId[postId] || []), tempComment]
      this.commentTotalsByPostId[postId] = (this.commentTotalsByPostId[postId] || 0) + 1
      this.patchPost(postId, (post) => {
        post.comments_count += 1
      })

      try {
        const saved = await apiCreateComment(postId, { content })
        this.commentsByPostId[postId] = (this.commentsByPostId[postId] || []).map((comment) =>
          comment.id === tempId ? saved : comment
        )
        return saved
      } catch (error: any) {
        this.commentsByPostId[postId] = (this.commentsByPostId[postId] || []).filter(
          (comment) => comment.id !== tempId
        )
        this.commentTotalsByPostId[postId] = Math.max(0, (this.commentTotalsByPostId[postId] || 1) - 1)
        this.patchPost(postId, (post) => {
          post.comments_count = Math.max(0, post.comments_count - 1)
        })
        this.error = error?.message || 'Failed to create comment'
        throw error
      } finally {
        this.submittingComment = false
      }
    }
  }
})

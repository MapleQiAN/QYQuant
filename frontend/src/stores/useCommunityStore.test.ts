import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useCommunityStore } from './useCommunityStore'
import { useUserStore } from './user'

const {
  getPostsMock,
  createPostMock,
  getPostDetailMock,
  likePostMock,
  collectPostMock,
  getCommentsMock,
  createCommentMock
} = vi.hoisted(() => ({
  getPostsMock: vi.fn(),
  createPostMock: vi.fn(),
  getPostDetailMock: vi.fn(),
  likePostMock: vi.fn(),
  collectPostMock: vi.fn(),
  getCommentsMock: vi.fn(),
  createCommentMock: vi.fn()
}))

vi.mock('../api/community', () => ({
  getPosts: getPostsMock,
  createPost: createPostMock,
  getPostDetail: getPostDetailMock,
  likePost: likePostMock,
  collectPost: collectPostMock,
  getComments: getCommentsMock,
  createComment: createCommentMock
}))

describe('useCommunityStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    getPostsMock.mockReset()
    createPostMock.mockReset()
    getPostDetailMock.mockReset()
    likePostMock.mockReset()
    collectPostMock.mockReset()
    getCommentsMock.mockReset()
    createCommentMock.mockReset()
  })

  it('loads feed and appends next pages', async () => {
    getPostsMock
      .mockResolvedValueOnce({
        items: [{ id: 'post-1', content: 'A', likes_count: 0, comments_count: 0, liked: false, collected: false }],
        total: 2,
        page: 1,
        per_page: 20
      })
      .mockResolvedValueOnce({
        items: [{ id: 'post-2', content: 'B', likes_count: 0, comments_count: 0, liked: false, collected: false }],
        total: 2,
        page: 2,
        per_page: 20
      })

    const store = useCommunityStore()
    await store.fetchPosts(1)
    await store.fetchPosts(2)

    expect(getPostsMock).toHaveBeenNthCalledWith(1, { page: 1, per_page: 20 })
    expect(getPostsMock).toHaveBeenNthCalledWith(2, { page: 2, per_page: 20 })
    expect(store.posts.map((post) => post.id)).toEqual(['post-1', 'post-2'])
    expect(store.postsTotal).toBe(2)
    expect(store.hasMorePosts).toBe(false)
  })

  it('creates a post and prepends it to the feed', async () => {
    createPostMock.mockResolvedValue({
      id: 'post-new',
      content: 'New',
      user_id: 'user-1',
      strategy_id: null,
      likes_count: 0,
      comments_count: 0,
      created_at: '2026-03-20T20:00:00+08:00',
      author: { nickname: 'Trader', avatar_url: '' },
      strategy: null,
      liked: false,
      collected: false
    })

    const store = useCommunityStore()
    store.posts = [
      {
        id: 'post-1',
        content: 'Old',
        user_id: 'user-1',
        strategy_id: null,
        likes_count: 0,
        comments_count: 0,
        created_at: '2026-03-20T19:00:00+08:00',
        author: { nickname: 'Trader', avatar_url: '' },
        strategy: null,
        liked: false,
        collected: false
      }
    ]

    await store.createPost('New')

    expect(createPostMock).toHaveBeenCalledWith({ content: 'New', strategy_id: undefined })
    expect(store.posts.map((post) => post.id)).toEqual(['post-new', 'post-1'])
  })

  it('fetches and stores post detail', async () => {
    getPostDetailMock.mockResolvedValue({
      id: 'post-1',
      content: 'Detail',
      user_id: 'user-1',
      strategy_id: null,
      likes_count: 0,
      comments_count: 0,
      created_at: '2026-03-20T20:00:00+08:00',
      author: { nickname: 'Trader', avatar_url: '' },
      strategy: null,
      liked: true,
      collected: false
    })

    const store = useCommunityStore()
    await store.fetchPostDetail('post-1')

    expect(getPostDetailMock).toHaveBeenCalledWith('post-1')
    expect(store.postDetailById['post-1']?.content).toBe('Detail')
    expect(store.likedPostIds['post-1']).toBe(true)
  })

  it('optimistically toggles like and reconciles with server state', async () => {
    likePostMock.mockResolvedValue({ liked: true, likes_count: 1 })

    const store = useCommunityStore()
    store.posts = [
      {
        id: 'post-1',
        content: 'Like me',
        user_id: 'user-1',
        strategy_id: null,
        likes_count: 0,
        comments_count: 0,
        created_at: '2026-03-20T20:00:00+08:00',
        author: { nickname: 'Trader', avatar_url: '' },
        strategy: null,
        liked: false,
        collected: false
      }
    ]

    await store.toggleLike('post-1')

    expect(likePostMock).toHaveBeenCalledWith('post-1')
    expect(store.posts[0].likes_count).toBe(1)
    expect(store.likedPostIds['post-1']).toBe(true)
  })

  it('rolls back optimistic like when the request fails', async () => {
    likePostMock.mockRejectedValue(new Error('like failed'))

    const store = useCommunityStore()
    store.posts = [
      {
        id: 'post-1',
        content: 'Like me',
        user_id: 'user-1',
        strategy_id: null,
        likes_count: 3,
        comments_count: 0,
        created_at: '2026-03-20T20:00:00+08:00',
        author: { nickname: 'Trader', avatar_url: '' },
        strategy: null,
        liked: false,
        collected: false
      }
    ]

    await expect(store.toggleLike('post-1')).rejects.toThrow('like failed')
    expect(store.posts[0].likes_count).toBe(3)
    expect(store.likedPostIds['post-1']).toBeUndefined()
  })

  it('fetches comments and appends the next page', async () => {
    getCommentsMock
      .mockResolvedValueOnce({
        items: [{ id: 'comment-1', content: 'A', user_id: 'user-1', created_at: '2026-03-20T20:00:00+08:00', author: { nickname: 'Trader', avatar_url: '' } }],
        total: 2,
        page: 1,
        per_page: 20
      })
      .mockResolvedValueOnce({
        items: [{ id: 'comment-2', content: 'B', user_id: 'user-1', created_at: '2026-03-20T20:01:00+08:00', author: { nickname: 'Trader', avatar_url: '' } }],
        total: 2,
        page: 2,
        per_page: 20
      })

    const store = useCommunityStore()
    await store.fetchComments('post-1', 1)
    await store.fetchComments('post-1', 2)

    expect(getCommentsMock).toHaveBeenNthCalledWith(1, 'post-1', { page: 1, per_page: 20 })
    expect(getCommentsMock).toHaveBeenNthCalledWith(2, 'post-1', { page: 2, per_page: 20 })
    expect(store.commentsByPostId['post-1'].map((comment) => comment.id)).toEqual(['comment-1', 'comment-2'])
  })

  it('creates a comment and updates the post comment count', async () => {
    const userStore = useUserStore()
    userStore.profile.id = 'user-1'
    userStore.profile.nickname = 'Trader'
    userStore.profile.avatar_url = 'https://example.com/avatar.png'

    createCommentMock.mockResolvedValue({
      id: 'comment-1',
      content: 'Nice post',
      user_id: 'user-1',
      created_at: '2026-03-20T20:10:00+08:00',
      author: { nickname: 'Trader', avatar_url: 'https://example.com/avatar.png' }
    })

    const store = useCommunityStore()
    store.posts = [
      {
        id: 'post-1',
        content: 'Post',
        user_id: 'user-1',
        strategy_id: null,
        likes_count: 0,
        comments_count: 0,
        created_at: '2026-03-20T20:00:00+08:00',
        author: { nickname: 'Trader', avatar_url: '' },
        strategy: null,
        liked: false,
        collected: false
      }
    ]

    await store.createComment('post-1', 'Nice post')

    expect(createCommentMock).toHaveBeenCalledWith('post-1', { content: 'Nice post' })
    expect(store.posts[0].comments_count).toBe(1)
    expect(store.commentsByPostId['post-1'][0].id).toBe('comment-1')
  })
})

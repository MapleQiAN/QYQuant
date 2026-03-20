import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as community from './community'

const { requestMock } = vi.hoisted(() => ({
  requestMock: vi.fn().mockResolvedValue({ ok: true })
}))

vi.mock('./http', () => ({
  createHttpClient: () => ({ request: requestMock })
}))

describe('community api', () => {
  beforeEach(() => {
    requestMock.mockClear()
  })

  it('calls posts feed endpoint', async () => {
    const data = await community.getPosts({ page: 2, per_page: 10 })

    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/posts',
      params: { page: 2, per_page: 10 }
    })
  })

  it('calls create post endpoint', async () => {
    const data = await community.createPost({ content: 'Hello', strategy_id: 'strategy-1' })

    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'post',
      url: '/v1/posts',
      data: { content: 'Hello', strategy_id: 'strategy-1' }
    })
  })

  it('calls post detail endpoint', async () => {
    const data = await community.getPostDetail('post-1')

    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/posts/post-1'
    })
  })

  it('calls like and collect endpoints', async () => {
    await community.likePost('post-1')
    expect(requestMock).toHaveBeenCalledWith({
      method: 'post',
      url: '/v1/posts/post-1/like'
    })

    await community.collectPost('post-1')
    expect(requestMock).toHaveBeenCalledWith({
      method: 'post',
      url: '/v1/posts/post-1/collect'
    })
  })

  it('calls comments endpoints', async () => {
    await community.getComments('post-1', { page: 3, per_page: 20 })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/posts/post-1/comments',
      params: { page: 3, per_page: 20 }
    })

    await community.createComment('post-1', { content: 'Nice post' })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'post',
      url: '/v1/posts/post-1/comments',
      data: { content: 'Nice post' }
    })
  })
})

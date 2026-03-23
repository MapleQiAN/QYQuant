import { createHttpClient } from './http'
import type {
  CommunityComment,
  CommunityPost,
  PaginatedCommunityComments,
  PaginatedCommunityPosts,
  ToggleCollectResult,
  ToggleLikeResult
} from '../types/community'

const client = createHttpClient()

export function getPosts(params?: { page?: number; per_page?: number }): Promise<PaginatedCommunityPosts> {
  return client.request({
    method: 'get',
    url: '/v1/posts',
    params
  })
}

export function createPost(data: { content: string; strategy_id?: string }): Promise<CommunityPost> {
  return client.request({
    method: 'post',
    url: '/v1/posts',
    data
  })
}

export function getPostDetail(postId: string): Promise<CommunityPost> {
  return client.request({
    method: 'get',
    url: `/v1/posts/${postId}`
  })
}

export function likePost(postId: string): Promise<ToggleLikeResult> {
  return client.request({
    method: 'post',
    url: `/v1/posts/${postId}/like`
  })
}

export function collectPost(postId: string): Promise<ToggleCollectResult> {
  return client.request({
    method: 'post',
    url: `/v1/posts/${postId}/collect`
  })
}

export function getMyCollections(params?: { page?: number; per_page?: number }): Promise<PaginatedCommunityPosts> {
  return client.request({
    method: 'get',
    url: '/v1/users/me/collections',
    params
  })
}

export function getComments(
  postId: string,
  params?: { page?: number; per_page?: number }
): Promise<PaginatedCommunityComments> {
  return client.request({
    method: 'get',
    url: `/v1/posts/${postId}/comments`,
    params
  })
}

export function createComment(postId: string, data: { content: string }): Promise<CommunityComment> {
  return client.request({
    method: 'post',
    url: `/v1/posts/${postId}/comments`,
    data
  })
}

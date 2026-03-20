export interface CommunityPostAuthor {
  nickname: string
  avatar_url: string
}

export interface CommunityPostStrategy {
  id: string
  name: string
  category: string | null
  returns: number
  max_drawdown: number
}

export interface CommunityPost {
  id: string
  content: string
  user_id: string
  strategy_id: string | null
  likes_count: number
  comments_count: number
  created_at: string | null
  author: CommunityPostAuthor
  strategy: CommunityPostStrategy | null
  liked: boolean
  collected: boolean
}

export interface PaginatedCommunityPosts {
  items: CommunityPost[]
  total: number
  page: number
  per_page: number
}

export interface CommunityComment {
  id: string
  content: string
  user_id: string
  created_at: string | null
  author: CommunityPostAuthor
}

export interface PaginatedCommunityComments {
  items: CommunityComment[]
  total: number
  page: number
  per_page: number
}

export interface ToggleLikeResult {
  liked: boolean
  likes_count: number
}

export interface ToggleCollectResult {
  collected: boolean
}

export interface User {
  id?: string
  name: string
  avatar: string
  level?: string
  notifications?: number
  nickname?: string
  avatar_url?: string
  bio?: string
  role?: string
  plan_level?: string
  is_banned?: boolean
  onboarding_completed: boolean
  sim_disclaimer_accepted: boolean
  phone?: string
  email?: string
  created_at?: string
  updated_at?: string
}

export interface UserProfileResponse {
  id?: string
  phone?: string
  email?: string
  nickname: string
  avatar_url: string
  bio: string
  role?: string
  plan_level?: string
  is_banned?: boolean
  onboarding_completed: boolean
  sim_disclaimer_accepted: boolean
  created_at?: string
  updated_at?: string
}

export interface UserPublicProfile {
  id: string
  nickname: string
  avatar_url: string
  bio: string
  is_banned: boolean
  created_at: string | null
}

export interface UserStrategyItem {
  id: string
  name: string
  category: string | null
  returns: number
  max_drawdown: number
  win_rate: number
  tags: string[]
}

export interface UserPostItem {
  id: string
  content: string
  likes_count: number
  comments_count: number
  created_at: string | null
}

export interface PaginatedStrategies {
  items: UserStrategyItem[]
  total: number
  page: number
  per_page: number
}

export interface PaginatedPosts {
  items: UserPostItem[]
  total: number
  page: number
  per_page: number
}

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
  phone?: string
  created_at?: string
  updated_at?: string
}

export interface UserProfileResponse {
  id?: string
  phone?: string
  nickname: string
  avatar_url: string
  bio: string
  role?: string
  plan_level?: string
  is_banned?: boolean
  onboarding_completed: boolean
  created_at?: string
  updated_at?: string
}

export interface NotificationItem {
  id: string
  type: string
  title: string
  content: string | null
  is_read: boolean
  created_at: string | null
}

export interface NotificationListMeta {
  total?: number
  page?: number
  per_page?: number
}

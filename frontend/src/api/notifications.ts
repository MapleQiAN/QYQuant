import { createHttpClient } from './http'
import type { NotificationItem, NotificationListMeta } from '../types/Notification'

const client = createHttpClient()

export function fetchUnreadCount(): Promise<{ count: number }> {
  return client.request({
    method: 'get',
    url: '/v1/notifications/unread-count'
  })
}

export function fetchNotifications(params?: { page?: number; per_page?: number }) {
  return client.requestWithMeta<NotificationItem[]>({
    method: 'get',
    url: '/v1/notifications',
    params
  }) as Promise<{ data: NotificationItem[]; meta?: NotificationListMeta }>
}

export function markNotificationAsRead(notificationId: string): Promise<{ ok: boolean }> {
  return client.request({
    method: 'patch',
    url: `/v1/notifications/${notificationId}/read`
  })
}

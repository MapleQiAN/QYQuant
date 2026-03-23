import { defineStore } from 'pinia'
import {
  fetchNotifications as fetchNotificationsApi,
  fetchUnreadCount as fetchUnreadCountApi,
  markNotificationAsRead,
} from '../api/notifications'
import type { NotificationItem } from '../types/Notification'

const DEFAULT_PER_PAGE = 20
const POLLING_INTERVAL_MS = 30000

export const useNotificationStore = defineStore('notification', {
  state: () => ({
    unreadCount: 0,
    notifications: [] as NotificationItem[],
    isLoading: false,
    page: 1,
    perPage: DEFAULT_PER_PAGE,
    total: 0,
    pollingTimer: null as ReturnType<typeof setInterval> | null,
  }),
  actions: {
    async fetchUnreadCount() {
      const result = await fetchUnreadCountApi()
      this.unreadCount = Number(result.count || 0)
    },
    startPolling() {
      void this.fetchUnreadCount()
      if (this.pollingTimer) {
        return
      }
      this.pollingTimer = setInterval(() => {
        void this.fetchUnreadCount()
      }, POLLING_INTERVAL_MS)
    },
    stopPolling() {
      if (this.pollingTimer) {
        clearInterval(this.pollingTimer)
        this.pollingTimer = null
      }
    },
    async fetchNotifications(page = 1) {
      this.isLoading = true
      try {
        const result = await fetchNotificationsApi({ page, per_page: this.perPage })
        this.notifications = result.data
        this.page = Number(result.meta?.page || page)
        this.perPage = Number(result.meta?.per_page || this.perPage)
        this.total = Number(result.meta?.total || result.data.length)
      } finally {
        this.isLoading = false
      }
    },
    async markAsRead(notificationId: string) {
      await markNotificationAsRead(notificationId)
      const notification = this.notifications.find((item) => item.id === notificationId)
      if (notification && !notification.is_read) {
        notification.is_read = true
        this.unreadCount = Math.max(0, this.unreadCount - 1)
      }
    },
  },
})

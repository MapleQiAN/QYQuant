import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useNotificationStore } from './useNotificationStore'

const {
  fetchNotificationsMock,
  fetchUnreadCountMock,
  markNotificationAsReadMock,
} = vi.hoisted(() => ({
  fetchNotificationsMock: vi.fn(),
  fetchUnreadCountMock: vi.fn(),
  markNotificationAsReadMock: vi.fn(),
}))

vi.mock('../api/notifications', () => ({
  fetchNotifications: fetchNotificationsMock,
  fetchUnreadCount: fetchUnreadCountMock,
  markNotificationAsRead: markNotificationAsReadMock,
}))

describe('notification store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    fetchNotificationsMock.mockReset()
    fetchUnreadCountMock.mockReset()
    markNotificationAsReadMock.mockReset()
  })

  it('fetches unread count into state', async () => {
    fetchUnreadCountMock.mockResolvedValueOnce({ count: 4 })
    const store = useNotificationStore()

    await store.fetchUnreadCount()

    expect(fetchUnreadCountMock).toHaveBeenCalledTimes(1)
    expect(store.unreadCount).toBe(4)
  })

  it('fetches paginated notifications into state', async () => {
    fetchNotificationsMock.mockResolvedValueOnce({
      data: [
        {
          id: 'notification-1',
          type: 'review',
          title: '审核通过',
          content: '内容摘要',
          is_read: false,
          created_at: '2026-03-23T18:00:00+08:00',
        },
      ],
      meta: { total: 1, page: 1, per_page: 20 },
    })
    const store = useNotificationStore()

    await store.fetchNotifications(1)

    expect(fetchNotificationsMock).toHaveBeenCalledWith({ page: 1, per_page: 20 })
    expect(store.notifications).toHaveLength(1)
    expect(store.total).toBe(1)
    expect(store.page).toBe(1)
  })

  it('marks an unread notification as read and decrements unread count once', async () => {
    markNotificationAsReadMock.mockResolvedValueOnce({ ok: true })
    const store = useNotificationStore()
    store.unreadCount = 2
    store.notifications = [
      {
        id: 'notification-1',
        type: 'review',
        title: '审核通过',
        content: '内容摘要',
        is_read: false,
        created_at: '2026-03-23T18:00:00+08:00',
      },
      {
        id: 'notification-2',
        type: 'review',
        title: '已读消息',
        content: '内容摘要',
        is_read: true,
        created_at: '2026-03-23T17:00:00+08:00',
      },
    ]

    await store.markAsRead('notification-1')
    await store.markAsRead('notification-2')

    expect(markNotificationAsReadMock).toHaveBeenCalledTimes(2)
    expect(store.unreadCount).toBe(1)
    expect(store.notifications[0].is_read).toBe(true)
  })

  it('starts polling immediately and stops cleanly', async () => {
    vi.useFakeTimers()
    fetchUnreadCountMock.mockResolvedValue({ count: 3 })
    const store = useNotificationStore()

    store.startPolling()
    await Promise.resolve()

    expect(fetchUnreadCountMock).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(30000)
    await Promise.resolve()

    expect(fetchUnreadCountMock).toHaveBeenCalledTimes(2)

    store.stopPolling()
    vi.advanceTimersByTime(30000)
    await Promise.resolve()

    expect(fetchUnreadCountMock).toHaveBeenCalledTimes(2)
    vi.useRealTimers()
  })
})

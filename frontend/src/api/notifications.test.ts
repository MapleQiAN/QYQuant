import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as notifications from './notifications'

const { requestMock, requestWithMetaMock } = vi.hoisted(() => ({
  requestMock: vi.fn().mockResolvedValue({ ok: true }),
  requestWithMetaMock: vi.fn().mockResolvedValue({ data: [], meta: { page: 1, per_page: 20, total: 0 } }),
}))

vi.mock('./http', () => ({
  createHttpClient: () => ({
    request: requestMock,
    requestWithMeta: requestWithMetaMock,
  })
}))

describe('notifications api', () => {
  beforeEach(() => {
    requestMock.mockClear()
    requestWithMetaMock.mockClear()
  })

  it('calls unread count endpoint', async () => {
    const data = await notifications.fetchUnreadCount()

    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/notifications/unread-count'
    })
  })

  it('calls paginated notifications endpoint', async () => {
    const data = await notifications.fetchNotifications({ page: 2, per_page: 10 })

    expect(data).toEqual({ data: [], meta: { page: 1, per_page: 20, total: 0 } })
    expect(requestWithMetaMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/notifications',
      params: { page: 2, per_page: 10 }
    })
  })

  it('calls mark-as-read endpoint', async () => {
    const data = await notifications.markNotificationAsRead('notification-1')

    expect(data).toEqual({ ok: true })
    expect(requestMock).toHaveBeenCalledWith({
      method: 'patch',
      url: '/v1/notifications/notification-1/read'
    })
  })
})

// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

const {
  loadUsersMock,
  loadAuditLogsMock,
  banUserMock,
  unbanUserMock,
  toastSuccessMock,
  toastErrorMock,
  storeState
} = vi.hoisted(() => ({
  loadUsersMock: vi.fn(),
  loadAuditLogsMock: vi.fn(),
  banUserMock: vi.fn(),
  unbanUserMock: vi.fn(),
  toastSuccessMock: vi.fn(),
  toastErrorMock: vi.fn(),
  storeState: {
    users: [
      {
        userId: 'user-1',
        nickname: 'Alice',
        phone: '138****8000',
        createdAt: '2026-03-26T12:00:00+08:00',
        planLevel: 'pro',
        isBanned: false
      },
      {
        userId: 'user-2',
        nickname: 'Bob',
        phone: '139****8246',
        createdAt: '2026-03-25T12:00:00+08:00',
        planLevel: 'free',
        isBanned: true
      }
    ] as any[],
    usersMeta: { total: 2, page: 1, perPage: 20 },
    userListLoading: false,
    banningUsers: {} as Record<string, boolean>,
    auditLogs: [
      {
        id: 'audit-1',
        operatorId: 'admin-1',
        operatorNickname: 'Root',
        action: 'user_ban',
        targetType: 'user',
        targetId: 'user-2',
        details: { ban_reason: 'spam' },
        createdAt: '2026-03-26T12:30:00+08:00'
      }
    ] as any[],
    auditLogsMeta: { total: 1, page: 1, perPage: 20 },
    auditLogsLoading: false
  }
}))

vi.mock('../../stores/useAdminStore', () => ({
  useAdminStore: () => ({
    ...storeState,
    loadUsers: loadUsersMock,
    loadAuditLogs: loadAuditLogsMock,
    banUser: banUserMock,
    unbanUser: unbanUserMock
  })
}))

vi.mock('../../lib/toast', () => ({
  toast: {
    success: toastSuccessMock,
    error: toastErrorMock
  }
}))

import UserManagement from './UserManagement.vue'

function mountUserManagement() {
  return mount(UserManagement, {
    global: {
      stubs: {
        RouterLink: {
          template: '<a><slot /></a>'
        }
      }
    }
  })
}

describe('UserManagement', () => {
  beforeEach(() => {
    loadUsersMock.mockReset()
    loadAuditLogsMock.mockReset()
    banUserMock.mockReset()
    unbanUserMock.mockReset()
    toastSuccessMock.mockReset()
    toastErrorMock.mockReset()
    storeState.users = [
      {
        userId: 'user-1',
        nickname: 'Alice',
        phone: '138****8000',
        createdAt: '2026-03-26T12:00:00+08:00',
        planLevel: 'pro',
        isBanned: false
      },
      {
        userId: 'user-2',
        nickname: 'Bob',
        phone: '139****8246',
        createdAt: '2026-03-25T12:00:00+08:00',
        planLevel: 'free',
        isBanned: true
      }
    ]
    storeState.usersMeta = { total: 2, page: 1, perPage: 20 }
    storeState.userListLoading = false
    storeState.banningUsers = {}
    storeState.auditLogs = [
      {
        id: 'audit-1',
        operatorId: 'admin-1',
        operatorNickname: 'Root',
        action: 'user_ban',
        targetType: 'user',
        targetId: 'user-2',
        details: { ban_reason: 'spam' },
        createdAt: '2026-03-26T12:30:00+08:00'
      }
    ]
    storeState.auditLogsMeta = { total: 1, page: 1, perPage: 20 }
    storeState.auditLogsLoading = false
  })

  it('loads users and audit logs on mount and supports user search', async () => {
    const wrapper = mountUserManagement()

    expect(loadUsersMock).toHaveBeenCalledWith({ page: 1, perPage: 20, search: '' })
    expect(loadAuditLogsMock).toHaveBeenCalledWith({ page: 1, perPage: 20 })
    expect(wrapper.text()).toContain('Alice')
    expect(wrapper.text()).toContain('Bob')

    await wrapper.get('[data-test="user-search-input"]').setValue('Alice')
    await wrapper.get('[data-test="user-search-submit"]').trigger('click')

    expect(loadUsersMock).toHaveBeenLastCalledWith({ page: 1, perPage: 20, search: 'Alice' })
  })

  it('requires a reason before banning a user', async () => {
    const wrapper = mountUserManagement()

    await wrapper.get('[data-test="open-ban-user-1"]').trigger('click')
    await wrapper.get('[data-test="confirm-ban-action"]').trigger('click')
    await flushPromises()

    expect(banUserMock).not.toHaveBeenCalled()
    expect(toastErrorMock).toHaveBeenCalled()
  })

  it('submits ban and unban actions', async () => {
    banUserMock.mockResolvedValueOnce({ userId: 'user-1', isBanned: true })
    unbanUserMock.mockResolvedValueOnce({ userId: 'user-2', isBanned: false })
    const wrapper = mountUserManagement()

    await wrapper.get('[data-test="open-ban-user-1"]').trigger('click')
    await wrapper.get('[data-test="ban-dialog-reason"]').setValue('spam')
    await wrapper.get('[data-test="confirm-ban-action"]').trigger('click')
    await flushPromises()

    expect(banUserMock).toHaveBeenCalledWith('user-1', 'spam')
    expect(toastSuccessMock).toHaveBeenCalled()

    await wrapper.get('[data-test="open-unban-user-2"]').trigger('click')
    await wrapper.get('[data-test="confirm-ban-action"]').trigger('click')
    await flushPromises()

    expect(unbanUserMock).toHaveBeenCalledWith('user-2')
  })

  it('renders audit logs and applies audit filters', async () => {
    const wrapper = mountUserManagement()

    await wrapper.get('[data-test="tab-audit-logs"]').trigger('click')
    expect(wrapper.text()).toContain('Root')
    expect(wrapper.text()).toContain('user_ban')

    await wrapper.get('[data-test="audit-action-input"]').setValue('user_ban')
    await wrapper.get('[data-test="audit-operator-input"]').setValue('admin-1')
    await wrapper.get('[data-test="apply-audit-filters"]').trigger('click')

    expect(loadAuditLogsMock).toHaveBeenLastCalledWith({
      operatorId: 'admin-1',
      action: 'user_ban',
      targetType: '',
      dateFrom: '',
      dateTo: '',
      page: 1,
      perPage: 20
    })
  })
})

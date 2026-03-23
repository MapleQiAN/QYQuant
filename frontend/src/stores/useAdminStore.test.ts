import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

const { fetchAdminHealthMock } = vi.hoisted(() => ({
  fetchAdminHealthMock: vi.fn()
}))

vi.mock('../api/admin', () => ({
  fetchAdminHealth: fetchAdminHealthMock
}))

import { useAdminStore } from './useAdminStore'

describe('admin store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    fetchAdminHealthMock.mockReset()
  })

  it('loads admin health overview into state', async () => {
    fetchAdminHealthMock.mockResolvedValueOnce({ status: 'ok', scope: 'admin' })
    const store = useAdminStore()

    await store.loadOverview()

    expect(fetchAdminHealthMock).toHaveBeenCalledTimes(1)
    expect(store.overview).toEqual({ status: 'ok', scope: 'admin' })
    expect(store.loading).toBe(false)
  })
})

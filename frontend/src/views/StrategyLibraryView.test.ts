import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import StrategyLibraryView from './StrategyLibraryView.vue'

const { pushMock, fetchStrategiesMock, deleteStrategyMock, importStrategyMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  fetchStrategiesMock: vi.fn(),
  deleteStrategyMock: vi.fn(),
  importStrategyMock: vi.fn()
}))

vi.mock('vue-router', () => ({
  RouterLink: {
    template: '<a><slot /></a>'
  },
  useRouter: () => ({
    push: pushMock
  })
}))

vi.mock('../api/strategies', () => ({
  fetchStrategies: fetchStrategiesMock,
  deleteStrategy: deleteStrategyMock,
  importStrategy: importStrategyMock
}))

describe('StrategyLibraryView', () => {
  beforeEach(() => {
    pushMock.mockClear()
    fetchStrategiesMock.mockReset()
    deleteStrategyMock.mockReset()
    importStrategyMock.mockReset()
    vi.stubGlobal('confirm', vi.fn(() => true))
  })

  it('loads and renders strategy library rows', async () => {
    fetchStrategiesMock.mockResolvedValue({
      items: [
        {
          id: 'strategy-1',
          name: 'Golden Cross',
          description: 'Trend following',
          tags: ['gold'],
          category: 'trend-following',
          source: 'upload',
          createdAt: 123
        }
      ],
      page: 1,
      perPage: 10,
      total: 1
    })
    deleteStrategyMock.mockResolvedValue({ deletedId: 'strategy-1' })

    const wrapper = mount(StrategyLibraryView)
    await flushPromises()

    expect(fetchStrategiesMock).toHaveBeenCalledWith({ page: 1, perPage: 10 })
    expect(wrapper.text()).toContain('Golden Cross')

    await wrapper.get('[data-test="delete-strategy-1"]').trigger('click')
    await flushPromises()

    expect(deleteStrategyMock).toHaveBeenCalledWith('strategy-1')
  })

  it('accepts dropped files and redirects after import', async () => {
    fetchStrategiesMock.mockResolvedValue({ items: [], page: 1, perPage: 10, total: 0 })
    importStrategyMock.mockResolvedValue({
      strategy: {
        id: 'strategy-2',
        name: 'Mean Reversion',
        description: 'Preview',
        tags: ['mean'],
        category: 'mean-reversion',
        source: 'upload'
      },
      next: '/strategies/strategy-2/parameters'
    })

    const wrapper = mount(StrategyLibraryView)
    await flushPromises()

    const file = new File(['package'], 'mean-reversion.qys', { type: 'application/octet-stream' })
    await wrapper.get('[data-test="dropzone"]').trigger('drop', {
      dataTransfer: { files: [file] }
    })
    await wrapper.get('[data-test="import-submit"]').trigger('click')
    await flushPromises()

    expect(importStrategyMock).toHaveBeenCalledWith(file)
    expect(pushMock).toHaveBeenCalledWith('/strategies/strategy-2/parameters')
    expect(wrapper.text()).toContain('Mean Reversion')
  })
})

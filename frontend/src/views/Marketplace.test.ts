// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import Marketplace from './Marketplace.vue'

const {
  pushMock,
  fetchStrategiesMock,
  fetchFeaturedMock,
  setFilterMock,
  clearFiltersMock,
  storeState
} = vi.hoisted(() => ({
  pushMock: vi.fn(),
  fetchStrategiesMock: vi.fn(),
  fetchFeaturedMock: vi.fn(),
  setFilterMock: vi.fn(),
  clearFiltersMock: vi.fn(),
  storeState: {
    strategies: [] as any[],
    featuredStrategies: [] as any[],
    loading: false,
    featuredLoading: false,
    featuredError: null as string | null,
    error: null as string | null,
    total: 0,
    page: 1,
    pageSize: 20,
    filters: {
      q: '',
      category: null as string | null,
      verified: false,
      annualReturnGte: null,
      maxDrawdownLte: null
    }
  }
}))

vi.mock('../stores', () => ({
  useMarketplaceStore: () => ({
    ...storeState,
    fetchStrategies: fetchStrategiesMock,
    fetchFeatured: fetchFeaturedMock,
    setFilter: setFilterMock,
    clearFilters: clearFiltersMock
  })
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: pushMock
  }),
  RouterLink: {
    template: '<a><slot /></a>'
  }
}))

describe('Marketplace view', () => {
  beforeEach(() => {
    pushMock.mockReset()
    fetchStrategiesMock.mockReset()
    fetchFeaturedMock.mockReset()
    setFilterMock.mockReset()
    clearFiltersMock.mockReset()
    storeState.strategies = []
    storeState.featuredStrategies = []
    storeState.loading = false
    storeState.featuredLoading = false
    storeState.featuredError = null
    storeState.error = null
    storeState.total = 0
    storeState.page = 1
    storeState.pageSize = 20
    storeState.filters = {
      q: '',
      category: null as string | null,
      verified: false,
      annualReturnGte: null,
      maxDrawdownLte: null
    }
  })

  it('loads featured and normal list on mount', () => {
    mount(Marketplace)

    expect(fetchFeaturedMock).toHaveBeenCalledTimes(1)
    expect(fetchStrategiesMock).toHaveBeenCalledWith(1)
  })

  it('shows featured strip when featured strategies exist', () => {
    storeState.featuredStrategies = [
      {
        id: 'featured-1',
        title: 'Featured Alpha',
        name: 'featured-alpha',
        description: 'featured',
        category: 'trend',
        tags: ['gold'],
        isVerified: true,
        displayMetrics: {},
        author: { nickname: 'Editor', avatarUrl: '' }
      }
    ]
    const wrapper = mount(Marketplace)

    expect(wrapper.find('[data-test="featured-section"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Featured Alpha')
  })

  it('hides featured strip when no featured strategies and shows normal empty state', () => {
    storeState.featuredStrategies = []
    storeState.strategies = []
    const wrapper = mount(Marketplace)

    expect(wrapper.find('[data-test="featured-section"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="marketplace-empty"]').exists()).toBe(true)
  })

  it('renders non-empty normal strategies in the standard grid', () => {
    storeState.strategies = [
      {
        id: 'strategy-1',
        title: 'Gold Swing Core',
        name: 'gold-swing-core',
        description: 'Swing strategy',
        category: 'swing',
        tags: ['gold'],
        isVerified: false,
        displayMetrics: {},
        author: { nickname: 'Alice', avatarUrl: '' }
      }
    ]
    const wrapper = mount(Marketplace)

    expect(wrapper.find('[data-test="marketplace-empty"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="marketplace-grid"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Gold Swing Core')
  })

  it('does not render page-level back navigation link', () => {
    const wrapper = mount(Marketplace)
    expect(wrapper.text()).not.toContain('Back to dashboard')
  })

  it('still renders main strategy grid when featured request fails', () => {
    storeState.featuredError = 'Featured list unavailable'
    storeState.featuredStrategies = []
    storeState.error = null
    storeState.strategies = [
      {
        id: 'strategy-9',
        title: 'Primary Grid Strategy',
        name: 'primary-grid-strategy',
        description: 'Main list item',
        category: 'trend',
        tags: ['gold'],
        isVerified: true,
        displayMetrics: {},
        author: { nickname: 'Bob', avatarUrl: '' }
      }
    ]

    const wrapper = mount(Marketplace)
    expect(wrapper.find('[data-test="marketplace-grid"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Primary Grid Strategy')
    expect(wrapper.find('[data-test="featured-error"]').exists()).toBe(true)
  })

  it('debounces search input before refetching', async () => {
    vi.useFakeTimers()

    const wrapper = mount(Marketplace)
    fetchStrategiesMock.mockClear()
    await wrapper.get('[data-test="marketplace-search-input"]').setValue('均线')

    expect(setFilterMock).not.toHaveBeenCalled()
    vi.advanceTimersByTime(299)
    expect(fetchStrategiesMock).not.toHaveBeenCalled()

    vi.advanceTimersByTime(1)
    expect(setFilterMock).toHaveBeenCalledWith('q', '均线')
    expect(fetchStrategiesMock).toHaveBeenCalledWith(1)
    vi.useRealTimers()
  })

  it('clears active filters from the empty state', async () => {
    storeState.filters = {
      q: '均线',
      category: 'trend-following' as string | null,
      verified: false,
      annualReturnGte: null,
      maxDrawdownLte: null
    }
    const wrapper = mount(Marketplace)

    await wrapper.get('[data-test="marketplace-clear-filters"]').trigger('click')

    expect(clearFiltersMock).toHaveBeenCalledTimes(1)
    expect(fetchStrategiesMock).toHaveBeenCalledWith(1)
  })

  it('opens strategy detail when a card CTA is clicked', async () => {
    storeState.strategies = [
      {
        id: 'strategy-1',
        title: 'Gold Swing Core',
        name: 'gold-swing-core',
        description: 'Swing strategy',
        category: 'swing',
        tags: ['gold'],
        isVerified: false,
        displayMetrics: {},
        author: { nickname: 'Alice', avatarUrl: '' }
      }
    ]

    const wrapper = mount(Marketplace)

    await wrapper.get('[data-test="strategy-cta"]').trigger('click')

    expect(pushMock).toHaveBeenCalledWith({
      name: 'marketplace-strategy-detail',
      params: { strategyId: 'strategy-1' }
    })
  })
})

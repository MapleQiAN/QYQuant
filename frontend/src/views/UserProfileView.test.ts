// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import UserProfileView from './UserProfileView.vue'
import { useUserStore } from '../stores/user'

const {
  getUserProfileMock,
  getUserStrategiesMock,
  getUserPostsMock
} = vi.hoisted(() => ({
  getUserProfileMock: vi.fn(),
  getUserStrategiesMock: vi.fn(),
  getUserPostsMock: vi.fn()
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: {
      id: 'user-1'
    }
  })
}))

vi.mock('../api/users', async () => {
  const actual = await vi.importActual<typeof import('../api/users')>('../api/users')
  return {
    ...actual,
    getUserProfile: getUserProfileMock,
    getUserStrategies: getUserStrategiesMock,
    getUserPosts: getUserPostsMock
  }
})

describe('UserProfileView', () => {
  beforeEach(() => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const userStore = useUserStore(pinia)
    userStore.profile.id = 'user-1'

    getUserProfileMock.mockReset()
    getUserStrategiesMock.mockReset()
    getUserPostsMock.mockReset()

    getUserProfileMock.mockResolvedValue({
      id: 'user-1',
      nickname: 'Quant Alice',
      avatar_url: '',
      bio: 'Systematic trader',
      is_banned: false,
      created_at: '2026-03-20T20:00:00+08:00'
    })
    getUserStrategiesMock.mockResolvedValue({
      items: [
        {
          id: 'strategy-1',
          name: 'Alpha Strategy',
          category: 'trend-following',
          returns: 12.5,
          max_drawdown: -4.2,
          win_rate: 58,
          tags: ['alpha']
        }
      ],
      total: 1,
      page: 1,
      per_page: 20
    })
    getUserPostsMock.mockResolvedValue({
      items: [
        {
          id: 'post-1',
          content: 'Community insight',
          likes_count: 3,
          comments_count: 1,
          created_at: '2026-03-20T20:30:00+08:00'
        }
      ],
      total: 1,
      page: 1,
      per_page: 20
    })
  })

  it('loads profile, shows edit link for owner, and switches tabs', async () => {
    const wrapper = mount(UserProfileView, {
      global: {
        stubs: {
          RouterLink: {
            props: ['to'],
            template: '<a :href="to"><slot /></a>'
          }
        }
      }
    })

    await flushPromises()

    expect(getUserProfileMock).toHaveBeenCalledWith('user-1')
    expect(getUserStrategiesMock).toHaveBeenCalledWith('user-1', { page: 1, per_page: 20 })
    expect(wrapper.text()).toContain('Quant Alice')
    expect(wrapper.text()).toContain('Alpha Strategy')
    expect(wrapper.text()).toContain('编辑资料')

    await wrapper.get('[data-test="tab-posts"]').trigger('click')
    await flushPromises()

    expect(getUserPostsMock).toHaveBeenCalledWith('user-1', { page: 1, per_page: 20 })
    expect(wrapper.text()).toContain('Community insight')
  })
})

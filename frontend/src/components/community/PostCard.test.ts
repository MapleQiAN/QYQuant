// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import PostCard from './PostCard.vue'

const toggleLikeMock = vi.fn()
const toggleCollectMock = vi.fn()

vi.mock('../../stores/useCommunityStore', () => ({
  useCommunityStore: () => ({
    toggleLike: toggleLikeMock,
    toggleCollect: toggleCollectMock,
  }),
}))

describe('PostCard', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    toggleLikeMock.mockReset()
    toggleCollectMock.mockReset()
  })

  it('renders uploaded avatar image when author avatar url exists', () => {
    const wrapper = mount(PostCard, {
      props: {
        post: {
          id: 'post-1',
          content: 'Avatar backed post',
          user_id: 'user-1',
          strategy_id: null,
          likes_count: 3,
          comments_count: 1,
          created_at: '2026-03-31T10:00:00+08:00',
          author: {
            nickname: 'Quant Alice',
            avatar_url: '/api/files/avatar-1/content',
          },
          strategy: null,
          liked: false,
          collected: false,
        },
      },
      global: {
        stubs: {
          RouterLink: {
            props: ['to'],
            template: '<a :href="to"><slot /></a>',
          },
        },
      },
    })

    const avatar = wrapper.get('[data-test="post-author-avatar-image"]')
    expect(avatar.attributes('src')).toBe('/api/files/avatar-1/content')
    expect(wrapper.find('[data-test="post-author-avatar-fallback"]').exists()).toBe(false)
  })
})

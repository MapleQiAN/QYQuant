// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent } from 'vue'
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

const RouterLinkStub = defineComponent({
  name: 'RouterLink',
  props: {
    to: {
      type: [String, Object],
      required: true,
    },
  },
  template: '<a :href="typeof to === \'string\' ? to : undefined" :data-to="typeof to === \'string\' ? undefined : JSON.stringify(to)"><slot /></a>',
})

function buildPost(overrides: Record<string, unknown> = {}) {
  return {
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
    ...overrides,
  }
}

describe('PostCard', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    toggleLikeMock.mockReset()
    toggleCollectMock.mockReset()
  })

  it('renders uploaded avatar image when author avatar url exists', () => {
    const wrapper = mount(PostCard, {
      props: {
        post: buildPost(),
      },
      global: {
        stubs: {
          RouterLink: RouterLinkStub,
        },
      },
    })

    const avatar = wrapper.get('[data-test="post-author-avatar-image"]')
    expect(avatar.attributes('src')).toBe('/api/files/avatar-1/content')
    expect(wrapper.find('[data-test="post-author-avatar-fallback"]').exists()).toBe(false)
  })

  it('renders attached strategy as marketplace detail cta', () => {
    const wrapper = mount(PostCard, {
      props: {
        post: buildPost({
          strategy_id: 'strategy-42',
          strategy: {
            id: 'strategy-42',
            name: 'Alpha Rotation',
            category: '轮动',
            returns: 18.6,
            max_drawdown: 6.3,
          },
        }),
      },
      global: {
        stubs: {
          RouterLink: RouterLinkStub,
        },
      },
    })

    const strategyLink = wrapper.get('[data-test="attached-strategy-link"]')
    expect(strategyLink.attributes('data-to')).toBe(JSON.stringify({
      name: 'marketplace-strategy-detail',
      params: {
        strategyId: 'strategy-42',
      },
    }))
    expect(strategyLink.text()).toContain('先看详情')
  })

  it('keeps the attached strategy cta visible in detail mode', () => {
    const wrapper = mount(PostCard, {
      props: {
        post: buildPost({
          strategy_id: 'strategy-42',
          strategy: {
            id: 'strategy-42',
            name: 'Alpha Rotation',
            category: '轮动',
            returns: 18.6,
            max_drawdown: 6.3,
          },
        }),
        detailMode: true,
      },
      global: {
        stubs: {
          RouterLink: RouterLinkStub,
        },
      },
    })

    expect(wrapper.find('.detail-link').exists()).toBe(false)

    const strategyLink = wrapper.get('[data-test="attached-strategy-link"]')
    expect(strategyLink.attributes('data-to')).toBe(JSON.stringify({
      name: 'marketplace-strategy-detail',
      params: {
        strategyId: 'strategy-42',
      },
    }))
    expect(strategyLink.text()).toContain('先看详情')
  })
})

// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ForumMiniCard from './ForumMiniCard.vue'

describe('ForumMiniCard', () => {
  it('emits dashboard actions for view all, publish, bookmarks, and post open', async () => {
    const wrapper = mount(ForumMiniCard, {
      props: {
        posts: [
          {
            id: 'post-1',
            content: 'Gold breakout setup',
            user_id: 'user-1',
            strategy_id: null,
            likes_count: 12,
            comments_count: 3,
            created_at: '2026-04-17T10:00:00+08:00',
            author: { nickname: 'Alice', avatar_url: '' },
            strategy: null,
            liked: false,
            collected: false
          }
        ]
      },
      global: {
        mocks: {
          $t: (key: string) => key
        }
      }
    })

    await wrapper.get('[data-test="forum-view-all"]').trigger('click')
    await wrapper.get('[data-test="forum-open-post-post-1"]').trigger('click')
    await wrapper.get('[data-test="forum-publish"]').trigger('click')
    await wrapper.get('[data-test="forum-bookmarks"]').trigger('click')

    expect(wrapper.emitted('view-all')).toHaveLength(1)
    expect(wrapper.emitted('open-post')).toEqual([['post-1']])
    expect(wrapper.emitted('publish')).toHaveLength(1)
    expect(wrapper.emitted('bookmarks')).toHaveLength(1)
  })
})

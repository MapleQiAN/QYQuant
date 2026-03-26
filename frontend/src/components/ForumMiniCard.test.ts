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
            title: 'Gold breakout setup',
            author: 'Alice',
            avatar: 'A',
            likes: 12,
            comments: 3,
            timestamp: '2m ago',
            tags: ['gold']
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

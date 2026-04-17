// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import PostComposer from './PostComposer.vue'

const createPostMock = vi.fn()
const loadLibraryMock = vi.fn()

const communityStoreMock = {
  submittingPost: false,
  createPost: createPostMock,
}

const strategiesStoreMock = {
  library: [
    {
      id: 'strategy-1',
      name: 'Rotation Alpha',
      title: 'Rotation Alpha',
    },
  ],
  loadLibrary: loadLibraryMock,
}

const userStoreMock = {
  profile: {
    id: 'user-1',
  },
}

vi.mock('../../stores/useCommunityStore', () => ({
  useCommunityStore: () => communityStoreMock,
}))

vi.mock('../../stores/strategies', () => ({
  useStrategiesStore: () => strategiesStoreMock,
}))

vi.mock('../../stores/user', () => ({
  useUserStore: () => userStoreMock,
}))

describe('PostComposer', () => {
  beforeEach(() => {
    createPostMock.mockReset()
    loadLibraryMock.mockReset()
    communityStoreMock.submittingPost = false
    strategiesStoreMock.library = [
      {
        id: 'strategy-1',
        name: 'Rotation Alpha',
        title: 'Rotation Alpha',
      },
    ]
    userStoreMock.profile.id = 'user-1'
  })

  it('keeps the composer discussion-first while exposing strategy attachment', () => {
    const wrapper = mount(PostComposer)

    expect(wrapper.text()).toContain('策略心得')
    expect(wrapper.text()).toContain('复盘')
    expect(wrapper.text()).toContain('不是源码发布区')

    const attachmentHint = wrapper.get('[data-test="strategy-attachment-hint"]')
    expect(attachmentHint.text()).toContain('附上一个策略')

    const strategySelect = wrapper.get('[data-test="strategy-attachment-select"]')
    expect(strategySelect.findAll('option')).toHaveLength(2)
    expect(strategySelect.text()).toContain('Rotation Alpha')
  })
})

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SkeletonState from './SkeletonState.vue'

describe('SkeletonState', () => {
  it('renders requested number of lines', () => {
    const wrapper = mount(SkeletonState, { props: { lines: 3 } })
    expect(wrapper.findAll('.skeleton-line').length).toBe(4)
  })
})

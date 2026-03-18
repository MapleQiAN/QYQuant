import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import DisclaimerFooter from './DisclaimerFooter.vue'

describe('DisclaimerFooter', () => {
  it('renders the default disclaimer text with accessibility metadata', () => {
    const wrapper = mount(DisclaimerFooter)

    expect(wrapper.get('[data-test="disclaimer-footer"]').text()).toContain('基于历史数据，不构成投资建议')
    expect(wrapper.get('[data-test="disclaimer-footer"]').attributes('role')).toBe('contentinfo')
    expect(wrapper.get('[data-test="disclaimer-footer"]').attributes('aria-label')).toBe('免责声明')
  })
})

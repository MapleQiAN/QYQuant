// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import DisclaimerTooltip from './DisclaimerTooltip.vue'

describe('DisclaimerTooltip', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('shows the disclaimer after the hover delay and wires aria attributes', async () => {
    const wrapper = mount(DisclaimerTooltip)
    const trigger = wrapper.get('[data-test="disclaimer-tooltip-trigger"]')
    const bubble = wrapper.get('[data-test="disclaimer-tooltip-content"]')

    expect(trigger.attributes('aria-describedby')).toBeTruthy()
    expect(bubble.attributes('role')).toBe('tooltip')
    expect(bubble.attributes('aria-hidden')).toBe('true')

    await trigger.trigger('mouseenter')
    vi.advanceTimersByTime(299)
    expect(bubble.attributes('aria-hidden')).toBe('true')

    vi.advanceTimersByTime(1)
    await wrapper.vm.$nextTick()

    expect(bubble.attributes('aria-hidden')).toBe('false')
    expect(bubble.text()).toContain('仅供参考，历史表现不代表未来收益')
  })
})

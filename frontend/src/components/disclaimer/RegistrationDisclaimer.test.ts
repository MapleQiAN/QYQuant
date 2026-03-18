import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import RegistrationDisclaimer from './RegistrationDisclaimer.vue'

describe('RegistrationDisclaimer', () => {
  it('supports v-model updates and renders agreement links', async () => {
    const wrapper = mount(RegistrationDisclaimer, {
      props: {
        modelValue: false,
      },
    })

    const checkbox = wrapper.get('[data-test="registration-disclaimer-checkbox"]')

    expect(checkbox.attributes('aria-required')).toBe('true')
    expect(wrapper.get('[data-test="service-agreement-link"]').attributes('href')).toBe('#')
    expect(wrapper.get('[data-test="disclaimer-link"]').attributes('href')).toBe('#')

    await checkbox.setValue(true)
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([true])
  })
})

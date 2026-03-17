// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import HelpPanel from './HelpPanel.vue'

describe('HelpPanel', () => {
  it('filters FAQ items by search keyword and category', async () => {
    const wrapper = mount(HelpPanel, {
      props: {
        open: true,
      },
    })

    expect(wrapper.text()).toContain('什么是回测')
    expect(wrapper.text()).toContain('夏普比率')

    await wrapper.get('[data-test="help-search"]').setValue('夏普')
    expect(wrapper.text()).toContain('夏普比率')
    expect(wrapper.text()).not.toContain('什么是回测')

    await wrapper.get('[data-test="help-category-core-metrics"]').trigger('click')
    expect(wrapper.text()).toContain('夏普比率')
  })
})

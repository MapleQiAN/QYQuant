// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import UpgradeCard from './UpgradeCard.vue'

describe('UpgradeCard', () => {
  it('emits upgrade when CTA is clicked', async () => {
    const wrapper = mount(UpgradeCard, {
      global: {
        mocks: {
          $t: (key: string) => key
        }
      }
    })

    await wrapper.get('[data-test="upgrade-cta"]').trigger('click')

    expect(wrapper.emitted('upgrade')).toHaveLength(1)
  })
})

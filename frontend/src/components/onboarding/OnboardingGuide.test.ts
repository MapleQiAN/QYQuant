// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import OnboardingGuide from './OnboardingGuide.vue'

describe('OnboardingGuide', () => {
  it('renders the three-step onboarding content and emits step actions', async () => {
    const wrapper = mount(OnboardingGuide, {
      props: {
        visible: true,
        initialStep: 1,
      },
    })

    expect(wrapper.text()).toContain('认识策略广场')
    expect(wrapper.text()).toContain('一键回测策略')
    expect(wrapper.text()).toContain('查看回测报告')

    await wrapper.get('[data-test="step-action"]').trigger('click')
    expect(wrapper.emitted('focus-target')?.[0]).toEqual(['strategy-library-entry'])

    await wrapper.get('[data-test="skip-onboarding"]').trigger('click')
    expect(wrapper.emitted('skip')).toHaveLength(1)
  })

  it('emits guided backtest launch from the second step', async () => {
    const wrapper = mount(OnboardingGuide, {
      props: {
        visible: true,
        initialStep: 2,
      },
    })

    await wrapper.get('[data-test="step-action"]').trigger('click')
    expect(wrapper.emitted('launch-guided-backtest')).toHaveLength(1)
  })
})

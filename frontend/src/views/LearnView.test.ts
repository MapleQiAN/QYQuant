import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import LearnView from './LearnView.vue'
import zh from '../i18n/messages/zh'

function mountLearnView() {
  const i18n = createI18n({
    legacy: false,
    locale: 'zh',
    globalInjection: true,
    messages: { zh },
  })

  return mount(LearnView, {
    global: {
      plugins: [i18n],
    },
  })
}

describe('LearnView', () => {
  it('renders a readable quant course layout with a left syllabus rail', () => {
    const wrapper = mountLearnView()

    expect(wrapper.find('.learn-shell').exists()).toBe(true)
    expect(wrapper.find('.learn-rail').exists()).toBe(true)
    expect(wrapper.find('.hero-summary-grid').exists()).toBe(true)
    expect(wrapper.find('.card-grid--map').exists()).toBe(true)
    expect(wrapper.find('.card-grid--metrics').exists()).toBe(true)
    expect(wrapper.find('.card-grid--ai').exists()).toBe(true)
    expect(wrapper.find('.card-grid--roadmap').exists()).toBe(true)
    expect(wrapper.find('.card-grid--resources').exists()).toBe(true)
    expect(wrapper.find('.hero-console').exists()).toBe(false)
    expect(wrapper.findAll('.editorial-title').length).toBeGreaterThanOrEqual(2)
    expect(wrapper.findAll('.syllabus-link').length).toBeGreaterThanOrEqual(6)
    expect(wrapper.text()).toContain('量化课程')
    expect(wrapper.text()).toContain('参数词典')
    expect(wrapper.text()).toContain('AI 策略工作流')
  })

  it('shows detailed quant parameters in readable Chinese', () => {
    const wrapper = mountLearnView()

    expect(wrapper.text()).toContain('初始资金')
    expect(wrapper.text()).toContain('滑点')
    expect(wrapper.text()).toContain('最大回撤')
    expect(wrapper.text()).toContain('Beta')
    expect(wrapper.text()).toContain('Walk-forward')
    expect(wrapper.text()).toContain('样本泄漏')
    expect(wrapper.text()).toContain('订单簿失衡')
    expect(wrapper.text()).toContain('概率校准')
  })
})

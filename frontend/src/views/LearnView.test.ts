import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import LearnView from './LearnView.vue'
import zh from '../i18n/messages/zh'

describe('LearnView', () => {
  it('renders the core beginner curriculum sections', () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh',
      globalInjection: true,
      messages: { zh }
    })

    const wrapper = mount(LearnView, {
      global: {
        plugins: [i18n]
      }
    })

    expect(wrapper.text()).toContain('量化入门教学')
    expect(wrapper.text()).toContain('知识框架')
    expect(wrapper.text()).toContain('研究流程')
    expect(wrapper.text()).toContain('指标与风控')
    expect(wrapper.text()).toContain('学习路线')
    expect(wrapper.text()).toContain('延伸阅读')
  })
})

// @vitest-environment jsdom
import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import NewStrategyView from './NewStrategyView.vue'

vi.mock('vue-router', () => ({
  RouterLink: {
    template: '<a><slot /></a>'
  }
}))

vi.mock('../api/strategies', () => ({
  createStrategy: vi.fn()
}))

vi.mock('../stores', () => ({
  useStrategiesStore: () => ({
    loadRecent: vi.fn()
  })
}))

function mountView() {
  return mount(NewStrategyView, {
    global: {
      plugins: [
        createI18n({
          legacy: false,
          globalInjection: true,
          locale: 'zh',
          messages: {
            zh: {
              pageTitle: {
                strategies: '策略'
              },
              strategyNew: {
                title: '新建策略',
                subtitle: '从零开始或导入一个 QYSP 包。',
                back: '返回概览',
                createTitle: '从零创建',
                createHint: '先填写基础信息，稍后也可以导入策略包。',
                nameLabel: '策略名称',
                namePlaceholder: '例如：黄金突破',
                symbolLabel: '主交易标的',
                symbolPlaceholder: '例如：XAUUSD',
                tagsLabel: '标签',
                tagsPlaceholder: '例如：gold, breakout, trend',
                createAction: '创建策略',
                resetAction: '重置',
                importTitle: '从文件导入',
                importHint: '上传包含 strategy.json 的 .qys 包。',
                importAction: '导入策略',
                createSuccess: '策略已创建',
                nameRequired: '请输入策略名称',
                symbolRequired: '请输入主交易标的',
                guideTitle: '策略编写指南',
                guideHint: '先写一个 strategy.py，再去导入页直接上传。',
                guideStep1: '写一个 on_bar(ctx, data) 函数。',
                guideStep2: '把文件保存成 strategy.py。',
                guideStep3: '前往导入页上传这个 Python 文件。',
                guidePrimaryAction: '新手教程',
                guideSecondaryAction: '进阶格式'
              }
            }
          }
        })
      ]
    }
  })
}

describe('NewStrategyView', () => {
  it('renders the strategy writing guide card with key references and CTAs', () => {
    const wrapper = mountView()
    const guideCard = wrapper.get('.guide-card')

    expect(guideCard.text()).toContain('策略编写指南')
    expect(guideCard.text()).toContain('strategy.py')
    expect(guideCard.text()).not.toContain('strategy.json')
    expect(guideCard.text()).not.toContain('src/strategy.py')
    expect(guideCard.text()).toContain('def on_bar(ctx: StrategyContext, data: BarData) -> list[Order]:')
    expect(wrapper.get('[data-testid="strategy-guide-primary"]').exists()).toBe(true)
    expect(wrapper.get('[data-testid="strategy-guide-secondary"]').exists()).toBe(true)
  })
})

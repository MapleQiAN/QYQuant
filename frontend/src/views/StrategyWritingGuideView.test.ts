// @vitest-environment jsdom
import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import StrategyWritingGuideView from './StrategyWritingGuideView.vue'

vi.mock('vue-router', () => ({
  RouterLink: {
    props: ['to'],
    template: '<a :data-route="typeof to === \'string\' ? to : to?.name"><slot /></a>',
  },
}))

function mountView() {
  return mount(StrategyWritingGuideView, {
    global: {
      plugins: [
        createI18n({
          legacy: false,
          globalInjection: true,
          locale: 'zh',
          messages: {
            zh: {
              pageTitle: {
                strategies: '策略',
              },
              strategyWritingGuide: {
                title: '策略编写指南',
                subtitle: '先写一个 strategy.py，再上传到导入页。',
                back: '返回策略创建',
                summaryTitle: '你将完成什么',
                summaryText: '先写出一个最小 Python 脚本，再上传导入。',
                summaryPoint1: '把策略逻辑写进单个 strategy.py。',
                summaryPoint2: '使用 event_v1 的 on_bar(ctx, data) 入口。',
                summaryPoint3: '上传到导入页，让系统分析入口函数。',
                scriptTitle: '先写一个 strategy.py',
                handlerTitle: 'on_bar(ctx, data) 示例',
                uploadTitle: '然后直接上传',
                uploadText: '把 strategy.py 上传到导入页，系统会自动识别 on_bar 入口。',
                uploadStep1: '打开 /strategies/import。',
                uploadStep2: '选择 strategy.py 文件。',
                uploadStep3: '确认分析结果后继续导入。',
                advancedTitle: '进阶：需要更多元数据时再做 .qys',
                advancedText: '如果你需要补充策略名称、参数、作者或 UI 信息，再准备 strategy.json 和 .qys 包。',
                advancedPoint1: '单文件 Python 上传适合先验证策略逻辑。',
                advancedPoint2: '需要完整元数据时，再补 strategy.json。',
                advancedPoint3: '最后才考虑把目录打包成 .qys。',
                packageTitle: '进阶目录结构',
                checklistTitle: '错误检查清单',
                checklistText: '如果 Python 文件导入失败，优先检查下面几项。',
                checklistItem1: '文件是否保存为 UTF-8 编码的 .py。',
                checklistItem2: '是否真的定义了 on_bar(ctx: StrategyContext, data: BarData) -> list[Order]。',
                checklistItem3: '返回值是否是 list[Order]，而不是 print 或其他对象。',
                specTitle: '规格参考',
                specText: '想进一步打包成 .qys 时，再查看完整规格。',
                specPathLabel: '完整字段参考：',
              },
            },
          },
        }),
      ],
    },
  })
}

describe('StrategyWritingGuideView', () => {
  it('renders the tutorial sections and back link to strategy creation', () => {
    const wrapper = mountView()

    expect(wrapper.text()).toContain('策略编写指南')
    expect(wrapper.text()).toContain('strategy.py')
    expect(wrapper.text()).toContain('event_v1')
    expect(wrapper.text()).toContain('打开 /strategies/import。')
    expect(wrapper.text()).toContain('.qys')
    expect(wrapper.text()).toContain('返回策略创建')
    expect(wrapper.get('[data-route="strategy-new"]').exists()).toBe(true)
    expect(wrapper.get('#spec-reference').exists()).toBe(true)
  })
})

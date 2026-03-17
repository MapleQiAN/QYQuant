// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import MetricTooltip from './MetricTooltip.vue'

describe('MetricTooltip', () => {
  it('shows the mapped explanation for a metric key', async () => {
    const wrapper = mount(MetricTooltip, {
      props: {
        metricKey: 'sharpe_ratio',
      },
    })

    await wrapper.get('[data-test="metric-tooltip-trigger"]').trigger('mouseenter')
    expect(wrapper.text()).toContain('夏普比率')
  })
})

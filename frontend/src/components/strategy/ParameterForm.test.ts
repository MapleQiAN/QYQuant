// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import ParameterForm from './ParameterForm.vue'

describe('ParameterForm', () => {
  it('renders controls by parameter type', async () => {
    const wrapper = mount(ParameterForm, {
      props: {
        definitions: [
          {
            name: 'window',
            type: 'int',
            default: 20,
            min: 5,
            max: 50,
            step: 1,
            description: 'Lookback window',
          },
          {
            name: 'mode',
            type: 'enum',
            default: 'long',
            options: ['long', 'short'],
            description: 'Trade direction',
          },
          {
            name: 'threshold',
            type: 'float',
            default: 1.5,
          },
          {
            name: 'label',
            type: 'string',
            default: 'demo',
          },
        ],
        modelValue: {},
      },
    })

    await flushPromises()

    expect(wrapper.find('[data-test="parameter-window-slider"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="parameter-mode-select"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="parameter-threshold-number"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="parameter-label-text"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="parameter-window-tooltip"]').attributes('title')).toBe('Lookback window')
  })

  it('shows validation errors in real time', async () => {
    const wrapper = mount(ParameterForm, {
      props: {
        definitions: [
          {
            name: 'window',
            type: 'int',
            min: 5,
            max: 50,
            default: 20,
          },
          {
            name: 'label',
            type: 'string',
            required: true,
            default: '',
          },
        ],
        modelValue: {
          window: 2,
          label: '',
        },
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('Must be at least 5')
    expect(wrapper.text()).toContain('This field is required')
    expect(wrapper.emitted('validation-change')?.at(-1)).toEqual([false])
  })
})

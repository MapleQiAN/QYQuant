// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import PresetManager from './PresetManager.vue'

describe('PresetManager', () => {
  it('emits selected preset id', async () => {
    const wrapper = mount(PresetManager, {
      props: {
        presets: [
          {
            id: 'preset-1',
            strategyId: 'strategy-1',
            userId: 'user-1',
            name: '稳健版',
            parameters: { window: 20 },
            createdAt: '2026-03-17T12:00:00+08:00',
          },
        ],
        selectedPresetId: '',
      },
    })

    await wrapper.get('[data-test="preset-select"]').setValue('preset-1')
    expect(wrapper.emitted('select')?.[0]).toEqual(['preset-1'])
  })

  it('opens save dialog and emits save/delete actions', async () => {
    const wrapper = mount(PresetManager, {
      props: {
        presets: [
          {
            id: 'preset-1',
            strategyId: 'strategy-1',
            userId: 'user-1',
            name: '稳健版',
            parameters: { window: 20 },
            createdAt: '2026-03-17T12:00:00+08:00',
          },
        ],
        selectedPresetId: 'preset-1',
      },
    })

    await wrapper.get('[data-test="open-save-preset"]').trigger('click')
    await wrapper.get('[data-test="preset-name-input"]').setValue('激进版')
    await wrapper.get('[data-test="confirm-save-preset"]').trigger('click')

    expect(wrapper.emitted('save')?.[0]).toEqual(['激进版'])

    await wrapper.get('[data-test="delete-preset"]').trigger('click')
    expect(wrapper.emitted('delete')?.[0]).toEqual(['preset-1'])
  })
})

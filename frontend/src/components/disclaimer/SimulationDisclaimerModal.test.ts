// @vitest-environment jsdom
import { beforeEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import SimulationDisclaimerModal from './SimulationDisclaimerModal.vue'

describe('SimulationDisclaimerModal', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('keeps the confirm action disabled until risk acknowledgement is checked', async () => {
    const activator = document.createElement('button')
    document.body.appendChild(activator)
    activator.focus()

    const wrapper = mount(SimulationDisclaimerModal, {
      attachTo: document.body,
      props: {
        modelValue: true,
      },
    })
    await nextTick()

    const dialog = document.body.querySelector('[data-test="simulation-disclaimer-dialog"]') as HTMLElement | null
    const confirmButton = document.body.querySelector('[data-test="simulation-disclaimer-confirm"]') as HTMLButtonElement | null

    expect(dialog?.getAttribute('role')).toBe('alertdialog')
    expect(dialog?.getAttribute('aria-modal')).toBe('true')
    expect(confirmButton?.getAttribute('disabled')).toBeDefined()
    expect(document.activeElement?.getAttribute('data-test')).toBe('simulation-disclaimer-close')

    const overlay = document.body.querySelector('[data-test="simulation-disclaimer-overlay"]') as HTMLElement | null
    overlay?.click()
    expect(wrapper.emitted('update:modelValue')).toBeFalsy()

    const checkbox = document.body.querySelector('[data-test="simulation-disclaimer-checkbox"]') as HTMLInputElement | null
    checkbox?.click()
    await nextTick()
    const enabledButton = document.body.querySelector('[data-test="simulation-disclaimer-confirm"]') as HTMLButtonElement | null
    expect(enabledButton?.getAttribute('disabled')).toBeNull()
  })
})

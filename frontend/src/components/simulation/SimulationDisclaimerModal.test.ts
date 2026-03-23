// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import SimulationDisclaimerModal from './SimulationDisclaimerModal.vue'

const { acceptDisclaimerMock } = vi.hoisted(() => ({
  acceptDisclaimerMock: vi.fn().mockResolvedValue(undefined),
}))

vi.mock('../../stores/useSimulationStore', () => ({
  useSimulationStore: () => ({
    acceptDisclaimer: acceptDisclaimerMock,
  }),
}))

describe('SimulationDisclaimerModal', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    acceptDisclaimerMock.mockClear()
  })

  it('keeps confirm disabled until checkbox is selected', async () => {
    const wrapper = mount(SimulationDisclaimerModal, {
      global: {
        plugins: [createPinia()],
      },
    })

    const confirmButton = wrapper.get('[data-test="simulation-disclaimer-confirm"]')
    expect(confirmButton.attributes('disabled')).toBeDefined()

    await wrapper.get('[data-test="simulation-disclaimer-checkbox"]').setValue(true)
    await nextTick()

    expect(confirmButton.attributes('disabled')).toBeUndefined()
  })

  it('accepts disclaimer and emits accepted event', async () => {
    const wrapper = mount(SimulationDisclaimerModal, {
      global: {
        plugins: [createPinia()],
      },
    })

    await wrapper.get('[data-test="simulation-disclaimer-checkbox"]').setValue(true)
    await wrapper.get('[data-test="simulation-disclaimer-confirm"]').trigger('click')

    expect(acceptDisclaimerMock).toHaveBeenCalledTimes(1)
    expect(wrapper.emitted('accepted')?.length).toBe(1)
  })
})

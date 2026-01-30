import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import ErrorState from './ErrorState.vue'

describe('ErrorState', () => {
  it('emits retry when action clicked', async () => {
    const i18n = createI18n({
      legacy: false,
      globalInjection: true,
      locale: 'en',
      messages: {
        en: {
          states: {
            errorTitle: 'Error'
          }
        }
      }
    })

    const wrapper = mount(ErrorState, {
      props: { message: 'Boom', actionLabel: 'Retry' },
      global: { plugins: [i18n] }
    })

    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('retry')).toBeTruthy()
  })
})

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import EmptyState from './EmptyState.vue'

describe('EmptyState', () => {
  it('renders default localized text', () => {
    const i18n = createI18n({
      legacy: false,
      globalInjection: true,
      locale: 'en',
      messages: {
        en: {
          states: {
            emptyTitle: 'Empty',
            emptyMessage: 'Nothing here'
          }
        }
      }
    })

    const wrapper = mount(EmptyState, {
      global: { plugins: [i18n] }
    })

    expect(wrapper.text()).toContain('Empty')
  })
})

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import SettingsView from './SettingsView.vue'
import { useUserStore } from '../stores/user'

describe('SettingsView', () => {
  it('toggles locale via store', async () => {
    setActivePinia(createPinia())
    const i18n = createI18n({
      legacy: false,
      globalInjection: true,
      locale: 'en',
      messages: {
        en: {
          settings: {
            title: 'Settings',
            language: 'Language',
            languageHint: 'Choose your interface language.',
            zh: '中文',
            en: 'EN'
          }
        },
        zh: {
          settings: {
            title: '设置',
            language: '语言',
            languageHint: '选择界面语言。',
            zh: '中文',
            en: 'EN'
          }
        }
      }
    })

    const wrapper = mount(SettingsView, {
      global: { plugins: [i18n] }
    })

    const store = useUserStore()
    expect(store.locale).toBeDefined()

    await wrapper.find('[data-locale="zh"]').trigger('click')
    expect(store.locale).toBe('zh')
  })
})

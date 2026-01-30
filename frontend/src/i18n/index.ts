import { createI18n } from 'vue-i18n'
import en from './messages/en'
import zh from './messages/zh'

export const LOCALE_KEY = 'qyquant_locale'

export const SUPPORTED_LOCALES = ['en', 'zh'] as const
export type Locale = (typeof SUPPORTED_LOCALES)[number]

function isLocale(value: string | null): value is Locale {
  return value === 'en' || value === 'zh'
}

export function resolveInitialLocale(): Locale {
  if (typeof window === 'undefined') {
    return 'en'
  }

  const stored = localStorage.getItem(LOCALE_KEY)
  if (isLocale(stored)) {
    return stored
  }

  const browser = navigator.language.toLowerCase()
  if (browser.startsWith('zh')) {
    return 'zh'
  }

  return 'en'
}

export const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: resolveInitialLocale(),
  fallbackLocale: 'en',
  messages: { en, zh }
})

export function setLocale(locale: Locale) {
  i18n.global.locale.value = locale
  if (typeof window !== 'undefined') {
    localStorage.setItem(LOCALE_KEY, locale)
  }
}

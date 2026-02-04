import { defineStore } from 'pinia'
import type { User } from '../types/User'
import { resolveInitialLocale, setLocale, type Locale } from '../i18n'
import { applyMarketStyle, resolveInitialMarketStyle, type MarketStyle } from '../styles/marketStyle'

const defaultUser: User = {
  name: 'Quant Pro',
  avatar: 'Q',
  level: 'Pro',
  notifications: 3
}

export const useUserStore = defineStore('user', {
  state: () => ({
    profile: defaultUser,
    locale: resolveInitialLocale(),
    marketStyle: resolveInitialMarketStyle()
  }),
  actions: {
    setLocale(next: Locale) {
      this.locale = next
      setLocale(next)
    },
    setMarketStyle(next: MarketStyle) {
      this.marketStyle = next
      applyMarketStyle(next)
    }
  }
})

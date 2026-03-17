import { defineStore } from 'pinia'
import type { User } from '../types/User'
import type { UserProfileResponse } from '../types/User'
import { resolveInitialLocale, setLocale, type Locale } from '../i18n'
import { applyMarketStyle, resolveInitialMarketStyle, type MarketStyle } from '../styles/marketStyle'
import { fetchProfile, updateOnboardingCompleted } from '../api/users'

const defaultUser: User = {
  id: undefined,
  name: 'Quant Pro',
  avatar: 'Q',
  level: 'Pro',
  notifications: 3,
  nickname: 'Quant Pro',
  avatar_url: '',
  bio: '',
  role: 'user',
  plan_level: 'free',
  is_banned: false,
  onboarding_completed: true,
  phone: '',
  created_at: undefined,
  updated_at: undefined,
}

export const useUserStore = defineStore('user', {
  state: () => ({
    profile: defaultUser,
    locale: resolveInitialLocale(),
    marketStyle: resolveInitialMarketStyle(),
    profileLoading: false,
    profileLoaded: false,
    guidedBacktestActive: false,
    guidedBacktestStep: null as number | null,
    guidedBacktestStrategyId: null as string | null,
    guidedBacktestJobId: null as string | null,
    helpPanelOpen: false,
    onboardingHighlightTarget: null as string | null,
  }),
  actions: {
    applyRemoteProfile(profile: UserProfileResponse) {
      this.profile = {
        ...this.profile,
        id: profile.id,
        name: profile.nickname,
        avatar: profile.nickname?.slice(0, 1)?.toUpperCase() || 'Q',
        level: profile.plan_level?.toUpperCase() || this.profile.level,
        nickname: profile.nickname,
        avatar_url: profile.avatar_url,
        bio: profile.bio,
        role: profile.role,
        plan_level: profile.plan_level,
        is_banned: profile.is_banned,
        onboarding_completed: profile.onboarding_completed,
        phone: profile.phone,
        created_at: profile.created_at,
        updated_at: profile.updated_at,
      }
      this.profileLoaded = true
    },
    async loadProfile() {
      if (this.profileLoading || this.profileLoaded) {
        return
      }
      if (typeof window === 'undefined') {
        return
      }
      const token = window.localStorage.getItem('qyquant-token')
      if (!token) {
        this.profileLoaded = true
        return
      }

      this.profileLoading = true
      try {
        const profile = await fetchProfile()
        this.applyRemoteProfile(profile)
      } finally {
        this.profileLoading = false
      }
    },
    async markOnboardingCompleted(completed = true) {
      if (!this.profile.id) {
        this.profile.onboarding_completed = completed
        return
      }
      const profile = await updateOnboardingCompleted(this.profile.id, completed)
      this.applyRemoteProfile(profile)
    },
    startGuidedBacktest(strategyId?: string) {
      this.guidedBacktestActive = true
      this.guidedBacktestStep = 1
      this.guidedBacktestStrategyId = strategyId ?? null
      this.guidedBacktestJobId = null
      this.onboardingHighlightTarget = 'guided-strategy-card'
    },
    setGuidedBacktestStep(step: number | null) {
      this.guidedBacktestStep = step
    },
    setGuidedBacktestStrategy(strategyId: string | null) {
      this.guidedBacktestStrategyId = strategyId
    },
    setGuidedBacktestJob(jobId: string | null) {
      this.guidedBacktestJobId = jobId
    },
    finishGuidedBacktest() {
      this.guidedBacktestActive = false
      this.guidedBacktestStep = null
      this.guidedBacktestStrategyId = null
      this.guidedBacktestJobId = null
      this.onboardingHighlightTarget = null
    },
    cancelGuidedBacktest() {
      this.finishGuidedBacktest()
    },
    setHelpPanelOpen(open: boolean) {
      this.helpPanelOpen = open
    },
    setOnboardingHighlightTarget(target: string | null) {
      this.onboardingHighlightTarget = target
    },
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

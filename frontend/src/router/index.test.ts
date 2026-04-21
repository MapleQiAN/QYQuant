// @vitest-environment jsdom
import { beforeEach, describe, it, expect, vi } from 'vitest'
import { toast } from '../lib/toast'
import { pinia } from '../stores/pinia'

const storage = vi.hoisted(() => {
  const values = new Map<string, string>()

  const api = {
    getItem(key: string) {
      return values.has(key) ? values.get(key)! : null
    },
    setItem(key: string, value: string) {
      values.set(key, value)
    },
    removeItem(key: string) {
      values.delete(key)
    },
    clear() {
      values.clear()
    }
  }

  Object.defineProperty(globalThis, 'localStorage', {
    value: api,
    configurable: true,
  })

  return api
})

vi.mock('../views/DashboardView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/BacktestsView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/BacktestResultView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/BotsView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/ForumView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/PostDetailView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/SettingsView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/NewStrategyView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/StrategyLibraryView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/StrategyImportView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/StrategyImportConfirmView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/StrategyWritingGuideView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/StrategyDetailView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/Marketplace.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/MarketplaceStrategyDetailView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/PricingView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/LearnView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/UserProfileView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/admin/AdminDashboard.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/admin/DataSourceHealth.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/admin/StrategyReview.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/admin/ReportManagement.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/admin/BacktestMonitor.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/admin/UserManagement.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/ForgotPasswordView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/ResetPasswordView.vue', () => ({ default: { template: '<div />' } }))

import router from './index'
import { useUserStore } from '../stores'

describe('router', () => {
  beforeEach(async () => {
    useUserStore(pinia).$dispose()
    useUserStore(pinia)
    storage.clear()
    vi.restoreAllMocks()
    vi.stubGlobal('scrollTo', vi.fn())
    vi.spyOn(toast, 'error').mockImplementation(() => undefined)
    await router.push('/')
    await router.isReady()
  })

  it('contains dashboard route', () => {
    const hasDashboard = router.getRoutes().some((route) => route.path === '/')
    expect(hasDashboard).toBe(true)
  })

  it('contains settings route', () => {
    const hasSettings = router.getRoutes().some((route) => route.path === '/settings')
    expect(hasSettings).toBe(true)
  })

  it('contains backtest report route', () => {
    const hasReport = router.getRoutes().some((route) => route.path === '/backtests/:jobId/report')
    expect(hasReport).toBe(true)
  })

  it('contains strategy library route', () => {
    const hasStrategyLibrary = router.getRoutes().some((route) => route.path === '/strategies')
    expect(hasStrategyLibrary).toBe(true)
  })

  it('contains strategy writing guide route', () => {
    const hasStrategyWritingGuide = router.getRoutes().some((route) => route.path === '/strategies/guide')
    expect(hasStrategyWritingGuide).toBe(true)
  })

  it('contains strategy parameter route', () => {
    const hasStrategyDetail = router.getRoutes().some((route) => route.path === '/strategies/:strategyId/parameters')
    expect(hasStrategyDetail).toBe(true)
  })

  it('contains strategy import routes', () => {
    const hasImport = router.getRoutes().some((route) => route.path === '/strategies/import')
    const hasImportConfirm = router.getRoutes().some((route) => route.path === '/strategies/import/confirm')

    expect(hasImport).toBe(true)
    expect(hasImportConfirm).toBe(true)
  })

  it('contains marketplace route', () => {
    const hasMarketplace = router.getRoutes().some((route) => route.path === '/marketplace')
    expect(hasMarketplace).toBe(true)
  })

  it('contains marketplace strategy detail route', () => {
    const hasMarketplaceStrategyDetail = router.getRoutes().some(
      (route) => route.path === '/marketplace/strategies/:strategyId'
    )
    expect(hasMarketplaceStrategyDetail).toBe(true)
  })

  it('contains forum post detail route', () => {
    const hasForumPostDetail = router.getRoutes().some((route) => route.path === '/forum/posts/:postId')
    expect(hasForumPostDetail).toBe(true)
  })

  it('contains pricing route', () => {
    const hasPricing = router.getRoutes().some((route) => route.path === '/pricing')
    expect(hasPricing).toBe(true)
  })

  it('contains learn route', () => {
    const hasLearn = router.getRoutes().some((route) => route.path === '/learn')
    expect(hasLearn).toBe(true)
  })

  it('contains forgot password route', () => {
    const hasRoute = router.getRoutes().some((route) => route.path === '/forgot-password')
    expect(hasRoute).toBe(true)
  })

  it('contains reset password route', () => {
    const hasRoute = router.getRoutes().some((route) => route.path === '/reset-password')
    expect(hasRoute).toBe(true)
  })

  it('contains admin route', () => {
    const adminRoute = router.getRoutes().find((route) => route.path === '/admin')

    expect(adminRoute).toBeTruthy()
    expect(adminRoute?.meta.requiresAdmin).toBe(true)
  })

  it('contains admin strategy review route', () => {
    const reviewRoute = router.getRoutes().find((route) => route.path === '/admin/strategies')

    expect(reviewRoute).toBeTruthy()
    expect(reviewRoute?.meta.requiresAdmin).toBe(true)
  })

  it('contains admin data source health route', () => {
    const dataSourceRoute = router.getRoutes().find((route) => route.path === '/admin/data-source-health')

    expect(dataSourceRoute).toBeTruthy()
    expect(dataSourceRoute?.meta.requiresAdmin).toBe(true)
  })

  it('contains admin report management route', () => {
    const reportRoute = router.getRoutes().find((route) => route.path === '/admin/reports')

    expect(reportRoute).toBeTruthy()
    expect(reportRoute?.meta.requiresAdmin).toBe(true)
  })

  it('contains admin backtest monitor route', () => {
    const monitorRoute = router.getRoutes().find((route) => route.path === '/admin/backtest-monitor')

    expect(monitorRoute).toBeTruthy()
    expect(monitorRoute?.meta.requiresAdmin).toBe(true)
  })

  it('contains admin user management route', () => {
    const userManagementRoute = router.getRoutes().find((route) => route.path === '/admin/user-management')

    expect(userManagementRoute).toBeTruthy()
    expect(userManagementRoute?.meta.requiresAdmin).toBe(true)
  })

  it('does not inject the frontend test account on protected routes', async () => {
    const userStore = useUserStore(pinia)

    expect(userStore.profile.role).toBe('user')
    expect(userStore.profileLoaded).toBe(false)
    expect(localStorage.getItem('qyquant-token')).toBeNull()

    await router.push('/settings')

    expect(localStorage.getItem('qyquant-token')).toBeNull()
    expect(userStore.profile.role).toBe('user')
    expect(userStore.profileLoaded).toBe(false)
    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/settings')
  })

  it('redirects unauthenticated users to login from protected routes', async () => {
    await router.push('/backtests')

    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/backtests')
  })

  it('redirects non-admin users away from admin route', async () => {
    localStorage.setItem('qyquant-token', 'test-token')
    useUserStore(pinia).$dispose()
    const userStore = useUserStore(pinia)
    userStore.profile.role = 'user'
    userStore.profileLoaded = true

    await router.push('/admin')

    expect(router.currentRoute.value.path).toBe('/')
    expect(toast.error).toHaveBeenCalled()
  })

  it('allows admin users to visit admin route', async () => {
    localStorage.setItem('qyquant-token', 'test-token')
    useUserStore(pinia).$dispose()
    const userStore = useUserStore(pinia)
    userStore.profile.role = 'admin'
    userStore.profileLoaded = true

    await router.push('/admin')

    expect(router.currentRoute.value.path).toBe('/admin')
  })

  it('does not block non-admin protected routes while profile is already loading', async () => {
    localStorage.setItem('qyquant-token', 'real-token')
    useUserStore(pinia).$dispose()
    const userStore = useUserStore(pinia)
    userStore.profileLoading = true
    userStore.profileLoaded = false

    const navigation = router.push('/settings').then(() => 'navigated')
    const result = await Promise.race([
      navigation,
      new Promise((resolve) => setTimeout(() => resolve('blocked'), 10)),
    ])

    if (result === 'blocked') {
      userStore.profile.role = 'user'
      userStore.profileLoaded = true
      userStore.profileLoading = false
      await navigation
    }

    expect(result).toBe('navigated')
    expect(router.currentRoute.value.path).toBe('/settings')
  })

  it('requires a real admin profile for admin routes', async () => {
    localStorage.setItem('qyquant-token', 'real-token')
    useUserStore(pinia).$dispose()
    const userStore = useUserStore(pinia)
    userStore.profile.role = 'user'
    userStore.profileLoaded = true

    await router.push('/admin/reports')

    expect(router.currentRoute.value.path).toBe('/')
    expect(toast.error).toHaveBeenCalled()
  })

  it('waits for profile loading to settle before checking admin access', async () => {
    localStorage.setItem('qyquant-token', 'real-token')
    useUserStore(pinia).$dispose()
    const userStore = useUserStore(pinia)
    userStore.profileLoading = true
    userStore.profileLoaded = false

    const finishLoading = setTimeout(() => {
      userStore.profile.role = 'admin'
      userStore.profileLoaded = true
      userStore.profileLoading = false
    }, 0)

    await router.push('/admin')
    clearTimeout(finishLoading)

    expect(router.currentRoute.value.path).toBe('/admin')
    expect(toast.error).not.toHaveBeenCalled()
  })
})

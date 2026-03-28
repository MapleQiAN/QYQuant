// @vitest-environment jsdom
import { beforeEach, describe, it, expect, vi } from 'vitest'
import { setActivePinia } from 'pinia'
import { toast } from '../lib/toast'
import { pinia } from '../stores/pinia'

vi.mock('../views/DashboardView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/BacktestsView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/BacktestResultView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/BotsView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/ForumView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/PostDetailView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/SettingsView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/NewStrategyView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/StrategyLibraryView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/StrategyDetailView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/Marketplace.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/MarketplaceStrategyDetailView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/PricingView.vue', () => ({ default: { template: '<div />' } }))
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
    ;(pinia as any)._s.clear()
    setActivePinia(pinia)
    localStorage.clear()
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

  it('contains strategy parameter route', () => {
    const hasStrategyDetail = router.getRoutes().some((route) => route.path === '/strategies/:strategyId/parameters')
    expect(hasStrategyDetail).toBe(true)
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

  it('redirects non-admin users away from admin route', async () => {
    const userStore = useUserStore()
    userStore.profile.role = 'user'
    userStore.profileLoaded = true
    localStorage.setItem('qyquant-token', 'test-token')

    await router.push('/admin')

    expect(router.currentRoute.value.path).toBe('/')
    expect(toast.error).toHaveBeenCalledWith('无权限')
  })

  it('allows admin users to visit admin route', async () => {
    const userStore = useUserStore()
    userStore.profile.role = 'admin'
    userStore.profileLoaded = true
    localStorage.setItem('qyquant-token', 'test-token')

    await router.push('/admin')

    expect(router.currentRoute.value.path).toBe('/admin')
  })
})

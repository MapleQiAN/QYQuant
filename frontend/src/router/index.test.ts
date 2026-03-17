// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'

vi.mock('../views/DashboardView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/BacktestsView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/BacktestResultView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/BotsView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/ForumView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/SettingsView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../views/NewStrategyView.vue', () => ({ default: { template: '<div />' } }))

import router from './index'

describe('router', () => {
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
})

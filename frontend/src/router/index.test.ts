// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import router from './index'

describe('router', () => {
  it('contains dashboard route', () => {
    const hasDashboard = router.getRoutes().some((route) => route.path === '/')
    expect(hasDashboard).toBe(true)
  })
})

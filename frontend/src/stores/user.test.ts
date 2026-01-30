import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from './user'

describe('user store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('updates locale', () => {
    const store = useUserStore()
    store.setLocale('zh')
    expect(store.locale).toBe('zh')
  })
})

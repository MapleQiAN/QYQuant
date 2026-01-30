import { describe, it, expect } from 'vitest'
import { handlers } from './handlers'

describe('handlers', () => {
  it('exports handlers array', () => {
    expect(Array.isArray(handlers)).toBe(true)
  })
})

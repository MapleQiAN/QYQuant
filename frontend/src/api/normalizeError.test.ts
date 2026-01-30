import { describe, it, expect } from 'vitest'
import { normalizeError } from './normalizeError'

describe('normalizeError', () => {
  it('normalizes axios-like error', () => {
    const err = {
      response: { status: 500, data: { message: 'boom' } },
      message: 'Request failed'
    }
    expect(normalizeError(err)).toEqual({
      status: 500,
      message: 'boom'
    })
  })
})

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

  it('reads nested backend error payloads', () => {
    const err = {
      response: {
        status: 403,
        data: {
          error: {
            code: 'SIMULATION_SLOT_LIMIT_REACHED',
            message: 'Current plan supports at most 1 active simulation bots',
          },
        },
      },
      message: 'Request failed',
    }

    expect(normalizeError(err)).toEqual({
      status: 403,
      code: 'SIMULATION_SLOT_LIMIT_REACHED',
      message: 'Current plan supports at most 1 active simulation bots',
    })
  })
})

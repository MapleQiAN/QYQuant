import { describe, expect, it } from 'vitest'
import {
  BACKTEST_FOOTER_DISCLAIMER,
  REGISTRATION_DISCLAIMER,
  SIMULATION_DISCLAIMER,
  STRATEGY_TOOLTIP_DISCLAIMER,
  DISCLAIMER_CONTENT,
} from './disclaimer-content'

describe('disclaimer-content', () => {
  it('exports non-empty disclaimer copy for all supported contexts', () => {
    expect(REGISTRATION_DISCLAIMER).toBeTruthy()
    expect(BACKTEST_FOOTER_DISCLAIMER).toBeTruthy()
    expect(STRATEGY_TOOLTIP_DISCLAIMER).toBeTruthy()
    expect(SIMULATION_DISCLAIMER).toBeTruthy()
    expect(DISCLAIMER_CONTENT.registration).toBe(REGISTRATION_DISCLAIMER)
    expect(DISCLAIMER_CONTENT['backtest-footer']).toBe(BACKTEST_FOOTER_DISCLAIMER)
    expect(DISCLAIMER_CONTENT['strategy-tooltip']).toBe(STRATEGY_TOOLTIP_DISCLAIMER)
    expect(DISCLAIMER_CONTENT['simulation-modal']).toBe(SIMULATION_DISCLAIMER)
  })
})

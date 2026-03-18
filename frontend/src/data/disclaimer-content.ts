export type DisclaimerType =
  | 'registration'
  | 'backtest-footer'
  | 'strategy-tooltip'
  | 'simulation-modal'

export const REGISTRATION_DISCLAIMER =
  '我已阅读并同意《服务协议》与《免责声明》，了解本平台不构成任何投资建议'

export const BACKTEST_FOOTER_DISCLAIMER = '基于历史数据，不构成投资建议'

export const STRATEGY_TOOLTIP_DISCLAIMER = '仅供参考，历史表现不代表未来收益'

export const SIMULATION_DISCLAIMER =
  '模拟托管仅用于学习和策略验证目的，不构成实际投资建议，模拟收益不代表真实交易收益'

export const DISCLAIMER_CONTENT: Record<DisclaimerType, string> = {
  registration: REGISTRATION_DISCLAIMER,
  'backtest-footer': BACKTEST_FOOTER_DISCLAIMER,
  'strategy-tooltip': STRATEGY_TOOLTIP_DISCLAIMER,
  'simulation-modal': SIMULATION_DISCLAIMER,
}

export function getDisclaimerContent(type: DisclaimerType) {
  return DISCLAIMER_CONTENT[type]
}

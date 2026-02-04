export type MarketStyle = 'cn' | 'us'

export const MARKET_STYLE_KEY = 'qyquant_market_style'

export function resolveInitialMarketStyle(): MarketStyle {
  if (typeof localStorage === 'undefined') {
    return 'cn'
  }
  const value = localStorage.getItem(MARKET_STYLE_KEY)
  return value === 'us' ? 'us' : 'cn'
}

export function applyMarketStyle(style: MarketStyle) {
  if (typeof document !== 'undefined') {
    document.documentElement.dataset.marketStyle = style
  }
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(MARKET_STYLE_KEY, style)
  }
}

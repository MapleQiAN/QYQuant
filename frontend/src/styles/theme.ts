export type Theme = 'dark' | 'light'

export const THEME_KEY = 'qyquant_theme'

export function resolveInitialTheme(): Theme {
  if (typeof localStorage === 'undefined' || typeof localStorage.getItem !== 'function') {
    return 'dark'
  }
  const value = localStorage.getItem(THEME_KEY)
  if (value === 'light' || value === 'dark') return value
  // Check system preference
  if (typeof window !== 'undefined' && window.matchMedia?.('(prefers-color-scheme: light)').matches) {
    return 'light'
  }
  return 'dark'
}

export function applyTheme(theme: Theme) {
  if (typeof document !== 'undefined') {
    document.documentElement.dataset.theme = theme
  }
  if (typeof localStorage !== 'undefined' && typeof localStorage.setItem === 'function') {
    localStorage.setItem(THEME_KEY, theme)
  }
}

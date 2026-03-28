// ============================================
// Design Tokens - QY Quant Dashboard
// Financial Professional Theme
// ============================================

export const designTokens = {
  colors: {
    dark: {
      primary: '#2563EB',
      primaryLight: '#3B82F6',
      primaryDark: '#1D4ED8',
      primaryBg: 'rgba(37, 99, 235, 0.12)',
      secondary: '#64748B',
      accent: '#F59E0B',
      success: '#22C55E',
      warning: '#F59E0B',
      danger: '#EF4444',
      info: '#3B82F6',
      background: '#0B0E14',
      surface: '#141821',
      surfaceElevated: '#1A2030',
      border: '#1E2736',
      borderLight: '#172033',
      textPrimary: '#E8ECF1',
      textSecondary: '#8B95A5',
      textMuted: '#5A6577',
      navBg: '#0D1117',
    },
    light: {
      primary: '#1D4ED8',
      primaryLight: '#2563EB',
      primaryDark: '#1E40AF',
      primaryBg: 'rgba(29, 78, 216, 0.08)',
      secondary: '#64748B',
      accent: '#D97706',
      success: '#16A34A',
      warning: '#D97706',
      danger: '#DC2626',
      info: '#2563EB',
      background: '#F0F2F5',
      surface: '#FFFFFF',
      surfaceElevated: '#FFFFFF',
      border: '#D5DAE1',
      borderLight: '#E8ECF1',
      textPrimary: '#111827',
      textSecondary: '#4B5563',
      textMuted: '#9CA3AF',
      navBg: '#FFFFFF',
    },
  },

  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '48px',
    xxxl: '64px',
  },

  radius: {
    xs: '4px',
    sm: '6px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    full: '9999px',
  },

  shadows: {
    sm: '0 1px 3px rgba(0, 0, 0, 0.3)',
    md: '0 2px 8px rgba(0, 0, 0, 0.35)',
    lg: '0 4px 16px rgba(0, 0, 0, 0.4)',
  },

  typography: {
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontMono: "'JetBrains Mono', 'Fira Code', 'SF Mono', 'Consolas', monospace",
    fontSizes: {
      xs: '11px',
      sm: '13px',
      md: '14px',
      lg: '16px',
      xl: '18px',
      xxl: '22px',
      xxxl: '28px',
      display: '36px',
    },
    fontWeights: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeights: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.75,
    },
  },

  transitions: {
    fast: '150ms ease',
    normal: '200ms ease',
    slow: '300ms ease',
  },

  grid: {
    columns: 12,
    gap: '16px',
    containerMaxWidth: '1440px',
  },

  nav: {
    height: '48px',
  },
} as const

export type DesignTokens = typeof designTokens

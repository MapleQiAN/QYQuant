// ============================================
// Design Tokens - QY Quant Terminal
// Professional Financial Terminal Theme
// ============================================

export const designTokens = {
  colors: {
    dark: {
      primary: '#2563EB',
      primaryLight: '#3B82F6',
      primaryDark: '#1D4ED8',
      primaryBg: 'rgba(37, 99, 235, 0.10)',
      secondary: '#64748B',
      accent: '#F59E0B',
      success: '#22C55E',
      warning: '#F59E0B',
      danger: '#EF4444',
      info: '#3B82F6',
      background: '#080B11',
      surface: '#0E1219',
      surfaceElevated: '#141A24',
      border: '#1A1F2E',
      borderLight: '#141A24',
      textPrimary: '#E2E8F0',
      textSecondary: '#8B95A5',
      textMuted: '#4A5568',
      navBg: '#0A0E15',
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
    '2xs': '2px',
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '24px',
    xxl: '32px',
    xxxl: '48px',
  },

  radius: {
    xs: '2px',
    sm: '3px',
    md: '4px',
    lg: '6px',
    xl: '8px',
    full: '9999px',
  },

  shadows: {
    sm: '0 1px 2px rgba(0, 0, 0, 0.2)',
    md: '0 2px 4px rgba(0, 0, 0, 0.25)',
    lg: '0 4px 8px rgba(0, 0, 0, 0.3)',
  },

  typography: {
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontMono: "'JetBrains Mono', 'Fira Code', 'SF Mono', 'Consolas', monospace",
    fontSizes: {
      '2xs': '10px',
      xs: '11px',
      sm: '12px',
      md: '13px',
      lg: '14px',
      xl: '16px',
      xxl: '20px',
      xxxl: '24px',
      display: '32px',
    },
    fontWeights: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeights: {
      tight: 1.2,
      normal: 1.4,
      relaxed: 1.6,
    },
  },

  transitions: {
    fast: '120ms ease',
    normal: '180ms ease',
    slow: '250ms ease',
  },

  grid: {
    columns: 12,
    gap: '8px',
    containerMaxWidth: '1600px',
  },

  layout: {
    sidebarWidth: '48px',
    panelHeaderHeight: '32px',
    statusBarHeight: '24px',
    navHeight: '40px',
  },
} as const

export type DesignTokens = typeof designTokens

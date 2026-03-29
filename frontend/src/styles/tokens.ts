// ============================================
// Design Tokens - QY Quant
// Enterprise Financial Theme
// ============================================

export const designTokens = {
  colors: {
    dark: {
      primary: '#2563EB',
      primaryLight: '#3B82F6',
      primaryDark: '#1D4ED8',
      primaryBg: 'rgba(37, 99, 235, 0.10)',
      primaryBorder: 'rgba(37, 99, 235, 0.25)',
      secondary: '#64748B',
      accent: '#F59E0B',
      success: '#22C55E',
      warning: '#F59E0B',
      danger: '#EF4444',
      info: '#3B82F6',
      background: '#06080D',
      surface: '#0C1019',
      surfaceElevated: '#111722',
      surfaceHover: '#161D2A',
      border: 'rgba(255, 255, 255, 0.06)',
      borderLight: 'rgba(255, 255, 255, 0.04)',
      borderHover: 'rgba(255, 255, 255, 0.10)',
      textPrimary: '#F0F2F5',
      textSecondary: '#8B95A5',
      textMuted: '#4E5B6E',
      sidebarBg: '#080B12',
      navBg: '#0A0E16',
    },
    light: {
      primary: '#1D4ED8',
      primaryLight: '#2563EB',
      primaryDark: '#1E40AF',
      primaryBg: 'rgba(29, 78, 216, 0.06)',
      primaryBorder: 'rgba(29, 78, 216, 0.20)',
      secondary: '#64748B',
      accent: '#D97706',
      success: '#16A34A',
      warning: '#D97706',
      danger: '#DC2626',
      info: '#2563EB',
      background: '#F4F5F7',
      surface: '#FFFFFF',
      surfaceElevated: '#FFFFFF',
      surfaceHover: '#F8F9FB',
      border: '#E2E5EA',
      borderLight: '#EBEDF1',
      borderHover: '#C8CDD5',
      textPrimary: '#0F172A',
      textSecondary: '#475569',
      textMuted: '#94A3B8',
      sidebarBg: '#FFFFFF',
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
    lg: '10px',
    xl: '12px',
    full: '9999px',
  },

  shadows: {
    xs: '0 1px 2px rgba(0, 0, 0, 0.4)',
    sm: '0 1px 3px rgba(0, 0, 0, 0.5), 0 1px 2px rgba(0, 0, 0, 0.3)',
    md: '0 4px 12px rgba(0, 0, 0, 0.5), 0 1px 4px rgba(0, 0, 0, 0.3)',
    lg: '0 8px 24px rgba(0, 0, 0, 0.6), 0 2px 8px rgba(0, 0, 0, 0.4)',
    xl: '0 16px 48px rgba(0, 0, 0, 0.7), 0 4px 16px rgba(0, 0, 0, 0.5)',
  },

  typography: {
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontMono: "'JetBrains Mono', 'Fira Code', 'SF Mono', 'Consolas', monospace",
    fontSizes: {
      xs: '11px',
      sm: '12px',
      md: '13px',
      lg: '14px',
      xl: '16px',
      xxl: '20px',
      xxxl: '26px',
      display: '32px',
      hero: '40px',
    },
    fontWeights: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeights: {
      tight: 1.2,
      normal: 1.5,
      relaxed: 1.75,
    },
    letterSpacing: {
      tight: '-0.02em',
      normal: '0',
      wide: '0.04em',
      wider: '0.08em',
    },
  },

  transitions: {
    fast: '150ms ease',
    normal: '200ms ease',
    slow: '300ms ease',
    easeOutExpo: 'cubic-bezier(0.16, 1, 0.3, 1)',
  },

  grid: {
    columns: 12,
    gap: '16px',
    containerMaxWidth: '1440px',
  },

  layout: {
    sidebarWidth: '220px',
    sidebarCollapsedWidth: '60px',
    navHeight: '48px',
  },
} as const

export type DesignTokens = typeof designTokens

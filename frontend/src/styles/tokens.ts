// Design Tokens - QY Quant

export const designTokens = {
  colors: {
    dark: {
      primary: '#7c6dd8',
      primaryLight: '#9585e6',
      primaryDark: '#5f4fc4',
      primaryBg: 'rgba(124, 109, 216, 0.10)',
      primaryBorder: 'rgba(124, 109, 216, 0.20)',
      secondary: '#6e6e8a',
      accent: '#36d6b6',
      success: '#36d6b6',
      warning: '#f0b429',
      danger: '#f06868',
      info: '#7c6dd8',
      background: '#0c0c1d',
      surface: '#161630',
      surfaceElevated: '#1c1c3a',
      surfaceHover: '#22224a',
      border: 'rgba(255, 255, 255, 0.06)',
      borderLight: 'rgba(255, 255, 255, 0.03)',
      borderHover: 'rgba(255, 255, 255, 0.10)',
      textPrimary: '#ebebf5',
      textSecondary: '#8888a0',
      textMuted: '#55556e',
      sidebarBg: '#0e0e22',
      navBg: '#0e0e22',
    },
    light: {
      primary: '#6354c0',
      primaryLight: '#7c6dd8',
      primaryDark: '#4e40a8',
      primaryBg: 'rgba(99, 84, 192, 0.06)',
      primaryBorder: 'rgba(99, 84, 192, 0.15)',
      secondary: '#6e6e8a',
      accent: '#2bb89e',
      success: '#2bb89e',
      warning: '#d99e1e',
      danger: '#d95555',
      info: '#6354c0',
      background: '#f0f0f5',
      surface: '#ffffff',
      surfaceElevated: '#ffffff',
      surfaceHover: '#f5f5fa',
      border: '#e0e0ea',
      borderLight: '#ebebf0',
      borderHover: '#d0d0dd',
      textPrimary: '#1a1a2e',
      textSecondary: '#6e6e8a',
      textMuted: '#9898b0',
      sidebarBg: '#ffffff',
      navBg: '#ffffff',
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
    xs: '6px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '20px',
    full: '9999px',
  },

  shadows: {
    xs: '0 1px 2px rgba(0, 0, 0, 0.3)',
    sm: '0 2px 6px rgba(0, 0, 0, 0.25)',
    md: '0 4px 12px rgba(0, 0, 0, 0.3)',
    lg: '0 8px 24px rgba(0, 0, 0, 0.35)',
    xl: '0 16px 40px rgba(0, 0, 0, 0.4)',
  },

  typography: {
    fontFamily: "'DM Sans', 'KaiTi', 'STKaiti', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontMono: "'DM Mono', 'JetBrains Mono', 'Courier New', monospace",
    fontSizes: {
      xs: '12px',
      sm: '13px',
      md: '14px',
      lg: '15px',
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

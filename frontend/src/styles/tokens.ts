// ============================================
// Design Tokens - QY Quant Dashboard
// ============================================

export const designTokens = {
  // Colors - Low saturation fintech palette
  colors: {
    // Primary
    primary: '#6366f1',
    primaryLight: '#818cf8',
    primaryDark: '#4f46e5',
    primaryBg: 'rgba(99, 102, 241, 0.08)',
    
    // Secondary
    secondary: '#64748b',
    secondaryLight: '#94a3b8',
    secondaryDark: '#475569',
    
    // Status
    success: '#10b981',
    successBg: 'rgba(16, 185, 129, 0.1)',
    warning: '#f59e0b',
    warningBg: 'rgba(245, 158, 11, 0.1)',
    danger: '#ef4444',
    dangerBg: 'rgba(239, 68, 68, 0.1)',
    info: '#3b82f6',
    infoBg: 'rgba(59, 130, 246, 0.1)',
    
    // Neutral
    white: '#ffffff',
    background: '#f8fafc',
    surface: '#ffffff',
    border: '#e2e8f0',
    borderLight: '#f1f5f9',
    
    // Text
    textPrimary: '#1e293b',
    textSecondary: '#64748b',
    textMuted: '#94a3b8',
    textInverse: '#ffffff',
  },
  
  // Spacing - 8px base system
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '48px',
    xxxl: '64px',
  },
  
  // Border Radius
  radius: {
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    full: '9999px',
  },
  
  // Shadows - Soft neumorphism
  shadows: {
    sm: '0 2px 8px rgba(0, 0, 0, 0.04)',
    md: '0 4px 16px rgba(0, 0, 0, 0.06)',
    lg: '0 8px 32px rgba(0, 0, 0, 0.08)',
    neumorphism: '8px 8px 16px rgba(0, 0, 0, 0.06), -8px -8px 16px rgba(255, 255, 255, 0.8)',
    neumorphismInset: 'inset 4px 4px 8px rgba(0, 0, 0, 0.04), inset -4px -4px 8px rgba(255, 255, 255, 0.9)',
  },
  
  // Typography
  typography: {
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontSizes: {
      xs: '12px',
      sm: '14px',
      md: '16px',
      lg: '18px',
      xl: '20px',
      xxl: '24px',
      xxxl: '32px',
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
  
  // Transitions
  transitions: {
    fast: '150ms ease',
    normal: '250ms ease',
    slow: '350ms ease',
  },
  
  // Glass effect
  glass: {
    background: 'rgba(255, 255, 255, 0.7)',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.3)',
  },
  
  // Grid
  grid: {
    columns: 12,
    gap: '24px',
    containerMaxWidth: '1440px',
  },
} as const

export type DesignTokens = typeof designTokens

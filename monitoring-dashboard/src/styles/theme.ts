/**
 * Design system tokens for CasareRPA Monitoring Dashboard.
 * Dark theme with accent colors blending modern dashboard aesthetics.
 */

export const theme = {
  colors: {
    // Base backgrounds
    background: {
      primary: '#0f0f12',    // Main background
      secondary: '#1a1a1f',  // Card background
      tertiary: '#252530',   // Elevated surfaces
      hover: '#2a2a35',      // Hover states
    },

    // Borders
    border: {
      default: '#2a2a35',
      subtle: '#1f1f28',
      focus: '#6366f1',
    },

    // Text
    text: {
      primary: '#ffffff',
      secondary: '#9ca3af',
      muted: '#6b7280',
      inverse: '#0f0f12',
    },

    // Accent colors
    accent: {
      primary: '#6366f1',    // Indigo - primary actions
      orange: '#f97316',     // Orange - highlights, active states
      blue: '#3b82f6',       // Blue - info, idle status
      green: '#22c55e',      // Green - success, completed
      yellow: '#eab308',     // Yellow - warning, busy
      red: '#ef4444',        // Red - error, failed
      cyan: '#06b6d4',       // Cyan - analytics accents
      purple: '#a855f7',     // Purple - special states
    },

    // Status-specific colors (mapped to robot/job statuses)
    status: {
      idle: '#3b82f6',
      busy: '#eab308',
      offline: '#6b7280',
      failed: '#ef4444',
      pending: '#9ca3af',
      completed: '#22c55e',
      running: '#f97316',
      claimed: '#a855f7',
    },
  },

  spacing: {
    xs: '0.25rem',   // 4px
    sm: '0.5rem',    // 8px
    md: '1rem',      // 16px
    lg: '1.5rem',    // 24px
    xl: '2rem',      // 32px
    '2xl': '3rem',   // 48px
  },

  borderRadius: {
    sm: '4px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    full: '9999px',
  },

  shadows: {
    card: '0 4px 6px -1px rgba(0, 0, 0, 0.3)',
    elevated: '0 10px 15px -3px rgba(0, 0, 0, 0.4)',
    glow: {
      primary: '0 0 20px rgba(99, 102, 241, 0.3)',
      green: '0 0 20px rgba(34, 197, 94, 0.3)',
      orange: '0 0 20px rgba(249, 115, 22, 0.3)',
      red: '0 0 20px rgba(239, 68, 68, 0.3)',
    },
  },

  typography: {
    fontFamily: {
      sans: 'Inter, system-ui, -apple-system, sans-serif',
      mono: 'JetBrains Mono, Menlo, Monaco, monospace',
    },
    fontSize: {
      xs: '0.75rem',    // 12px
      sm: '0.875rem',   // 14px
      base: '1rem',     // 16px
      lg: '1.125rem',   // 18px
      xl: '1.25rem',    // 20px
      '2xl': '1.5rem',  // 24px
      '3xl': '2rem',    // 32px
      '4xl': '2.5rem',  // 40px
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
  },

  transitions: {
    fast: '150ms ease',
    normal: '200ms ease',
    slow: '300ms ease',
  },

  breakpoints: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },

  zIndex: {
    dropdown: 1000,
    sticky: 1020,
    modal: 1050,
    tooltip: 1070,
  },
} as const;

// Type exports for use in components
export type ThemeColors = typeof theme.colors;
export type StatusColor = keyof typeof theme.colors.status;
export type AccentColor = keyof typeof theme.colors.accent;

// Helper to get status color
export function getStatusColor(status: string): string {
  const statusColors = theme.colors.status as Record<string, string>;
  return statusColors[status.toLowerCase()] || theme.colors.text.muted;
}

// Helper to get status background (with opacity)
export function getStatusBackground(status: string, opacity = 0.2): string {
  const color = getStatusColor(status);
  // Convert hex to rgba
  const hex = color.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${opacity})`;
}

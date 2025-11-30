import { useMemo } from 'react';
import type { CSSProperties, ReactNode } from 'react';
import { motion, useSpring, useTransform } from 'framer-motion';
import { AreaChart, Area, ResponsiveContainer } from 'recharts';

export interface KPICardProps {
  title: string;
  value: number;
  previousValue?: number;
  format?: 'number' | 'percentage' | 'duration';
  icon?: ReactNode;
  accentColor?: string;
  isLive?: boolean;
  trend?: 'up' | 'down' | 'stable';
  sparklineData?: number[];
  suffix?: string;
  className?: string;
}

// Animated number component
function AnimatedNumber({ value, format, suffix }: { value: number; format: string; suffix?: string }) {
  const spring = useSpring(value, { stiffness: 100, damping: 30 });
  const display = useTransform(spring, (current) => {
    if (format === 'percentage') {
      return `${current.toFixed(1)}%`;
    }
    if (format === 'duration') {
      if (current < 60) return `${current.toFixed(1)}s`;
      return `${(current / 60).toFixed(1)}m`;
    }
    if (current >= 1000) {
      return `${(current / 1000).toFixed(1)}k`;
    }
    return Math.round(current).toLocaleString();
  });

  return (
    <>
      <motion.span>{display}</motion.span>
      {suffix && <span style={{ fontSize: '0.5em', marginLeft: '0.25em' }}>{suffix}</span>}
    </>
  );
}

// Trend indicator
function TrendIndicator({ trend, value }: { trend?: 'up' | 'down' | 'stable'; value?: number }) {
  if (!trend || trend === 'stable') return null;

  const isUp = trend === 'up';
  const color = isUp ? 'var(--accent-green)' : 'var(--accent-red)';
  const arrow = isUp ? '↑' : '↓';
  const change = value ? `${Math.abs(value).toFixed(1)}%` : '';

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.25rem',
        fontSize: '0.75rem',
        fontWeight: 500,
        color,
      }}
    >
      {arrow} {change}
    </span>
  );
}

// Live indicator (pulsing dot)
function LiveIndicator() {
  return (
    <motion.span
      style={{
        display: 'inline-block',
        width: 8,
        height: 8,
        borderRadius: '50%',
        backgroundColor: 'var(--accent-green)',
        marginLeft: 'var(--spacing-sm)',
      }}
      animate={{ opacity: [1, 0.4, 1] }}
      transition={{ duration: 1.5, repeat: Infinity }}
    />
  );
}

// Mini sparkline chart
function Sparkline({ data, color }: { data: number[]; color: string }) {
  const chartData = useMemo(() => data.map((value, index) => ({ value, index })), [data]);

  return (
    <div style={{ width: '100%', height: 40, marginTop: 'var(--spacing-sm)' }}>
      <ResponsiveContainer>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id={`gradient-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.3} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            fill={`url(#gradient-${color.replace('#', '')})`}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function KPICard({
  title,
  value,
  previousValue,
  format = 'number',
  icon,
  accentColor = 'var(--accent-primary)',
  isLive = false,
  trend,
  sparklineData,
  suffix,
  className = '',
}: KPICardProps) {
  const cardStyles: CSSProperties = {
    backgroundColor: 'var(--bg-secondary)',
    border: '1px solid var(--border-subtle)',
    borderRadius: 'var(--radius-lg)',
    padding: 'var(--spacing-lg)',
    position: 'relative',
    overflow: 'hidden',
  };

  const accentBarStyles: CSSProperties = {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 3,
    backgroundColor: accentColor,
  };

  const headerStyles: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 'var(--spacing-sm)',
  };

  const titleStyles: CSSProperties = {
    fontSize: '0.75rem',
    fontWeight: 500,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    color: 'var(--text-muted)',
    display: 'flex',
    alignItems: 'center',
  };

  const valueStyles: CSSProperties = {
    fontSize: '2.5rem',
    fontWeight: 700,
    color: 'var(--text-primary)',
    lineHeight: 1,
  };

  const footerStyles: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 'var(--spacing-sm)',
  };

  // Calculate trend from previous value if not provided
  const calculatedTrend = useMemo(() => {
    if (trend) return trend;
    if (previousValue === undefined) return undefined;
    if (value > previousValue) return 'up';
    if (value < previousValue) return 'down';
    return 'stable';
  }, [trend, value, previousValue]);

  const trendValue = previousValue !== undefined ? ((value - previousValue) / previousValue) * 100 : undefined;

  return (
    <motion.div
      className={className}
      style={cardStyles}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={{ borderColor: accentColor }}
    >
      {/* Accent bar */}
      <div style={accentBarStyles} />

      {/* Header */}
      <div style={headerStyles}>
        <span style={titleStyles}>
          {title}
          {isLive && <LiveIndicator />}
        </span>
        {icon && (
          <span style={{ color: accentColor, opacity: 0.7 }}>{icon}</span>
        )}
      </div>

      {/* Value */}
      <div style={valueStyles}>
        <AnimatedNumber value={value} format={format} suffix={suffix} />
      </div>

      {/* Footer with trend */}
      <div style={footerStyles}>
        <TrendIndicator trend={calculatedTrend} value={trendValue} />
      </div>

      {/* Sparkline */}
      {sparklineData && sparklineData.length > 0 && (
        <Sparkline data={sparklineData} color={accentColor} />
      )}
    </motion.div>
  );
}

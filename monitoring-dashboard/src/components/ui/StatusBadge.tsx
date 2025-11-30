import type { CSSProperties } from 'react';
import { motion } from 'framer-motion';

export type Status = 'idle' | 'busy' | 'offline' | 'failed' | 'pending' | 'completed' | 'running' | 'claimed';

interface StatusBadgeProps {
  status: Status | string;
  size?: 'sm' | 'md' | 'lg';
  showDot?: boolean;
  pulseDot?: boolean;
  className?: string;
}

const statusConfig: Record<string, { color: string; bg: string; label: string }> = {
  idle: { color: 'var(--status-idle)', bg: 'rgba(59, 130, 246, 0.15)', label: 'Idle' },
  busy: { color: 'var(--status-busy)', bg: 'rgba(234, 179, 8, 0.15)', label: 'Busy' },
  offline: { color: 'var(--status-offline)', bg: 'rgba(107, 114, 128, 0.15)', label: 'Offline' },
  failed: { color: 'var(--status-failed)', bg: 'rgba(239, 68, 68, 0.15)', label: 'Failed' },
  pending: { color: 'var(--status-pending)', bg: 'rgba(156, 163, 175, 0.15)', label: 'Pending' },
  completed: { color: 'var(--status-completed)', bg: 'rgba(34, 197, 94, 0.15)', label: 'Completed' },
  running: { color: 'var(--status-running)', bg: 'rgba(249, 115, 22, 0.15)', label: 'Running' },
  claimed: { color: 'var(--accent-purple)', bg: 'rgba(168, 85, 247, 0.15)', label: 'Claimed' },
};

const sizeConfig = {
  sm: { padding: '0.125rem 0.5rem', fontSize: '0.625rem', dotSize: 6 },
  md: { padding: '0.25rem 0.75rem', fontSize: '0.75rem', dotSize: 8 },
  lg: { padding: '0.375rem 1rem', fontSize: '0.875rem', dotSize: 10 },
};

export function StatusBadge({
  status,
  size = 'md',
  showDot = true,
  pulseDot = false,
  className = '',
}: StatusBadgeProps) {
  const normalizedStatus = status.toLowerCase();
  const config = statusConfig[normalizedStatus] || statusConfig.pending;
  const sizeStyles = sizeConfig[size];

  const badgeStyles: CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.375rem',
    padding: sizeStyles.padding,
    borderRadius: 'var(--radius-full)',
    backgroundColor: config.bg,
    color: config.color,
    fontSize: sizeStyles.fontSize,
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    whiteSpace: 'nowrap',
  };

  const dotStyles: CSSProperties = {
    width: sizeStyles.dotSize,
    height: sizeStyles.dotSize,
    borderRadius: '50%',
    backgroundColor: config.color,
    flexShrink: 0,
  };

  // Determine if dot should pulse (busy or running statuses)
  const shouldPulse = pulseDot || normalizedStatus === 'busy' || normalizedStatus === 'running';

  return (
    <span className={className} style={badgeStyles}>
      {showDot && (
        shouldPulse ? (
          <motion.span
            style={dotStyles}
            animate={{ opacity: [1, 0.4, 1] }}
            transition={{ duration: 1, repeat: Infinity }}
          />
        ) : (
          <span style={dotStyles} />
        )
      )}
      {config.label}
    </span>
  );
}

// Status dot only (no text)
interface StatusDotProps {
  status: Status | string;
  size?: number;
  pulse?: boolean;
  className?: string;
}

export function StatusDot({ status, size = 10, pulse = false, className = '' }: StatusDotProps) {
  const normalizedStatus = status.toLowerCase();
  const config = statusConfig[normalizedStatus] || statusConfig.pending;
  const shouldPulse = pulse || normalizedStatus === 'busy' || normalizedStatus === 'running';

  const dotStyles: CSSProperties = {
    width: size,
    height: size,
    borderRadius: '50%',
    backgroundColor: config.color,
    boxShadow: `0 0 ${size}px ${config.color}40`,
  };

  if (shouldPulse) {
    return (
      <motion.span
        className={className}
        style={dotStyles}
        animate={{ opacity: [1, 0.4, 1], scale: [1, 1.1, 1] }}
        transition={{ duration: 1.5, repeat: Infinity }}
      />
    );
  }

  return <span className={className} style={dotStyles} />;
}

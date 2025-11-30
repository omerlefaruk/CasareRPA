import { useMemo } from 'react';
import type { CSSProperties } from 'react';
import { motion } from 'framer-motion';

type RobotStatus = 'idle' | 'busy' | 'offline' | 'failed';

interface RobotStatusIndicatorProps {
  status: RobotStatus;
  size?: 'sm' | 'md' | 'lg';
  showGlow?: boolean;
  className?: string;
}

interface StatusConfig {
  color: string;
  glowColor: string;
  label: string;
  shouldPulse: boolean;
}

const STATUS_CONFIG: Record<RobotStatus, StatusConfig> = {
  idle: {
    color: 'var(--status-idle)',
    glowColor: 'rgba(59, 130, 246, 0.5)',
    label: 'Idle',
    shouldPulse: false,
  },
  busy: {
    color: 'var(--status-busy)',
    glowColor: 'rgba(234, 179, 8, 0.5)',
    label: 'Busy',
    shouldPulse: true,
  },
  offline: {
    color: 'var(--status-offline)',
    glowColor: 'rgba(107, 114, 128, 0.3)',
    label: 'Offline',
    shouldPulse: false,
  },
  failed: {
    color: 'var(--status-failed)',
    glowColor: 'rgba(239, 68, 68, 0.5)',
    label: 'Failed',
    shouldPulse: false,
  },
};

const SIZE_CONFIG = {
  sm: { dotSize: 8, glowSpread: 4 },
  md: { dotSize: 10, glowSpread: 6 },
  lg: { dotSize: 14, glowSpread: 8 },
};

export function RobotStatusIndicator({
  status,
  size = 'md',
  showGlow = true,
  className = '',
}: RobotStatusIndicatorProps) {
  const config = STATUS_CONFIG[status];
  const sizeConfig = SIZE_CONFIG[size];

  const dotStyles = useMemo((): CSSProperties => ({
    width: sizeConfig.dotSize,
    height: sizeConfig.dotSize,
    borderRadius: '50%',
    backgroundColor: config.color,
    boxShadow: showGlow
      ? `0 0 ${sizeConfig.glowSpread}px ${config.glowColor}, 0 0 ${sizeConfig.glowSpread * 2}px ${config.glowColor}`
      : undefined,
    flexShrink: 0,
  }), [config.color, config.glowColor, sizeConfig.dotSize, sizeConfig.glowSpread, showGlow]);

  if (config.shouldPulse) {
    return (
      <motion.span
        className={className}
        style={dotStyles}
        animate={{
          opacity: [1, 0.5, 1],
          scale: [1, 1.15, 1],
          boxShadow: showGlow ? [
            `0 0 ${sizeConfig.glowSpread}px ${config.glowColor}, 0 0 ${sizeConfig.glowSpread * 2}px ${config.glowColor}`,
            `0 0 ${sizeConfig.glowSpread * 2}px ${config.glowColor}, 0 0 ${sizeConfig.glowSpread * 3}px ${config.glowColor}`,
            `0 0 ${sizeConfig.glowSpread}px ${config.glowColor}, 0 0 ${sizeConfig.glowSpread * 2}px ${config.glowColor}`,
          ] : undefined,
        }}
        transition={{
          duration: 1.5,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
        aria-label={`Status: ${config.label}`}
        role="status"
      />
    );
  }

  return (
    <span
      className={className}
      style={dotStyles}
      aria-label={`Status: ${config.label}`}
      role="status"
    />
  );
}

export { STATUS_CONFIG };
export type { RobotStatus, RobotStatusIndicatorProps };

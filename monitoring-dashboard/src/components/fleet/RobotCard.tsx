import { useMemo, useCallback } from 'react';
import type { CSSProperties } from 'react';
import { motion } from 'framer-motion';
import { formatDistanceToNow } from 'date-fns';
import { RobotStatusIndicator } from './RobotStatusIndicator';
import type { RobotStatus } from './RobotStatusIndicator';

export interface RobotSummary {
  robot_id: string;
  hostname: string;
  status: RobotStatus;
  current_job_id: string | null;
  cpu_percent: number;
  memory_mb: number;
  last_heartbeat: string;
}

interface RobotCardProps {
  robot: RobotSummary;
  onClick?: (robot: RobotSummary) => void;
  isSelected?: boolean;
}

interface ProgressBarProps {
  value: number;
  max: number;
  label: string;
  color: string;
  unit?: string;
}

function ProgressBar({ value, max, label, color, unit = '%' }: ProgressBarProps) {
  const percentage = Math.min((value / max) * 100, 100);
  const displayValue = unit === '%' ? value.toFixed(0) : value.toFixed(0);

  const containerStyles: CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    gap: 'var(--spacing-xs)',
    width: '100%',
  };

  const labelRowStyles: CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    fontSize: '0.75rem',
  };

  const trackStyles: CSSProperties = {
    height: 4,
    backgroundColor: 'var(--bg-tertiary)',
    borderRadius: 'var(--radius-full)',
    overflow: 'hidden',
  };

  const fillStyles: CSSProperties = {
    height: '100%',
    width: `${percentage}%`,
    backgroundColor: color,
    borderRadius: 'var(--radius-full)',
    transition: 'width var(--transition-normal)',
  };

  return (
    <div style={containerStyles}>
      <div style={labelRowStyles}>
        <span style={{ color: 'var(--text-muted)' }}>{label}</span>
        <span style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
          {displayValue}{unit}
        </span>
      </div>
      <div style={trackStyles}>
        <div style={fillStyles} />
      </div>
    </div>
  );
}

export function RobotCard({ robot, onClick, isSelected = false }: RobotCardProps) {
  const lastSeenText = useMemo(() => {
    try {
      const date = new Date(robot.last_heartbeat);
      if (isNaN(date.getTime())) {
        return 'Unknown';
      }
      return formatDistanceToNow(date, { addSuffix: true });
    } catch {
      return 'Unknown';
    }
  }, [robot.last_heartbeat]);

  const truncatedId = useMemo(() => {
    return robot.robot_id.length > 8
      ? `${robot.robot_id.slice(0, 8)}...`
      : robot.robot_id;
  }, [robot.robot_id]);

  const handleClick = useCallback(() => {
    if (onClick) {
      onClick(robot);
    }
  }, [onClick, robot]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleClick();
    }
  }, [handleClick]);

  const cpuColor = robot.cpu_percent > 80
    ? 'var(--status-failed)'
    : robot.cpu_percent > 60
      ? 'var(--status-busy)'
      : 'var(--accent-green)';

  const memoryColor = robot.memory_mb > 8000
    ? 'var(--status-failed)'
    : robot.memory_mb > 4000
      ? 'var(--status-busy)'
      : 'var(--accent-blue)';

  const cardStyles: CSSProperties = {
    backgroundColor: 'var(--bg-secondary)',
    border: `1px solid ${isSelected ? 'var(--accent-primary)' : 'var(--border-default)'}`,
    borderRadius: 'var(--radius-lg)',
    padding: 'var(--spacing-md)',
    cursor: onClick ? 'pointer' : 'default',
    transition: 'all var(--transition-normal)',
    display: 'flex',
    flexDirection: 'column',
    gap: 'var(--spacing-md)',
    height: '100%',
    minHeight: 200,
  };

  const headerStyles: CSSProperties = {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 'var(--spacing-sm)',
  };

  const hostInfoStyles: CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    gap: 'var(--spacing-xs)',
    flex: 1,
    minWidth: 0,
  };

  const hostnameStyles: CSSProperties = {
    fontSize: '1rem',
    fontWeight: 600,
    color: 'var(--text-primary)',
    margin: 0,
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  };

  const robotIdStyles: CSSProperties = {
    fontSize: '0.75rem',
    color: 'var(--text-muted)',
    fontFamily: 'var(--font-mono)',
  };

  const metricsContainerStyles: CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    gap: 'var(--spacing-sm)',
    flex: 1,
  };

  const footerStyles: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 'var(--spacing-sm)',
    borderTop: '1px solid var(--border-subtle)',
    marginTop: 'auto',
  };

  const jobBadgeStyles: CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '0.125rem 0.5rem',
    borderRadius: 'var(--radius-full)',
    fontSize: '0.625rem',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    backgroundColor: robot.current_job_id
      ? 'rgba(249, 115, 22, 0.15)'
      : 'rgba(107, 114, 128, 0.15)',
    color: robot.current_job_id
      ? 'var(--status-running)'
      : 'var(--text-muted)',
  };

  const lastSeenStyles: CSSProperties = {
    fontSize: '0.75rem',
    color: 'var(--text-muted)',
  };

  return (
    <motion.div
      style={cardStyles}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      tabIndex={onClick ? 0 : undefined}
      role={onClick ? 'button' : undefined}
      aria-label={`Robot ${robot.hostname}, status ${robot.status}`}
      aria-pressed={isSelected}
      whileHover={onClick ? {
        backgroundColor: 'var(--bg-hover)',
        borderColor: 'var(--border-focus)',
        scale: 1.02,
        y: -2,
      } : undefined}
      whileTap={onClick ? { scale: 0.98 } : undefined}
      transition={{ duration: 0.15 }}
      layout
    >
      <div style={headerStyles}>
        <div style={hostInfoStyles}>
          <h4 style={hostnameStyles} title={robot.hostname}>
            {robot.hostname}
          </h4>
          <span style={robotIdStyles} title={robot.robot_id}>
            {truncatedId}
          </span>
        </div>
        <RobotStatusIndicator status={robot.status} size="md" showGlow />
      </div>

      <div style={metricsContainerStyles}>
        <ProgressBar
          value={robot.cpu_percent}
          max={100}
          label="CPU"
          color={cpuColor}
        />
        <ProgressBar
          value={robot.memory_mb}
          max={16000}
          label="Memory"
          color={memoryColor}
          unit=" MB"
        />
      </div>

      <div style={footerStyles}>
        <span style={jobBadgeStyles}>
          {robot.current_job_id
            ? `Job: ${robot.current_job_id.slice(0, 6)}`
            : 'Idle'}
        </span>
        <span style={lastSeenStyles}>
          {lastSeenText}
        </span>
      </div>
    </motion.div>
  );
}

export type { RobotCardProps };

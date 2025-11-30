import { useMemo } from 'react';
import type { CSSProperties } from 'react';
import { motion } from 'framer-motion';
import { formatDistanceToNow } from 'date-fns';

/**
 * Event types supported by the activity feed.
 */
export type ActivityEventType =
  | 'job_started'
  | 'job_completed'
  | 'job_failed'
  | 'robot_online'
  | 'robot_offline'
  | 'schedule_triggered';

/**
 * Activity event data structure.
 */
export interface ActivityEvent {
  id: string;
  type: ActivityEventType;
  timestamp: string;
  title: string;
  details?: string;
  robotId?: string;
  jobId?: string;
}

interface ActivityItemProps {
  event: ActivityEvent;
  onClick?: (event: ActivityEvent) => void;
}

/**
 * Icon configuration for each event type.
 * Returns SVG path data and color CSS variable.
 */
const eventIconConfig: Record<
  ActivityEventType,
  { path: string; color: string; bgColor: string }
> = {
  job_started: {
    // Play icon
    path: 'M8 5v14l11-7z',
    color: 'var(--accent-orange)',
    bgColor: 'rgba(249, 115, 22, 0.15)',
  },
  job_completed: {
    // Check icon
    path: 'M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z',
    color: 'var(--accent-green)',
    bgColor: 'rgba(34, 197, 94, 0.15)',
  },
  job_failed: {
    // X icon
    path: 'M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z',
    color: 'var(--accent-red)',
    bgColor: 'rgba(239, 68, 68, 0.15)',
  },
  robot_online: {
    // Server icon
    path: 'M20 13H4c-.55 0-1 .45-1 1v6c0 .55.45 1 1 1h16c.55 0 1-.45 1-1v-6c0-.55-.45-1-1-1zM7 19c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zM20 3H4c-.55 0-1 .45-1 1v6c0 .55.45 1 1 1h16c.55 0 1-.45 1-1V4c0-.55-.45-1-1-1zM7 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z',
    color: 'var(--accent-blue)',
    bgColor: 'rgba(59, 130, 246, 0.15)',
  },
  robot_offline: {
    // Server icon (gray)
    path: 'M20 13H4c-.55 0-1 .45-1 1v6c0 .55.45 1 1 1h16c.55 0 1-.45 1-1v-6c0-.55-.45-1-1-1zM7 19c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zM20 3H4c-.55 0-1 .45-1 1v6c0 .55.45 1 1 1h16c.55 0 1-.45 1-1V4c0-.55-.45-1-1-1zM7 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z',
    color: 'var(--text-muted)',
    bgColor: 'rgba(107, 114, 128, 0.15)',
  },
  schedule_triggered: {
    // Clock icon
    path: 'M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z',
    color: 'var(--accent-purple)',
    bgColor: 'rgba(168, 85, 247, 0.15)',
  },
};

/**
 * Formats the timestamp as a relative time string.
 */
function formatRelativeTime(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return formatDistanceToNow(date, { addSuffix: true });
  } catch {
    return 'Unknown time';
  }
}

/**
 * Individual activity feed item with icon, title, details, and timestamp.
 * Animates on mount with a fade-in effect.
 */
export function ActivityItem({ event, onClick }: ActivityItemProps) {
  const iconConfig = eventIconConfig[event.type];
  const relativeTime = useMemo(
    () => formatRelativeTime(event.timestamp),
    [event.timestamp]
  );

  const handleClick = () => {
    if (onClick) {
      onClick(event);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  };

  const containerStyles: CSSProperties = {
    display: 'flex',
    alignItems: 'flex-start',
    gap: 'var(--spacing-sm)',
    padding: 'var(--spacing-sm)',
    borderRadius: 'var(--radius-md)',
    cursor: onClick ? 'pointer' : 'default',
    transition: 'background-color var(--transition-fast)',
  };

  const iconContainerStyles: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: 32,
    height: 32,
    borderRadius: 'var(--radius-md)',
    backgroundColor: iconConfig.bgColor,
    flexShrink: 0,
  };

  const iconStyles: CSSProperties = {
    width: 16,
    height: 16,
    fill: iconConfig.color,
  };

  const contentStyles: CSSProperties = {
    flex: 1,
    minWidth: 0,
  };

  const titleStyles: CSSProperties = {
    margin: 0,
    fontSize: '0.875rem',
    fontWeight: 500,
    color: 'var(--text-primary)',
    lineHeight: 1.4,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  };

  const detailsStyles: CSSProperties = {
    margin: 0,
    marginTop: '0.125rem',
    fontSize: '0.75rem',
    color: 'var(--text-muted)',
    lineHeight: 1.4,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  };

  const timestampStyles: CSSProperties = {
    fontSize: '0.625rem',
    color: 'var(--text-muted)',
    whiteSpace: 'nowrap',
    flexShrink: 0,
    marginTop: '0.125rem',
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
      style={containerStyles}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      whileHover={onClick ? { backgroundColor: 'var(--bg-hover)' } : undefined}
    >
      <div style={iconContainerStyles}>
        <svg viewBox="0 0 24 24" style={iconStyles} aria-hidden="true">
          <path d={iconConfig.path} />
        </svg>
      </div>
      <div style={contentStyles}>
        <p style={titleStyles} title={event.title}>
          {event.title}
        </p>
        {event.details && (
          <p style={detailsStyles} title={event.details}>
            {event.details}
          </p>
        )}
      </div>
      <span style={timestampStyles}>{relativeTime}</span>
    </motion.div>
  );
}

import { useRef, useEffect, useMemo } from 'react';
import type { CSSProperties } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  isToday,
  isYesterday,
  differenceInMinutes,
  format,
} from 'date-fns';
import { ActivityItem } from './ActivityItem';
import type { ActivityEvent } from './ActivityItem';

interface ActivityFeedProps {
  events: ActivityEvent[];
  onEventClick?: (event: ActivityEvent) => void;
  maxVisible?: number;
}

/**
 * Time group labels for activity events.
 */
type TimeGroup =
  | 'Just now'
  | '5 min ago'
  | '15 min ago'
  | '30 min ago'
  | '1 hour ago'
  | 'Earlier today'
  | 'Yesterday'
  | 'Older';

/**
 * Determines the time group for a given timestamp.
 */
function getTimeGroup(timestamp: string): TimeGroup {
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const minutesAgo = differenceInMinutes(now, date);

    if (minutesAgo < 2) {
      return 'Just now';
    }
    if (minutesAgo < 10) {
      return '5 min ago';
    }
    if (minutesAgo < 20) {
      return '15 min ago';
    }
    if (minutesAgo < 45) {
      return '30 min ago';
    }
    if (minutesAgo < 90) {
      return '1 hour ago';
    }
    if (isToday(date)) {
      return 'Earlier today';
    }
    if (isYesterday(date)) {
      return 'Yesterday';
    }
    return 'Older';
  } catch {
    return 'Older';
  }
}

/**
 * Groups events by their time category.
 */
function groupEventsByTime(
  events: ActivityEvent[]
): Map<TimeGroup, ActivityEvent[]> {
  const groups = new Map<TimeGroup, ActivityEvent[]>();

  // Define group order
  const groupOrder: TimeGroup[] = [
    'Just now',
    '5 min ago',
    '15 min ago',
    '30 min ago',
    '1 hour ago',
    'Earlier today',
    'Yesterday',
    'Older',
  ];

  // Initialize groups in order
  for (const group of groupOrder) {
    groups.set(group, []);
  }

  // Sort events by timestamp (newest first)
  const sortedEvents = [...events].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  // Group events
  for (const event of sortedEvents) {
    const group = getTimeGroup(event.timestamp);
    const groupEvents = groups.get(group);
    if (groupEvents) {
      groupEvents.push(event);
    }
  }

  // Remove empty groups
  for (const [key, value] of groups) {
    if (value.length === 0) {
      groups.delete(key);
    }
  }

  return groups;
}

/**
 * Formats a time group for display with optional date.
 */
function formatGroupHeader(group: TimeGroup): string {
  if (group === 'Yesterday') {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    return `Yesterday, ${format(yesterday, 'MMM d')}`;
  }
  return group;
}

/**
 * Real-time activity feed component.
 * Groups events by time and supports auto-scroll to top on new events.
 */
export function ActivityFeed({
  events,
  onEventClick,
  maxVisible = 20,
}: ActivityFeedProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const prevEventCountRef = useRef(events.length);

  // Group events by time
  const groupedEvents = useMemo(() => {
    const limitedEvents = events.slice(0, maxVisible);
    return groupEventsByTime(limitedEvents);
  }, [events, maxVisible]);

  // Auto-scroll to top when new events arrive
  useEffect(() => {
    if (events.length > prevEventCountRef.current && containerRef.current) {
      containerRef.current.scrollTo({
        top: 0,
        behavior: 'smooth',
      });
    }
    prevEventCountRef.current = events.length;
  }, [events.length]);

  const containerStyles: CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    overflow: 'hidden',
  };

  const scrollContainerStyles: CSSProperties = {
    flex: 1,
    overflowY: 'auto',
    overflowX: 'hidden',
    paddingRight: 'var(--spacing-xs)',
  };

  const groupStyles: CSSProperties = {
    marginBottom: 'var(--spacing-md)',
  };

  const groupHeaderStyles: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: 'var(--spacing-sm)',
    marginBottom: 'var(--spacing-xs)',
    paddingLeft: 'var(--spacing-sm)',
  };

  const groupLabelStyles: CSSProperties = {
    fontSize: '0.625rem',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    color: 'var(--text-muted)',
    whiteSpace: 'nowrap',
  };

  const groupLineStyles: CSSProperties = {
    flex: 1,
    height: 1,
    backgroundColor: 'var(--border-subtle)',
  };

  const emptyStateStyles: CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 'var(--spacing-xl)',
    color: 'var(--text-muted)',
    textAlign: 'center',
  };

  const emptyIconStyles: CSSProperties = {
    width: 48,
    height: 48,
    fill: 'var(--text-muted)',
    opacity: 0.5,
    marginBottom: 'var(--spacing-md)',
  };

  if (events.length === 0) {
    return (
      <div style={containerStyles}>
        <div style={emptyStateStyles}>
          <svg viewBox="0 0 24 24" style={emptyIconStyles} aria-hidden="true">
            <path d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z" />
          </svg>
          <p style={{ margin: 0, fontSize: '0.875rem' }}>No recent activity</p>
          <p style={{ margin: '0.25rem 0 0', fontSize: '0.75rem' }}>
            Events will appear here as they occur
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={containerStyles}>
      <div ref={containerRef} style={scrollContainerStyles}>
        <AnimatePresence mode="popLayout">
          {Array.from(groupedEvents.entries()).map(([group, groupEvents]) => (
            <motion.div
              key={group}
              style={groupStyles}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
            >
              <div style={groupHeaderStyles}>
                <span style={groupLabelStyles}>{formatGroupHeader(group)}</span>
                <div style={groupLineStyles} />
              </div>
              <div>
                {groupEvents.map((event) => (
                  <ActivityItem
                    key={event.id}
                    event={event}
                    onClick={onEventClick}
                  />
                ))}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}

// Re-export types for convenience
export type { ActivityEvent, ActivityEventType } from './ActivityItem';

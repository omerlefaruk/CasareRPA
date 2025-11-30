/**
 * UpcomingRuns - Displays the next scheduled workflow runs.
 *
 * Features:
 * - Shows next 5 scheduled runs
 * - Workflow name, schedule name, relative time until run
 * - Color-coded by priority
 * - Click to view schedule details
 */

import { useMemo } from 'react';
import type { CSSProperties } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { formatDistanceToNow, parseISO, isPast, differenceInMinutes } from 'date-fns';
import { Card, CardHeader } from '@/components/ui/Card';
import type { Schedule } from '@/hooks/useSchedules';

interface UpcomingRunsProps {
  schedules: Schedule[];
  onScheduleClick?: (schedule: Schedule) => void;
  limit?: number;
  className?: string;
}

const listStyles: CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: 'var(--spacing-sm)',
};

const itemStyles: CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  padding: 'var(--spacing-sm) var(--spacing-md)',
  borderRadius: 'var(--radius-md)',
  backgroundColor: 'var(--bg-tertiary)',
  border: '1px solid var(--border-subtle)',
  cursor: 'pointer',
  transition: 'all var(--transition-fast)',
};

const priorityIndicatorStyles: CSSProperties = {
  width: 4,
  height: 32,
  borderRadius: 2,
  marginRight: 'var(--spacing-md)',
  flexShrink: 0,
};

const contentStyles: CSSProperties = {
  flex: 1,
  minWidth: 0,
  overflow: 'hidden',
};

const workflowNameStyles: CSSProperties = {
  fontSize: '0.875rem',
  fontWeight: 600,
  color: 'var(--text-primary)',
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
};

const scheduleNameStyles: CSSProperties = {
  fontSize: '0.75rem',
  color: 'var(--text-muted)',
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  marginTop: 2,
};

const timeStyles: CSSProperties = {
  fontSize: '0.875rem',
  fontWeight: 500,
  textAlign: 'right',
  flexShrink: 0,
  marginLeft: 'var(--spacing-md)',
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

function getPriorityColor(priority: number): string {
  if (priority >= 8) return 'var(--accent-red)';
  if (priority >= 6) return 'var(--accent-orange)';
  if (priority >= 4) return 'var(--accent-yellow)';
  if (priority >= 2) return 'var(--accent-blue)';
  return 'var(--text-muted)';
}

function getTimeColor(nextRun: string): string {
  const runDate = parseISO(nextRun);
  const minutesUntil = differenceInMinutes(runDate, new Date());

  if (isPast(runDate)) return 'var(--accent-red)';
  if (minutesUntil <= 5) return 'var(--accent-orange)';
  if (minutesUntil <= 30) return 'var(--accent-yellow)';
  if (minutesUntil <= 60) return 'var(--accent-green)';
  return 'var(--text-secondary)';
}

function formatRelativeTime(nextRun: string): string {
  const runDate = parseISO(nextRun);

  if (isPast(runDate)) {
    return 'Overdue';
  }

  const minutesUntil = differenceInMinutes(runDate, new Date());

  if (minutesUntil < 1) return 'Now';
  if (minutesUntil === 1) return 'in 1 min';
  if (minutesUntil < 60) return `in ${minutesUntil} min`;

  return formatDistanceToNow(runDate, { addSuffix: true });
}

export function UpcomingRuns({
  schedules,
  onScheduleClick,
  limit = 5,
  className = '',
}: UpcomingRunsProps) {
  const upcomingRuns = useMemo(() => {
    return schedules
      .filter((s) => s.enabled && s.next_run)
      .sort((a, b) => {
        if (!a.next_run || !b.next_run) return 0;
        return new Date(a.next_run).getTime() - new Date(b.next_run).getTime();
      })
      .slice(0, limit);
  }, [schedules, limit]);

  const handleItemClick = (schedule: Schedule) => {
    onScheduleClick?.(schedule);
  };

  const handleKeyDown = (e: React.KeyboardEvent, schedule: Schedule) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onScheduleClick?.(schedule);
    }
  };

  return (
    <Card className={className} padding="md" variant="default">
      <CardHeader
        title="Upcoming Runs"
        subtitle={upcomingRuns.length > 0 ? `Next ${upcomingRuns.length} scheduled` : undefined}
      />

      {upcomingRuns.length === 0 ? (
        <div style={emptyStateStyles}>
          <svg
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            style={{ marginBottom: 'var(--spacing-md)', opacity: 0.5 }}
          >
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
            <line x1="16" y1="2" x2="16" y2="6" />
            <line x1="8" y1="2" x2="8" y2="6" />
            <line x1="3" y1="10" x2="21" y2="10" />
          </svg>
          <p style={{ margin: 0, fontSize: '0.875rem' }}>No upcoming scheduled runs</p>
          <p style={{ margin: '0.5rem 0 0', fontSize: '0.75rem', opacity: 0.7 }}>
            Enable schedules to see them here
          </p>
        </div>
      ) : (
        <div style={listStyles}>
          <AnimatePresence mode="popLayout">
            {upcomingRuns.map((schedule, index) => (
              <motion.div
                key={schedule.schedule_id}
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2, delay: index * 0.05 }}
                style={itemStyles}
                onClick={() => handleItemClick(schedule)}
                onKeyDown={(e) => handleKeyDown(e, schedule)}
                tabIndex={0}
                role="button"
                aria-label={`${schedule.schedule_name} scheduled ${formatRelativeTime(schedule.next_run!)}`}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--bg-hover)';
                  e.currentTarget.style.borderColor = 'var(--border-default)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)';
                  e.currentTarget.style.borderColor = 'var(--border-subtle)';
                }}
              >
                {/* Priority indicator */}
                <div
                  style={{
                    ...priorityIndicatorStyles,
                    backgroundColor: getPriorityColor(schedule.priority),
                  }}
                  title={`Priority: ${schedule.priority}`}
                />

                {/* Content */}
                <div style={contentStyles}>
                  <div style={workflowNameStyles} title={schedule.workflow_id}>
                    {schedule.workflow_id.split('/').pop() || schedule.workflow_id}
                  </div>
                  <div style={scheduleNameStyles} title={schedule.schedule_name}>
                    {schedule.schedule_name}
                  </div>
                </div>

                {/* Time */}
                <div
                  style={{
                    ...timeStyles,
                    color: getTimeColor(schedule.next_run!),
                  }}
                >
                  {formatRelativeTime(schedule.next_run!)}
                </div>

                {/* Execution mode badge */}
                <div
                  style={{
                    marginLeft: 'var(--spacing-sm)',
                    padding: '2px 6px',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor:
                      schedule.execution_mode === 'lan'
                        ? 'rgba(34, 197, 94, 0.15)'
                        : 'rgba(59, 130, 246, 0.15)',
                    color:
                      schedule.execution_mode === 'lan'
                        ? 'var(--accent-green)'
                        : 'var(--accent-blue)',
                    fontSize: '0.65rem',
                    fontWeight: 500,
                    textTransform: 'uppercase',
                  }}
                >
                  {schedule.execution_mode}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* Summary footer */}
      {upcomingRuns.length > 0 && (
        <div
          style={{
            marginTop: 'var(--spacing-md)',
            paddingTop: 'var(--spacing-sm)',
            borderTop: '1px solid var(--border-subtle)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
          }}
        >
          <span>
            {schedules.filter((s) => s.enabled).length} active schedule
            {schedules.filter((s) => s.enabled).length !== 1 ? 's' : ''}
          </span>
          <span>
            {schedules.reduce((sum, s) => sum + s.run_count, 0)} total runs
          </span>
        </div>
      )}
    </Card>
  );
}

export default UpcomingRuns;

/**
 * ScheduleCalendar - Week view calendar for scheduled runs.
 *
 * Displays schedules as colored blocks at their next_run time.
 * Features:
 * - Hour slots from 6am to 11pm
 * - Enabled schedules in accent color, disabled in gray
 * - "Now" line indicator showing current time
 * - Navigation between weeks
 * - Click schedule to trigger callback
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import type { CSSProperties } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  startOfWeek,
  endOfWeek,
  addWeeks,
  subWeeks,
  format,
  isSameDay,
  isToday,
  getHours,
  getMinutes,
  parseISO,
  isWithinInterval,
  addDays,
} from 'date-fns';
import type { Schedule } from '@/hooks/useSchedules';

interface ScheduleCalendarProps {
  schedules: Schedule[];
  onScheduleClick?: (schedule: Schedule) => void;
  className?: string;
}

const HOUR_START = 6;
const HOUR_END = 23;
const HOUR_HEIGHT = 48; // pixels per hour
const HEADER_HEIGHT = 60;
const TIME_COLUMN_WIDTH = 60;

const containerStyles: CSSProperties = {
  backgroundColor: 'var(--bg-secondary)',
  border: '1px solid var(--border-subtle)',
  borderRadius: 'var(--radius-lg)',
  overflow: 'hidden',
};

const headerStyles: CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: 'var(--spacing-md)',
  borderBottom: '1px solid var(--border-subtle)',
  backgroundColor: 'var(--bg-tertiary)',
};

const navButtonStyles: CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  width: 32,
  height: 32,
  border: '1px solid var(--border-default)',
  borderRadius: 'var(--radius-md)',
  backgroundColor: 'transparent',
  color: 'var(--text-secondary)',
  cursor: 'pointer',
  transition: 'all var(--transition-fast)',
};

const dayHeaderStyles: CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: 'var(--spacing-sm)',
  borderBottom: '1px solid var(--border-subtle)',
  minHeight: HEADER_HEIGHT,
};

const hourLabelStyles: CSSProperties = {
  width: TIME_COLUMN_WIDTH,
  minWidth: TIME_COLUMN_WIDTH,
  fontSize: '0.75rem',
  color: 'var(--text-muted)',
  textAlign: 'right',
  paddingRight: 'var(--spacing-sm)',
  position: 'relative',
  top: -8,
};

const hourRowStyles: CSSProperties = {
  display: 'flex',
  height: HOUR_HEIGHT,
  borderBottom: '1px solid var(--border-subtle)',
};

const dayCellStyles: CSSProperties = {
  flex: 1,
  borderLeft: '1px solid var(--border-subtle)',
  position: 'relative',
};

function getScheduleStyle(schedule: Schedule): CSSProperties {
  const baseColor = schedule.enabled ? 'var(--accent-primary)' : 'var(--text-muted)';
  const backgroundColor = schedule.enabled
    ? 'rgba(99, 102, 241, 0.2)'
    : 'rgba(107, 114, 128, 0.2)';

  return {
    position: 'absolute',
    left: 2,
    right: 2,
    minHeight: 24,
    padding: '2px 6px',
    borderRadius: 'var(--radius-sm)',
    backgroundColor,
    borderLeft: `3px solid ${baseColor}`,
    cursor: 'pointer',
    overflow: 'hidden',
    fontSize: '0.75rem',
    color: schedule.enabled ? 'var(--text-primary)' : 'var(--text-muted)',
    transition: 'all var(--transition-fast)',
    zIndex: 1,
  };
}

function formatHour(hour: number): string {
  if (hour === 0) return '12 AM';
  if (hour === 12) return '12 PM';
  if (hour < 12) return `${hour} AM`;
  return `${hour - 12} PM`;
}

export function ScheduleCalendar({
  schedules,
  onScheduleClick,
  className = '',
}: ScheduleCalendarProps) {
  const [currentDate, setCurrentDate] = useState(() => new Date());
  const [now, setNow] = useState(() => new Date());

  // Update "now" every minute
  useEffect(() => {
    const interval = setInterval(() => {
      setNow(new Date());
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  const weekStart = useMemo(() => startOfWeek(currentDate, { weekStartsOn: 1 }), [currentDate]);
  const weekEnd = useMemo(() => endOfWeek(currentDate, { weekStartsOn: 1 }), [currentDate]);

  const weekDays = useMemo(() => {
    const days: Date[] = [];
    for (let i = 0; i < 7; i++) {
      days.push(addDays(weekStart, i));
    }
    return days;
  }, [weekStart]);

  const hours = useMemo(() => {
    const hoursArray: number[] = [];
    for (let h = HOUR_START; h <= HOUR_END; h++) {
      hoursArray.push(h);
    }
    return hoursArray;
  }, []);

  const schedulesInWeek = useMemo(() => {
    return schedules.filter((schedule) => {
      if (!schedule.next_run) return false;
      const runDate = parseISO(schedule.next_run);
      return isWithinInterval(runDate, { start: weekStart, end: weekEnd });
    });
  }, [schedules, weekStart, weekEnd]);

  const getSchedulesForDay = useCallback(
    (day: Date) => {
      return schedulesInWeek.filter((schedule) => {
        if (!schedule.next_run) return false;
        return isSameDay(parseISO(schedule.next_run), day);
      });
    },
    [schedulesInWeek]
  );

  const navigatePrevWeek = useCallback(() => {
    setCurrentDate((d) => subWeeks(d, 1));
  }, []);

  const navigateNextWeek = useCallback(() => {
    setCurrentDate((d) => addWeeks(d, 1));
  }, []);

  const navigateToday = useCallback(() => {
    setCurrentDate(new Date());
  }, []);

  // Calculate "now" line position
  const nowLinePosition = useMemo(() => {
    const currentHour = getHours(now);
    const currentMinute = getMinutes(now);

    if (currentHour < HOUR_START || currentHour > HOUR_END) {
      return null;
    }

    const minutesFromStart = (currentHour - HOUR_START) * 60 + currentMinute;
    const totalMinutes = (HOUR_END - HOUR_START + 1) * 60;
    const percentage = (minutesFromStart / totalMinutes) * 100;

    return percentage;
  }, [now]);

  const handleScheduleClick = useCallback(
    (schedule: Schedule, event: React.MouseEvent) => {
      event.stopPropagation();
      onScheduleClick?.(schedule);
    },
    [onScheduleClick]
  );

  return (
    <div className={className} style={containerStyles}>
      {/* Header with navigation */}
      <div style={headerStyles}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
          <button
            onClick={navigatePrevWeek}
            style={navButtonStyles}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--bg-hover)';
              e.currentTarget.style.borderColor = 'var(--accent-primary)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.borderColor = 'var(--border-default)';
            }}
            aria-label="Previous week"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M15 18l-6-6 6-6" />
            </svg>
          </button>
          <button
            onClick={navigateNextWeek}
            style={navButtonStyles}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--bg-hover)';
              e.currentTarget.style.borderColor = 'var(--accent-primary)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.borderColor = 'var(--border-default)';
            }}
            aria-label="Next week"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 18l6-6-6-6" />
            </svg>
          </button>
          <button
            onClick={navigateToday}
            style={{
              ...navButtonStyles,
              width: 'auto',
              padding: '0 var(--spacing-sm)',
              fontSize: '0.75rem',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--bg-hover)';
              e.currentTarget.style.borderColor = 'var(--accent-primary)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.borderColor = 'var(--border-default)';
            }}
          >
            Today
          </button>
        </div>

        <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
          {format(weekStart, 'MMM d')} - {format(weekEnd, 'MMM d, yyyy')}
        </h3>

        <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          {schedulesInWeek.length} scheduled run{schedulesInWeek.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Day headers */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{ width: TIME_COLUMN_WIDTH, minWidth: TIME_COLUMN_WIDTH }} />
        {weekDays.map((day) => (
          <div
            key={day.toISOString()}
            style={{
              ...dayHeaderStyles,
              flex: 1,
              backgroundColor: isToday(day) ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
            }}
          >
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 500,
                color: isToday(day) ? 'var(--accent-primary)' : 'var(--text-muted)',
                textTransform: 'uppercase',
              }}
            >
              {format(day, 'EEE')}
            </span>
            <span
              style={{
                fontSize: '1.25rem',
                fontWeight: 600,
                color: isToday(day) ? 'var(--accent-primary)' : 'var(--text-primary)',
                marginTop: 2,
              }}
            >
              {format(day, 'd')}
            </span>
          </div>
        ))}
      </div>

      {/* Time grid */}
      <div style={{ position: 'relative', overflowY: 'auto', maxHeight: 500 }}>
        {/* Now line indicator */}
        <AnimatePresence>
          {nowLinePosition !== null && isWithinInterval(now, { start: weekStart, end: weekEnd }) && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{
                position: 'absolute',
                top: `${nowLinePosition}%`,
                left: TIME_COLUMN_WIDTH,
                right: 0,
                height: 2,
                backgroundColor: 'var(--accent-red)',
                zIndex: 10,
                pointerEvents: 'none',
              }}
            >
              <div
                style={{
                  position: 'absolute',
                  left: -4,
                  top: -4,
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  backgroundColor: 'var(--accent-red)',
                }}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {hours.map((hour) => (
          <div key={hour} style={hourRowStyles}>
            <div style={hourLabelStyles}>{formatHour(hour)}</div>
            {weekDays.map((day) => {
              const daySchedules = getSchedulesForDay(day).filter((schedule) => {
                if (!schedule.next_run) return false;
                const runHour = getHours(parseISO(schedule.next_run));
                return runHour === hour;
              });

              return (
                <div
                  key={`${day.toISOString()}-${hour}`}
                  style={{
                    ...dayCellStyles,
                    backgroundColor: isToday(day) ? 'rgba(99, 102, 241, 0.03)' : 'transparent',
                  }}
                >
                  {daySchedules.map((schedule, index) => {
                    const runTime = parseISO(schedule.next_run!);
                    const minutes = getMinutes(runTime);
                    const topOffset = (minutes / 60) * HOUR_HEIGHT;

                    return (
                      <motion.div
                        key={schedule.schedule_id}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        whileHover={{ scale: 1.02, zIndex: 2 }}
                        style={{
                          ...getScheduleStyle(schedule),
                          top: topOffset + index * 2, // Slight offset for overlapping
                        }}
                        onClick={(e) => handleScheduleClick(schedule, e)}
                        title={`${schedule.schedule_name}\n${format(runTime, 'h:mm a')}\n${schedule.cron_expression}`}
                      >
                        <div
                          style={{
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            fontWeight: 500,
                          }}
                        >
                          {schedule.schedule_name}
                        </div>
                        <div style={{ fontSize: '0.65rem', opacity: 0.8 }}>
                          {format(runTime, 'h:mm a')}
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

export default ScheduleCalendar;

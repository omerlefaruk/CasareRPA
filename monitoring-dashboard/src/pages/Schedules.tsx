/**
 * Schedules - Schedule management page.
 *
 * Displays:
 * - Schedule calendar (week view)
 * - Upcoming runs sidebar
 * - Schedule list with enable/disable and trigger actions
 */

import { useState, useCallback } from 'react';
import type { CSSProperties } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  DashboardLayout,
  DashboardSection,
  DashboardRow,
  DashboardColumn,
} from '@/components/layout/DashboardLayout';
import { Card, CardHeader } from '@/components/ui/Card';
import { ScheduleCalendar } from '@/components/schedule/ScheduleCalendar';
import { UpcomingRuns } from '@/components/schedule/UpcomingRuns';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Skeleton } from '@/components/ui/Skeleton';
import { useSchedules, useToggleSchedule, useTriggerSchedule, type Schedule } from '@/hooks/useSchedules';
import { format, parseISO } from 'date-fns';

const tableContainerStyles: CSSProperties = {
  overflowX: 'auto',
  borderRadius: 'var(--radius-lg)',
  border: '1px solid var(--border-subtle)',
  backgroundColor: 'var(--bg-secondary)',
};

const tableStyles: CSSProperties = {
  width: '100%',
  borderCollapse: 'collapse',
  fontSize: '0.875rem',
};

const thStyles: CSSProperties = {
  padding: 'var(--spacing-md)',
  textAlign: 'left',
  fontWeight: 600,
  fontSize: '0.75rem',
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  color: 'var(--text-muted)',
  backgroundColor: 'var(--bg-tertiary)',
  borderBottom: '1px solid var(--border-subtle)',
};

const tdStyles: CSSProperties = {
  padding: 'var(--spacing-md)',
  borderBottom: '1px solid var(--border-subtle)',
  color: 'var(--text-primary)',
};

const actionButtonStyles: CSSProperties = {
  padding: 'var(--spacing-xs) var(--spacing-sm)',
  fontSize: '0.75rem',
  fontWeight: 500,
  borderRadius: 'var(--radius-sm)',
  border: 'none',
  cursor: 'pointer',
  transition: 'all var(--transition-fast)',
  display: 'inline-flex',
  alignItems: 'center',
  gap: 'var(--spacing-xs)',
};

const toggleButtonStyles = (enabled: boolean): CSSProperties => ({
  ...actionButtonStyles,
  backgroundColor: enabled ? 'rgba(239, 68, 68, 0.15)' : 'rgba(34, 197, 94, 0.15)',
  color: enabled ? 'var(--accent-red)' : 'var(--accent-green)',
});

const triggerButtonStyles: CSSProperties = {
  ...actionButtonStyles,
  backgroundColor: 'rgba(99, 102, 241, 0.15)',
  color: 'var(--accent-primary)',
};

const emptyStateStyles: CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: 'var(--spacing-2xl)',
  color: 'var(--text-muted)',
  textAlign: 'center',
};

const cronBadgeStyles: CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: '0.75rem',
  padding: '2px 6px',
  backgroundColor: 'var(--bg-tertiary)',
  borderRadius: 'var(--radius-sm)',
  color: 'var(--text-secondary)',
};

export function Schedules() {
  const { data: schedules = [], isLoading, error } = useSchedules();
  const toggleSchedule = useToggleSchedule();
  const triggerSchedule = useTriggerSchedule();

  const [selectedSchedule, setSelectedSchedule] = useState<Schedule | null>(null);

  const handleScheduleClick = useCallback((schedule: Schedule) => {
    setSelectedSchedule(schedule);
  }, []);

  const handleToggle = useCallback(
    async (schedule: Schedule) => {
      await toggleSchedule.mutateAsync({
        schedule_id: schedule.schedule_id,
        enabled: !schedule.enabled,
      });
    },
    [toggleSchedule]
  );

  const handleTrigger = useCallback(
    async (schedule: Schedule) => {
      await triggerSchedule.mutateAsync({
        schedule_id: schedule.schedule_id,
      });
    },
    [triggerSchedule]
  );

  const enabledSchedules = schedules.filter((s) => s.enabled).length;
  const totalRuns = schedules.reduce((sum, s) => sum + s.run_count, 0);

  return (
    <DashboardLayout
      pageTitle="Schedules"
      pageSubtitle={`${enabledSchedules} active schedules, ${totalRuns} total runs`}
    >
      <DashboardRow gap="lg">
        {/* Main Content - Calendar and List */}
        <DashboardColumn flex={3} minWidth="600px">
          {/* Calendar View */}
          <DashboardSection
            title="Schedule Calendar"
            subtitle="Weekly view of scheduled runs"
          >
            {isLoading ? (
              <Skeleton height={400} />
            ) : (
              <ScheduleCalendar
                schedules={schedules}
                onScheduleClick={handleScheduleClick}
              />
            )}
          </DashboardSection>

          {/* Schedule List */}
          <DashboardSection
            title="All Schedules"
            subtitle={`${schedules.length} schedules configured`}
          >
            {isLoading ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
                <Skeleton height={48} />
                <Skeleton height={48} />
                <Skeleton height={48} />
              </div>
            ) : error ? (
              <div style={emptyStateStyles}>
                <svg
                  width="48"
                  height="48"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  style={{ marginBottom: 'var(--spacing-md)', color: 'var(--accent-red)' }}
                >
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <p style={{ margin: 0, fontSize: '0.875rem' }}>Failed to load schedules</p>
                <p style={{ margin: '0.5rem 0 0', fontSize: '0.75rem', opacity: 0.7 }}>
                  {error.message}
                </p>
              </div>
            ) : schedules.length === 0 ? (
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
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
                <p style={{ margin: 0, fontSize: '0.875rem' }}>No schedules configured</p>
                <p style={{ margin: '0.5rem 0 0', fontSize: '0.75rem', opacity: 0.7 }}>
                  Create schedules via the Orchestrator API
                </p>
              </div>
            ) : (
              <div style={tableContainerStyles}>
                <table style={tableStyles}>
                  <thead>
                    <tr>
                      <th style={thStyles}>Schedule</th>
                      <th style={thStyles}>Workflow</th>
                      <th style={thStyles}>Cron</th>
                      <th style={thStyles}>Next Run</th>
                      <th style={thStyles}>Status</th>
                      <th style={thStyles}>Runs</th>
                      <th style={{ ...thStyles, textAlign: 'right' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    <AnimatePresence>
                      {schedules.map((schedule) => (
                        <motion.tr
                          key={schedule.schedule_id}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={{ opacity: 0 }}
                          style={{ cursor: 'pointer' }}
                          onClick={() => handleScheduleClick(schedule)}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.backgroundColor = 'var(--bg-hover)';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.backgroundColor = 'transparent';
                          }}
                        >
                          <td style={tdStyles}>
                            <div style={{ fontWeight: 500 }}>{schedule.schedule_name}</div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                              ID: {schedule.schedule_id.slice(0, 8)}
                            </div>
                          </td>
                          <td style={tdStyles}>
                            <div
                              style={{
                                maxWidth: 200,
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                              }}
                              title={schedule.workflow_id}
                            >
                              {schedule.workflow_id.split('/').pop() || schedule.workflow_id}
                            </div>
                          </td>
                          <td style={tdStyles}>
                            <span style={cronBadgeStyles}>{schedule.cron_expression}</span>
                          </td>
                          <td style={tdStyles}>
                            {schedule.next_run ? (
                              <div>
                                <div>{format(parseISO(schedule.next_run), 'MMM d, yyyy')}</div>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                  {format(parseISO(schedule.next_run), 'h:mm a')}
                                </div>
                              </div>
                            ) : (
                              <span style={{ color: 'var(--text-muted)' }}>-</span>
                            )}
                          </td>
                          <td style={tdStyles}>
                            <StatusBadge status={schedule.enabled ? 'idle' : 'offline'} />
                          </td>
                          <td style={tdStyles}>
                            <div>{schedule.run_count}</div>
                            {schedule.failure_count > 0 && (
                              <div style={{ fontSize: '0.75rem', color: 'var(--accent-red)' }}>
                                {schedule.failure_count} failed
                              </div>
                            )}
                          </td>
                          <td style={{ ...tdStyles, textAlign: 'right' }}>
                            <div
                              style={{ display: 'flex', gap: 'var(--spacing-xs)', justifyContent: 'flex-end' }}
                              onClick={(e) => e.stopPropagation()}
                            >
                              <button
                                style={toggleButtonStyles(schedule.enabled)}
                                onClick={() => handleToggle(schedule)}
                                disabled={toggleSchedule.isPending}
                                onMouseEnter={(e) => {
                                  e.currentTarget.style.opacity = '0.8';
                                }}
                                onMouseLeave={(e) => {
                                  e.currentTarget.style.opacity = '1';
                                }}
                              >
                                {schedule.enabled ? 'Disable' : 'Enable'}
                              </button>
                              <button
                                style={triggerButtonStyles}
                                onClick={() => handleTrigger(schedule)}
                                disabled={triggerSchedule.isPending || !schedule.enabled}
                                onMouseEnter={(e) => {
                                  e.currentTarget.style.opacity = '0.8';
                                }}
                                onMouseLeave={(e) => {
                                  e.currentTarget.style.opacity = '1';
                                }}
                              >
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                                  <polygon points="5 3 19 12 5 21 5 3" />
                                </svg>
                                Run Now
                              </button>
                            </div>
                          </td>
                        </motion.tr>
                      ))}
                    </AnimatePresence>
                  </tbody>
                </table>
              </div>
            )}
          </DashboardSection>
        </DashboardColumn>

        {/* Right Sidebar - Upcoming Runs & Details */}
        <DashboardColumn flex={1} minWidth="320px" maxWidth="400px">
          {/* Upcoming Runs */}
          <DashboardSection title="Upcoming">
            <UpcomingRuns
              schedules={schedules}
              onScheduleClick={handleScheduleClick}
              limit={8}
            />
          </DashboardSection>

          {/* Selected Schedule Details */}
          <AnimatePresence>
            {selectedSchedule && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <DashboardSection title="Schedule Details">
                  <Card padding="md" variant="default">
                    <CardHeader
                      title={selectedSchedule.schedule_name}
                      subtitle={`ID: ${selectedSchedule.schedule_id}`}
                    />
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
                      <DetailRow label="Workflow" value={selectedSchedule.workflow_id.split('/').pop() || selectedSchedule.workflow_id} />
                      <DetailRow label="Cron Expression" value={selectedSchedule.cron_expression} mono />
                      <DetailRow label="Execution Mode" value={selectedSchedule.execution_mode.toUpperCase()} />
                      <DetailRow label="Priority" value={String(selectedSchedule.priority)} />
                      <DetailRow label="Status" value={selectedSchedule.enabled ? 'Enabled' : 'Disabled'} />
                      <DetailRow label="Total Runs" value={String(selectedSchedule.run_count)} />
                      <DetailRow label="Failures" value={String(selectedSchedule.failure_count)} />
                      {selectedSchedule.last_run && (
                        <DetailRow
                          label="Last Run"
                          value={format(parseISO(selectedSchedule.last_run), 'MMM d, yyyy h:mm a')}
                        />
                      )}
                      {selectedSchedule.next_run && (
                        <DetailRow
                          label="Next Run"
                          value={format(parseISO(selectedSchedule.next_run), 'MMM d, yyyy h:mm a')}
                        />
                      )}
                      <DetailRow
                        label="Created"
                        value={format(parseISO(selectedSchedule.created_at), 'MMM d, yyyy')}
                      />
                    </div>

                    {/* Action Buttons */}
                    <div
                      style={{
                        marginTop: 'var(--spacing-lg)',
                        paddingTop: 'var(--spacing-md)',
                        borderTop: '1px solid var(--border-subtle)',
                        display: 'flex',
                        gap: 'var(--spacing-sm)',
                      }}
                    >
                      <button
                        style={{
                          ...toggleButtonStyles(selectedSchedule.enabled),
                          flex: 1,
                          justifyContent: 'center',
                          padding: 'var(--spacing-sm)',
                        }}
                        onClick={() => handleToggle(selectedSchedule)}
                        disabled={toggleSchedule.isPending}
                      >
                        {selectedSchedule.enabled ? 'Disable Schedule' : 'Enable Schedule'}
                      </button>
                      <button
                        style={{
                          ...triggerButtonStyles,
                          flex: 1,
                          justifyContent: 'center',
                          padding: 'var(--spacing-sm)',
                        }}
                        onClick={() => handleTrigger(selectedSchedule)}
                        disabled={triggerSchedule.isPending || !selectedSchedule.enabled}
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                          <polygon points="5 3 19 12 5 21 5 3" />
                        </svg>
                        Run Now
                      </button>
                    </div>
                  </Card>
                </DashboardSection>
              </motion.div>
            )}
          </AnimatePresence>
        </DashboardColumn>
      </DashboardRow>
    </DashboardLayout>
  );
}

interface DetailRowProps {
  label: string;
  value: string;
  mono?: boolean;
}

function DetailRow({ label, value, mono = false }: DetailRowProps) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{label}</span>
      <span
        style={{
          fontSize: '0.875rem',
          color: 'var(--text-primary)',
          fontFamily: mono ? 'var(--font-mono)' : 'inherit',
          maxWidth: '60%',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          textAlign: 'right',
        }}
        title={value}
      >
        {value}
      </span>
    </div>
  );
}

export default Schedules;

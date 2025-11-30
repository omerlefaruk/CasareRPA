/**
 * RobotDetail - Individual robot monitoring page.
 *
 * Displays detailed metrics and job history for a single robot.
 * Uses DashboardLayout for consistent navigation.
 */

import type { CSSProperties } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  DashboardLayout,
  DashboardSection,
  DashboardGrid,
} from '@/components/layout/DashboardLayout';
import { KPICard } from '@/components/ui/KPICard';
import { Card } from '@/components/ui/Card';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Skeleton } from '@/components/ui/Skeleton';
import { useRobotDetails } from '@/hooks/useRobots';
import { useJobs } from '@/hooks/useJobs';

const tableContainerStyles: CSSProperties = {
  overflowX: 'auto',
  borderRadius: 'var(--radius-lg)',
  border: '1px solid var(--border-subtle)',
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

const backLinkStyles: CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: 'var(--spacing-xs)',
  color: 'var(--accent-primary)',
  textDecoration: 'none',
  fontSize: '0.875rem',
  fontWeight: 500,
  marginBottom: 'var(--spacing-lg)',
};

function RobotDetail() {
  const { robotId } = useParams<{ robotId: string }>();

  const { data: robot, isLoading, error } = useRobotDetails(robotId!);
  const { data: robotJobs, isLoading: jobsLoading } = useJobs({ robot_id: robotId, limit: 20 });

  if (isLoading) {
    return (
      <DashboardLayout pageTitle="Robot Details" pageSubtitle="Loading...">
        <Link to="/fleet" style={backLinkStyles}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          Back to Fleet
        </Link>
        <DashboardGrid columns={4} gap="lg">
          <Skeleton height={120} />
          <Skeleton height={120} />
          <Skeleton height={120} />
          <Skeleton height={120} />
        </DashboardGrid>
      </DashboardLayout>
    );
  }

  if (error || !robot) {
    return (
      <DashboardLayout pageTitle="Robot Details" pageSubtitle="Error">
        <Link to="/fleet" style={backLinkStyles}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          Back to Fleet
        </Link>
        <Card padding="lg" variant="default">
          <div style={{ textAlign: 'center', color: 'var(--accent-red)' }}>
            <svg
              width="48"
              height="48"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              style={{ margin: '0 auto var(--spacing-md)' }}
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <p>{error ? 'Failed to load robot details' : 'Robot not found'}</p>
            {error && <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>{error.message}</p>}
          </div>
        </Card>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout
      pageTitle={`Robot: ${robot.hostname}`}
      pageSubtitle={robot.robot_id}
    >
      {/* Back Link */}
      <Link to="/fleet" style={backLinkStyles}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M19 12H5M12 19l-7-7 7-7" />
        </svg>
        Back to Fleet
      </Link>

      {/* Status KPIs */}
      <DashboardSection>
        <DashboardGrid columns={4} gap="lg">
          <KPICard
            title="Status"
            value={robot.status === 'busy' ? 1 : robot.status === 'idle' ? 2 : 0}
            accentColor={
              robot.status === 'busy' ? 'var(--accent-orange)' :
              robot.status === 'idle' ? 'var(--accent-green)' :
              'var(--text-muted)'
            }
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 6v6l4 2" />
              </svg>
            }
          />
          <KPICard
            title="CPU Usage"
            value={robot.cpu_percent}
            format="percentage"
            accentColor={robot.cpu_percent > 80 ? 'var(--accent-red)' : 'var(--accent-green)'}
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="4" y="4" width="16" height="16" rx="2" />
                <rect x="9" y="9" width="6" height="6" />
                <line x1="9" y1="1" x2="9" y2="4" />
                <line x1="15" y1="1" x2="15" y2="4" />
                <line x1="9" y1="20" x2="9" y2="23" />
                <line x1="15" y1="20" x2="15" y2="23" />
              </svg>
            }
          />
          <KPICard
            title="Memory"
            value={robot.memory_mb}
            suffix=" MB"
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="2" y="6" width="20" height="12" rx="2" />
                <line x1="6" y1="10" x2="6" y2="14" />
                <line x1="10" y1="10" x2="10" y2="14" />
                <line x1="14" y1="10" x2="14" y2="14" />
                <line x1="18" y1="10" x2="18" y2="14" />
              </svg>
            }
          />
          <KPICard
            title="Current Job"
            value={robot.current_job_id ? 1 : 0}
            accentColor={robot.current_job_id ? 'var(--accent-orange)' : 'var(--text-muted)'}
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
                <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
              </svg>
            }
          />
        </DashboardGrid>
      </DashboardSection>

      {/* Performance Metrics */}
      <DashboardSection title="Performance">
        <DashboardGrid columns={3} gap="lg">
          <KPICard
            title="Jobs Completed Today"
            value={robot.jobs_completed_today}
            accentColor="var(--accent-green)"
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            }
          />
          <KPICard
            title="Jobs Failed Today"
            value={robot.jobs_failed_today}
            accentColor={robot.jobs_failed_today > 0 ? 'var(--accent-red)' : 'var(--text-muted)'}
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="15" y1="9" x2="9" y2="15" />
                <line x1="9" y1="9" x2="15" y2="15" />
              </svg>
            }
          />
          <KPICard
            title="Avg Duration"
            value={robot.average_job_duration_seconds}
            format="duration"
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 16 14" />
              </svg>
            }
          />
        </DashboardGrid>
      </DashboardSection>

      {/* Recent Jobs */}
      <DashboardSection
        title="Recent Jobs"
        subtitle={`${robotJobs?.length ?? 0} jobs`}
      >
        {jobsLoading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
            <Skeleton height={48} />
            <Skeleton height={48} />
            <Skeleton height={48} />
          </div>
        ) : robotJobs && robotJobs.length > 0 ? (
          <div style={tableContainerStyles}>
            <table style={tableStyles}>
              <thead>
                <tr>
                  <th style={thStyles}>Job ID</th>
                  <th style={thStyles}>Workflow</th>
                  <th style={thStyles}>Status</th>
                  <th style={thStyles}>Duration</th>
                  <th style={thStyles}>Completed</th>
                </tr>
              </thead>
              <tbody>
                {robotJobs.map((job) => (
                  <tr
                    key={job.job_id}
                    style={{ transition: 'background-color var(--transition-fast)' }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--bg-hover)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                  >
                    <td style={tdStyles}>
                      <code style={{ fontSize: '0.875rem', fontFamily: 'var(--font-mono)' }}>
                        {job.job_id.slice(0, 8)}
                      </code>
                    </td>
                    <td style={tdStyles}>{job.workflow_name || job.workflow_id}</td>
                    <td style={tdStyles}>
                      <StatusBadge status={job.status} />
                    </td>
                    <td style={tdStyles}>
                      {job.duration_ms ? (
                        <span style={{ color: 'var(--text-secondary)' }}>
                          {(job.duration_ms / 1000).toFixed(1)}s
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>-</span>
                      )}
                    </td>
                    <td style={{ ...tdStyles, color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                      {job.completed_at ? new Date(job.completed_at).toLocaleString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Card padding="lg" variant="default">
            <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
              <svg
                width="48"
                height="48"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                style={{ margin: '0 auto var(--spacing-md)', opacity: 0.5 }}
              >
                <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
                <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
              </svg>
              <p style={{ margin: 0, fontSize: '0.875rem' }}>No recent jobs</p>
            </div>
          </Card>
        )}
      </DashboardSection>
    </DashboardLayout>
  );
}

export default RobotDetail;

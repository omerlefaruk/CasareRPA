/**
 * WorkflowExecution - Job queue and execution history page.
 *
 * Displays job history with filtering and live updates.
 * Uses DashboardLayout for consistent navigation.
 */

import { useState } from 'react';
import type { CSSProperties } from 'react';
import {
  DashboardLayout,
  DashboardSection,
} from '@/components/layout/DashboardLayout';
import { Card } from '@/components/ui/Card';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Skeleton } from '@/components/ui/Skeleton';
import { useJobs } from '@/hooks/useJobs';
import { useLiveJobs } from '@/api/websockets';

const filterContainerStyles: CSSProperties = {
  display: 'flex',
  gap: 'var(--spacing-md)',
  alignItems: 'center',
  padding: 'var(--spacing-md)',
  backgroundColor: 'var(--bg-secondary)',
  borderRadius: 'var(--radius-lg)',
  border: '1px solid var(--border-subtle)',
  marginBottom: 'var(--spacing-lg)',
};

const selectStyles: CSSProperties = {
  marginLeft: 'var(--spacing-sm)',
  padding: 'var(--spacing-sm) var(--spacing-md)',
  backgroundColor: 'var(--bg-tertiary)',
  border: '1px solid var(--border-default)',
  borderRadius: 'var(--radius-md)',
  color: 'var(--text-primary)',
  fontSize: '0.875rem',
  cursor: 'pointer',
};

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

function WorkflowExecution() {
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [limit] = useState(50);

  const { data: jobs, isLoading, error, refetch } = useJobs({
    status: statusFilter,
    limit,
  });

  // WebSocket for live job updates
  const isLive = useLiveJobs((message) => {
    console.log('[Live Job Update]', message);
    refetch();
  });

  return (
    <DashboardLayout
      pageTitle="Workflow Execution"
      pageSubtitle="Monitor job execution history and live updates"
      connectionStatus={isLive ? 'connected' : 'disconnected'}
    >
      {/* Filters */}
      <div style={filterContainerStyles}>
        <label style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', display: 'flex', alignItems: 'center' }}>
          Status:
          <select
            value={statusFilter ?? ''}
            onChange={(e) => setStatusFilter(e.target.value || undefined)}
            style={selectStyles}
          >
            <option value="">All</option>
            <option value="pending">Pending</option>
            <option value="queued">Queued</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </label>
        {isLive && (
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 'var(--spacing-xs)',
              fontSize: '0.75rem',
              fontWeight: 500,
              color: 'var(--accent-green)',
              marginLeft: 'auto',
            }}
          >
            <span
              style={{
                width: 6,
                height: 6,
                borderRadius: '50%',
                backgroundColor: 'var(--accent-green)',
                animation: 'pulse 1.5s infinite',
              }}
            />
            Live Updates
          </span>
        )}
      </div>

      {/* Job History Table */}
      <DashboardSection
        title="Job History"
        subtitle={`${jobs?.length ?? 0} jobs`}
      >
        {error ? (
          <Card padding="lg" variant="default">
            <div style={{ textAlign: 'center', color: 'var(--accent-red)' }}>
              <svg
                width="48"
                height="48"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                style={{ marginBottom: 'var(--spacing-md)', margin: '0 auto var(--spacing-md)' }}
              >
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <p>Failed to load job history</p>
              <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>{error.message}</p>
            </div>
          </Card>
        ) : isLoading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
            <Skeleton height={48} />
            <Skeleton height={48} />
            <Skeleton height={48} />
            <Skeleton height={48} />
            <Skeleton height={48} />
          </div>
        ) : jobs && jobs.length > 0 ? (
          <div style={tableContainerStyles}>
            <table style={tableStyles}>
              <thead>
                <tr>
                  <th style={thStyles}>Job ID</th>
                  <th style={thStyles}>Workflow</th>
                  <th style={thStyles}>Robot</th>
                  <th style={thStyles}>Status</th>
                  <th style={thStyles}>Duration</th>
                  <th style={thStyles}>Created</th>
                  <th style={thStyles}>Completed</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
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
                      {job.robot_id ? (
                        <code style={{ fontSize: '0.875rem', fontFamily: 'var(--font-mono)' }}>
                          {job.robot_id.slice(0, 8)}
                        </code>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>-</span>
                      )}
                    </td>
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
                      {new Date(job.created_at).toLocaleString()}
                    </td>
                    <td style={{ ...tdStyles, fontSize: '0.875rem' }}>
                      {job.completed_at ? (
                        <span style={{ color: 'var(--text-muted)' }}>
                          {new Date(job.completed_at).toLocaleString()}
                        </span>
                      ) : (
                        <span style={{ color: 'var(--accent-orange)' }}>Running...</span>
                      )}
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
                style={{ marginBottom: 'var(--spacing-md)', opacity: 0.5, margin: '0 auto var(--spacing-md)' }}
              >
                <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
                <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
              </svg>
              <p style={{ margin: 0, fontSize: '0.875rem' }}>No jobs found</p>
              {statusFilter && (
                <p style={{ margin: '0.5rem 0 0', fontSize: '0.75rem', opacity: 0.7 }}>
                  Try changing the status filter
                </p>
              )}
            </div>
          </Card>
        )}
      </DashboardSection>
    </DashboardLayout>
  );
}

export default WorkflowExecution;

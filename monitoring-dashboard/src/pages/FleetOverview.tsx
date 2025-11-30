/**
 * FleetOverview - Robot fleet management page.
 *
 * Displays all robots with their status, metrics, and job history.
 * Uses DashboardLayout for consistent navigation.
 */

import type { CSSProperties } from 'react';
import { Link } from 'react-router-dom';
import {
  DashboardLayout,
  DashboardSection,
  DashboardGrid,
} from '@/components/layout/DashboardLayout';
import { KPICard } from '@/components/ui/KPICard';
import { Card } from '@/components/ui/Card';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Skeleton } from '@/components/ui/Skeleton';
import { useFleetMetrics } from '@/hooks/useFleetMetrics';
import { useRobots } from '@/hooks/useRobots';
import { useQueueMetrics } from '@/api/websockets';

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

const linkStyles: CSSProperties = {
  color: 'var(--accent-primary)',
  textDecoration: 'none',
  fontSize: '0.875rem',
  fontWeight: 500,
};

function FleetOverview() {
  const { data: fleetMetrics, error: metricsError } = useFleetMetrics();
  const { data: robots, isLoading: robotsLoading } = useRobots();

  // WebSocket for real-time queue depth
  const { lastMessage: queueMessage } = useQueueMetrics();

  const queueDepth = queueMessage?.depth ?? fleetMetrics?.queue_depth ?? 0;
  const isConnected = !!queueMessage;

  return (
    <DashboardLayout
      pageTitle="Fleet Overview"
      pageSubtitle="Monitor your multi-robot RPA fleet in real-time"
      connectionStatus={isConnected ? 'connected' : 'disconnected'}
    >
      {/* KPI Metrics */}
      <DashboardSection>
        <DashboardGrid columns={4} gap="lg">
          <KPICard
            title="Total Robots"
            value={fleetMetrics?.total_robots ?? 0}
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="2" y="6" width="20" height="12" rx="2" />
                <path d="M12 12h.01" />
                <path d="M17 12h.01" />
                <path d="M7 12h.01" />
              </svg>
            }
          />
          <KPICard
            title="Active Robots"
            value={fleetMetrics?.active_robots ?? 0}
            accentColor="var(--accent-green)"
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            }
          />
          <KPICard
            title="Active Jobs"
            value={fleetMetrics?.active_jobs ?? 0}
            accentColor="var(--accent-orange)"
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
            }
          />
          <KPICard
            title="Queue Depth"
            value={queueDepth}
            accentColor={queueDepth > 10 ? 'var(--accent-red)' : 'var(--accent-primary)'}
            isLive={isConnected}
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="8" y1="6" x2="21" y2="6" />
                <line x1="8" y1="12" x2="21" y2="12" />
                <line x1="8" y1="18" x2="21" y2="18" />
                <line x1="3" y1="6" x2="3.01" y2="6" />
                <line x1="3" y1="12" x2="3.01" y2="12" />
                <line x1="3" y1="18" x2="3.01" y2="18" />
              </svg>
            }
          />
        </DashboardGrid>
      </DashboardSection>

      {/* Secondary Metrics */}
      <DashboardSection>
        <DashboardGrid columns={2} gap="lg">
          <KPICard
            title="Jobs Today"
            value={fleetMetrics?.total_jobs_today ?? 0}
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                <line x1="16" y1="2" x2="16" y2="6" />
                <line x1="8" y1="2" x2="8" y2="6" />
                <line x1="3" y1="10" x2="21" y2="10" />
              </svg>
            }
          />
          <KPICard
            title="Avg Duration"
            value={fleetMetrics?.average_job_duration_seconds ?? 0}
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

      {/* Robot Status Table */}
      <DashboardSection
        title="Robot Status"
        subtitle={`${robots?.length ?? 0} robots registered`}
      >
        {metricsError ? (
          <Card padding="lg" variant="default">
            <div style={{ textAlign: 'center', color: 'var(--accent-red)' }}>
              <p>Failed to load fleet metrics</p>
              <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>{metricsError.message}</p>
            </div>
          </Card>
        ) : robotsLoading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
            <Skeleton height={48} />
            <Skeleton height={48} />
            <Skeleton height={48} />
          </div>
        ) : robots && robots.length > 0 ? (
          <div style={tableContainerStyles}>
            <table style={tableStyles}>
              <thead>
                <tr>
                  <th style={thStyles}>Robot ID</th>
                  <th style={thStyles}>Hostname</th>
                  <th style={thStyles}>Status</th>
                  <th style={thStyles}>Current Job</th>
                  <th style={thStyles}>Last Seen</th>
                  <th style={{ ...thStyles, textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {robots.map((robot) => (
                  <tr
                    key={robot.robot_id}
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
                        {robot.robot_id.slice(0, 8)}
                      </code>
                    </td>
                    <td style={tdStyles}>{robot.hostname}</td>
                    <td style={tdStyles}>
                      <StatusBadge status={robot.status} />
                    </td>
                    <td style={tdStyles}>
                      {robot.current_job_id ? (
                        <code style={{ fontSize: '0.875rem', fontFamily: 'var(--font-mono)' }}>
                          {robot.current_job_id.slice(0, 8)}
                        </code>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>-</span>
                      )}
                    </td>
                    <td style={{ ...tdStyles, color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                      {new Date(robot.last_seen ?? Date.now()).toLocaleString()}
                    </td>
                    <td style={{ ...tdStyles, textAlign: 'right' }}>
                      <Link to={`/robots/${robot.robot_id}`} style={linkStyles}>
                        View Details
                        <svg
                          width="14"
                          height="14"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          style={{ marginLeft: '4px', verticalAlign: 'middle' }}
                        >
                          <path d="M5 12h14M12 5l7 7-7 7" />
                        </svg>
                      </Link>
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
                <rect x="2" y="6" width="20" height="12" rx="2" />
                <path d="M12 12h.01" />
                <path d="M17 12h.01" />
                <path d="M7 12h.01" />
              </svg>
              <p style={{ margin: 0, fontSize: '0.875rem' }}>No robots registered yet</p>
              <p style={{ margin: '0.5rem 0 0', fontSize: '0.75rem', opacity: 0.7 }}>
                Robots will appear here once they connect to the orchestrator
              </p>
            </div>
          </Card>
        )}
      </DashboardSection>
    </DashboardLayout>
  );
}

export default FleetOverview;

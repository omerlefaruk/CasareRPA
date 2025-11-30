/**
 * Analytics - Performance metrics and insights page.
 *
 * Displays workflow execution analytics, duration percentiles,
 * and error distribution.
 * Uses DashboardLayout for consistent navigation.
 */

import type { CSSProperties } from 'react';
import {
  DashboardLayout,
  DashboardSection,
  DashboardGrid,
} from '@/components/layout/DashboardLayout';
import { KPICard } from '@/components/ui/KPICard';
import { Card } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { useAnalytics } from '@/hooks/useAnalytics';

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

const progressBarContainerStyles: CSSProperties = {
  flex: 1,
  height: 8,
  backgroundColor: 'var(--bg-tertiary)',
  borderRadius: 'var(--radius-sm)',
  overflow: 'hidden',
};

function Analytics() {
  const { data: analytics, isLoading, error } = useAnalytics();

  if (error) {
    return (
      <DashboardLayout pageTitle="Analytics" pageSubtitle="Workflow execution insights and trends">
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
            <p>Failed to load analytics</p>
            <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>{error.message}</p>
          </div>
        </Card>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout
      pageTitle="Analytics"
      pageSubtitle="Workflow execution insights and trends"
    >
      {/* Success/Failure Rates */}
      <DashboardSection>
        <DashboardGrid columns={3} gap="lg">
          <KPICard
            title="Success Rate"
            value={analytics?.success_rate ?? 0}
            format="percentage"
            accentColor="var(--accent-green)"
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            }
          />
          <KPICard
            title="Failure Rate"
            value={analytics?.failure_rate ?? 0}
            format="percentage"
            accentColor={
              (analytics?.failure_rate ?? 0) > 10 ? 'var(--accent-red)' : 'var(--text-muted)'
            }
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="15" y1="9" x2="9" y2="15" />
                <line x1="9" y1="9" x2="15" y2="15" />
              </svg>
            }
          />
          <KPICard
            title="Self-Healing Success"
            value={analytics?.self_healing_success_rate ?? 0}
            format="percentage"
            accentColor={
              analytics?.self_healing_success_rate ? 'var(--accent-green)' : 'var(--text-muted)'
            }
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z" />
              </svg>
            }
          />
        </DashboardGrid>
      </DashboardSection>

      {/* Duration Percentiles */}
      <DashboardSection
        title="Job Duration Percentiles"
        subtitle="Performance distribution across all jobs"
      >
        {isLoading ? (
          <DashboardGrid columns={3} gap="lg">
            <Skeleton height={120} />
            <Skeleton height={120} />
            <Skeleton height={120} />
          </DashboardGrid>
        ) : (
          <DashboardGrid columns={3} gap="lg">
            <KPICard
              title="P50 (Median)"
              value={(analytics?.p50_duration_ms ?? 0) / 1000}
              format="duration"
              icon={
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
              }
            />
            <KPICard
              title="P90"
              value={(analytics?.p90_duration_ms ?? 0) / 1000}
              format="duration"
              icon={
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
              }
            />
            <KPICard
              title="P99"
              value={(analytics?.p99_duration_ms ?? 0) / 1000}
              format="duration"
              accentColor="var(--accent-orange)"
              icon={
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
              }
            />
          </DashboardGrid>
        )}
      </DashboardSection>

      {/* Slowest Workflows */}
      <DashboardSection
        title="Slowest Workflows"
        subtitle="Workflows with longest average execution times"
      >
        {isLoading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
            <Skeleton height={48} />
            <Skeleton height={48} />
            <Skeleton height={48} />
          </div>
        ) : analytics?.slowest_workflows && analytics.slowest_workflows.length > 0 ? (
          <div style={tableContainerStyles}>
            <table style={tableStyles}>
              <thead>
                <tr>
                  <th style={thStyles}>Workflow Name</th>
                  <th style={thStyles}>Workflow ID</th>
                  <th style={thStyles}>Average Duration</th>
                </tr>
              </thead>
              <tbody>
                {analytics.slowest_workflows.map((workflow, index) => (
                  <tr
                    key={workflow.workflow_id}
                    style={{ transition: 'background-color var(--transition-fast)' }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--bg-hover)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                  >
                    <td style={tdStyles}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            width: 24,
                            height: 24,
                            borderRadius: 'var(--radius-full)',
                            backgroundColor: 'var(--bg-tertiary)',
                            color: 'var(--text-muted)',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                          }}
                        >
                          {index + 1}
                        </span>
                        {workflow.workflow_name}
                      </div>
                    </td>
                    <td style={tdStyles}>
                      <code style={{ fontSize: '0.875rem', fontFamily: 'var(--font-mono)' }}>
                        {workflow.workflow_id}
                      </code>
                    </td>
                    <td style={{ ...tdStyles, color: 'var(--accent-orange)', fontWeight: 600 }}>
                      {(workflow.average_duration_ms / 1000).toFixed(1)}s
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
                <line x1="18" y1="20" x2="18" y2="10" />
                <line x1="12" y1="20" x2="12" y2="4" />
                <line x1="6" y1="20" x2="6" y2="14" />
              </svg>
              <p style={{ margin: 0, fontSize: '0.875rem' }}>No workflow data available</p>
            </div>
          </Card>
        )}
      </DashboardSection>

      {/* Error Distribution */}
      <DashboardSection
        title="Error Distribution"
        subtitle="Breakdown of error types across all jobs"
      >
        {isLoading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
            <Skeleton height={48} />
            <Skeleton height={48} />
            <Skeleton height={48} />
          </div>
        ) : analytics?.error_distribution && analytics.error_distribution.length > 0 ? (
          <div style={tableContainerStyles}>
            <table style={tableStyles}>
              <thead>
                <tr>
                  <th style={thStyles}>Error Type</th>
                  <th style={thStyles}>Count</th>
                  <th style={thStyles}>Percentage</th>
                </tr>
              </thead>
              <tbody>
                {analytics.error_distribution.map((err) => {
                  const totalErrors = analytics.error_distribution.reduce(
                    (sum, e) => sum + e.count,
                    0
                  );
                  const percentage = (err.count / totalErrors) * 100;

                  return (
                    <tr
                      key={err.error_type}
                      style={{ transition: 'background-color var(--transition-fast)' }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = 'var(--bg-hover)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'transparent';
                      }}
                    >
                      <td style={tdStyles}>
                        <code style={{ fontSize: '0.875rem', color: 'var(--accent-red)', fontFamily: 'var(--font-mono)' }}>
                          {err.error_type}
                        </code>
                      </td>
                      <td style={tdStyles}>{err.count}</td>
                      <td style={tdStyles}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
                          <div style={progressBarContainerStyles}>
                            <div
                              style={{
                                width: `${percentage}%`,
                                height: '100%',
                                backgroundColor: 'var(--accent-red)',
                                transition: 'width var(--transition-normal)',
                              }}
                            />
                          </div>
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem', minWidth: 48 }}>
                            {percentage.toFixed(1)}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
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
                stroke="var(--accent-green)"
                strokeWidth="1.5"
                style={{ margin: '0 auto var(--spacing-md)' }}
              >
                <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
              <p style={{ margin: 0, fontSize: '0.875rem' }}>No error data available</p>
              <p style={{ margin: '0.5rem 0 0', fontSize: '0.75rem', color: 'var(--accent-green)' }}>
                No errors detected - great job!
              </p>
            </div>
          </Card>
        )}
      </DashboardSection>
    </DashboardLayout>
  );
}

export default Analytics;

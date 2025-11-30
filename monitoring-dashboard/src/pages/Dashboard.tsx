/**
 * Dashboard - Main unified monitoring page for CasareRPA.
 *
 * Layout Structure (1200px+ desktop):
 * +------------------+------------------+------------------+------------------+
 * |   Total Robots   |   Active Jobs    |   Success Rate   |   Queue Depth    |
 * +------------------+------------------+------------------+------------------+
 * |                                                        |                  |
 * |                   Robot Fleet Grid                     |   Activity Feed  |
 * |                   (2/3 width)                          |   (1/3 width)    |
 * |                                                        |                  |
 * +--------------------------------------------------------+------------------+
 * |                                                        |                  |
 * |              Schedule Calendar                         |  Upcoming Runs   |
 * |              (2/3 width)                               |  (1/3 width)     |
 * |                                                        |                  |
 * +--------------------------------------------------------+------------------+
 *
 * Features:
 * - WebSocket real-time updates
 * - Loading skeletons
 * - Error handling with retry
 * - Click navigation to detail pages
 */

import { useCallback, useMemo } from 'react';
import type { CSSProperties } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  DashboardLayout,
  EmptyState,
} from '../components/layout/DashboardLayout';
import { KPICard } from '../components/ui/KPICard';
import { Skeleton, SkeletonCard } from '../components/ui/Skeleton';
import { RobotGrid } from '../components/fleet/RobotGrid';
import { ActivityFeed } from '../components/activity/ActivityFeed';
import { ScheduleCalendar } from '../components/schedule/ScheduleCalendar';
import { UpcomingRuns } from '../components/schedule/UpcomingRuns';
import { useCriticalMetrics } from '../hooks/useCriticalMetrics';
import { useRobots } from '../hooks/useRobots';
import { useWebSocketManager } from '../hooks/useWebSocketManager';
import { useSchedules } from '../hooks/useSchedules';
import {
  useMetricsStore,
  selectActivityEvents,
} from '../store/metricsStore';
import type { RobotSummary } from '../components/fleet/RobotCard';
import type { ActivityEvent } from '../components/activity/ActivityFeed';
import type { Schedule } from '../hooks/useSchedules';

// ============================================================================
// Types
// ============================================================================

type ConnectionStatus = 'connected' | 'connecting' | 'disconnected';

// ============================================================================
// Styles
// ============================================================================

const dashboardGridStyles: CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(4, 1fr)',
  gap: 'var(--spacing-lg)',
  marginBottom: 'var(--spacing-xl)',
};

const mainContentRowStyles: CSSProperties = {
  display: 'grid',
  gridTemplateColumns: '2fr 1fr',
  gap: 'var(--spacing-lg)',
  marginBottom: 'var(--spacing-xl)',
};

const scheduleRowStyles: CSSProperties = {
  display: 'grid',
  gridTemplateColumns: '2fr 1fr',
  gap: 'var(--spacing-lg)',
};

const errorContainerStyles: CSSProperties = {
  backgroundColor: 'rgba(239, 68, 68, 0.1)',
  border: '1px solid var(--accent-red)',
  borderRadius: 'var(--radius-lg)',
  padding: 'var(--spacing-lg)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  marginBottom: 'var(--spacing-lg)',
};

const errorTextStyles: CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 'var(--spacing-sm)',
  color: 'var(--accent-red)',
};

const retryButtonStyles: CSSProperties = {
  padding: 'var(--spacing-sm) var(--spacing-md)',
  backgroundColor: 'transparent',
  border: '1px solid var(--accent-red)',
  borderRadius: 'var(--radius-md)',
  color: 'var(--accent-red)',
  cursor: 'pointer',
  fontSize: '0.875rem',
  fontWeight: 500,
  transition: 'all var(--transition-fast)',
};

const sectionCardStyles: CSSProperties = {
  backgroundColor: 'var(--bg-secondary)',
  border: '1px solid var(--border-subtle)',
  borderRadius: 'var(--radius-lg)',
  overflow: 'hidden',
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
};

const sectionHeaderStyles: CSSProperties = {
  padding: 'var(--spacing-md) var(--spacing-lg)',
  borderBottom: '1px solid var(--border-subtle)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
};

const sectionTitleStyles: CSSProperties = {
  margin: 0,
  fontSize: '1rem',
  fontWeight: 600,
  color: 'var(--text-primary)',
};

const sectionSubtitleStyles: CSSProperties = {
  fontSize: '0.75rem',
  color: 'var(--text-muted)',
  marginTop: 2,
};

const sectionContentStyles: CSSProperties = {
  flex: 1,
  padding: 'var(--spacing-md)',
  overflow: 'hidden',
};

// ============================================================================
// KPI Skeleton Component
// ============================================================================

function KPISkeleton() {
  const skeletonCardStyles: CSSProperties = {
    backgroundColor: 'var(--bg-secondary)',
    border: '1px solid var(--border-subtle)',
    borderRadius: 'var(--radius-lg)',
    padding: 'var(--spacing-lg)',
    position: 'relative',
  };

  return (
    <div style={skeletonCardStyles}>
      <Skeleton variant="text" width="60%" height={12} style={{ marginBottom: 'var(--spacing-sm)' }} />
      <Skeleton variant="text" width="40%" height={40} style={{ marginBottom: 'var(--spacing-sm)' }} />
      <Skeleton variant="text" width="30%" height={12} />
    </div>
  );
}

// ============================================================================
// Robot Grid Skeleton Component
// ============================================================================

function RobotGridSkeleton() {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--spacing-md)' }}>
      {Array.from({ length: 6 }).map((_, i) => (
        <SkeletonCard key={i} lines={3} />
      ))}
    </div>
  );
}

// ============================================================================
// Activity Feed Skeleton Component
// ============================================================================

function ActivityFeedSkeleton() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-sm)',
            padding: 'var(--spacing-sm)',
          }}
        >
          <Skeleton variant="circular" width={32} height={32} />
          <div style={{ flex: 1 }}>
            <Skeleton variant="text" width="70%" height={14} style={{ marginBottom: 4 }} />
            <Skeleton variant="text" width="40%" height={12} />
          </div>
        </div>
      ))}
    </div>
  );
}

// ============================================================================
// Error Banner Component
// ============================================================================

interface ErrorBannerProps {
  message: string;
  onRetry: () => void;
}

function ErrorBanner({ message, onRetry }: ErrorBannerProps) {
  return (
    <motion.div
      style={errorContainerStyles}
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
    >
      <span style={errorTextStyles}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        {message}
      </span>
      <button
        style={retryButtonStyles}
        onClick={onRetry}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = 'transparent';
        }}
      >
        Retry
      </button>
    </motion.div>
  );
}

// ============================================================================
// Main Dashboard Component
// ============================================================================

export function Dashboard() {
  const navigate = useNavigate();

  // WebSocket connection
  const { isConnected, reconnect } = useWebSocketManager();

  // Critical metrics (KPIs)
  const {
    totalRobots,
    activeJobs,
    successRate,
    queueDepth,
    isLoading: metricsLoading,
    isError: metricsError,
    refresh: refreshMetrics,
  } = useCriticalMetrics();

  // Robot data
  const {
    data: robots = [],
    isLoading: robotsLoading,
    isError: robotsError,
    refetch: refetchRobots,
  } = useRobots();

  // Schedule data
  const {
    data: schedules = [],
    isLoading: schedulesLoading,
    isError: schedulesError,
    refetch: refetchSchedules,
  } = useSchedules();

  // Activity events from Zustand store
  const activityEvents = useMetricsStore(selectActivityEvents);

  // Connection status for header
  const connectionStatus: ConnectionStatus = useMemo(() => {
    if (isConnected) return 'connected';
    if (metricsLoading || robotsLoading) return 'connecting';
    return 'disconnected';
  }, [isConnected, metricsLoading, robotsLoading]);

  // Error state
  const hasError = metricsError || robotsError || schedulesError;
  const errorMessage = useMemo(() => {
    if (metricsError) return 'Failed to load metrics. Check your connection.';
    if (robotsError) return 'Failed to load robot data. Check your connection.';
    if (schedulesError) return 'Failed to load schedules. Check your connection.';
    return '';
  }, [metricsError, robotsError, schedulesError]);

  // Handlers
  const handleRetry = useCallback(() => {
    refreshMetrics();
    refetchRobots();
    refetchSchedules();
    reconnect();
  }, [refreshMetrics, refetchRobots, refetchSchedules, reconnect]);

  const handleRobotClick = useCallback((robot: RobotSummary) => {
    navigate(`/fleet/${robot.robot_id}`);
  }, [navigate]);

  const handleActivityClick = useCallback((event: ActivityEvent) => {
    if (event.jobId) {
      navigate(`/jobs/${event.jobId}`);
    } else if (event.robotId) {
      navigate(`/fleet/${event.robotId}`);
    }
  }, [navigate]);

  const handleScheduleClick = useCallback((schedule: Schedule) => {
    navigate(`/schedules/${schedule.schedule_id}`);
  }, [navigate]);

  // KPI icons
  const robotIcon = (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="8" width="18" height="12" rx="2" />
      <path d="M7 8V6a2 2 0 012-2h6a2 2 0 012 2v2" />
      <circle cx="9" cy="13" r="1" fill="currentColor" />
      <circle cx="15" cy="13" r="1" fill="currentColor" />
    </svg>
  );

  const jobIcon = (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
  );

  const successIcon = (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  );

  const queueIcon = (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="8" y1="6" x2="21" y2="6" />
      <line x1="8" y1="12" x2="21" y2="12" />
      <line x1="8" y1="18" x2="21" y2="18" />
      <line x1="3" y1="6" x2="3.01" y2="6" />
      <line x1="3" y1="12" x2="3.01" y2="12" />
      <line x1="3" y1="18" x2="3.01" y2="18" />
    </svg>
  );

  return (
    <DashboardLayout
      pageTitle="Dashboard"
      pageSubtitle="Real-time RPA monitoring overview"
      connectionStatus={connectionStatus}
    >
      {/* Error Banner */}
      <AnimatePresence>
        {hasError && (
          <ErrorBanner message={errorMessage} onRetry={handleRetry} />
        )}
      </AnimatePresence>

      {/* KPI Row */}
      <div style={dashboardGridStyles}>
        {metricsLoading ? (
          <>
            <KPISkeleton />
            <KPISkeleton />
            <KPISkeleton />
            <KPISkeleton />
          </>
        ) : (
          <>
            <KPICard
              title="Total Robots"
              value={totalRobots}
              icon={robotIcon}
              accentColor="var(--accent-blue)"
              isLive={isConnected}
            />
            <KPICard
              title="Active Jobs"
              value={activeJobs}
              icon={jobIcon}
              accentColor="var(--accent-orange)"
              isLive={isConnected}
            />
            <KPICard
              title="Success Rate"
              value={successRate}
              format="percentage"
              icon={successIcon}
              accentColor={successRate >= 95 ? 'var(--accent-green)' : successRate >= 80 ? 'var(--accent-yellow)' : 'var(--accent-red)'}
              isLive={isConnected}
            />
            <KPICard
              title="Queue Depth"
              value={queueDepth}
              icon={queueIcon}
              accentColor={queueDepth > 50 ? 'var(--accent-red)' : queueDepth > 20 ? 'var(--accent-yellow)' : 'var(--accent-cyan)'}
              isLive={isConnected}
            />
          </>
        )}
      </div>

      {/* Robot Fleet + Activity Feed Row */}
      <div style={mainContentRowStyles}>
        {/* Robot Fleet Grid */}
        <div style={sectionCardStyles}>
          <div style={sectionHeaderStyles}>
            <div>
              <h3 style={sectionTitleStyles}>Robot Fleet</h3>
              <p style={sectionSubtitleStyles}>
                {robotsLoading ? 'Loading...' : `${robots.length} robots registered`}
              </p>
            </div>
            <button
              onClick={() => navigate('/fleet')}
              style={{
                padding: 'var(--spacing-xs) var(--spacing-sm)',
                backgroundColor: 'transparent',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
                fontSize: '0.75rem',
                fontWeight: 500,
                transition: 'all var(--transition-fast)',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--accent-primary)';
                e.currentTarget.style.color = 'var(--accent-primary)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border-default)';
                e.currentTarget.style.color = 'var(--text-secondary)';
              }}
            >
              View All
            </button>
          </div>
          <div style={sectionContentStyles}>
            {robotsLoading ? (
              <RobotGridSkeleton />
            ) : robots.length === 0 ? (
              <EmptyState
                title="No robots connected"
                description="Robots will appear here once they connect to the orchestrator"
                icon={robotIcon}
              />
            ) : (
              <RobotGrid
                robots={robots}
                onRobotClick={handleRobotClick}
                columnCount={3}
              />
            )}
          </div>
        </div>

        {/* Activity Feed */}
        <div style={sectionCardStyles}>
          <div style={sectionHeaderStyles}>
            <div>
              <h3 style={sectionTitleStyles}>Activity Feed</h3>
              <p style={sectionSubtitleStyles}>
                {activityEvents.length > 0 ? `${activityEvents.length} recent events` : 'No recent activity'}
              </p>
            </div>
            {isConnected && (
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 'var(--spacing-xs)',
                  fontSize: '0.625rem',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  color: 'var(--accent-green)',
                }}
              >
                <motion.span
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: '50%',
                    backgroundColor: 'var(--accent-green)',
                  }}
                  animate={{ opacity: [1, 0.4, 1] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                />
                Live
              </span>
            )}
          </div>
          <div style={{ ...sectionContentStyles, padding: 'var(--spacing-sm)' }}>
            {metricsLoading ? (
              <ActivityFeedSkeleton />
            ) : (
              <ActivityFeed
                events={activityEvents}
                onEventClick={handleActivityClick}
                maxVisible={15}
              />
            )}
          </div>
        </div>
      </div>

      {/* Schedule Calendar + Upcoming Runs Row */}
      <div style={scheduleRowStyles}>
        {/* Schedule Calendar */}
        <div style={sectionCardStyles}>
          <div style={sectionHeaderStyles}>
            <div>
              <h3 style={sectionTitleStyles}>Schedule Calendar</h3>
              <p style={sectionSubtitleStyles}>
                {schedulesLoading
                  ? 'Loading...'
                  : `${schedules.filter((s) => s.enabled).length} active schedules`}
              </p>
            </div>
            <button
              onClick={() => navigate('/schedules')}
              style={{
                padding: 'var(--spacing-xs) var(--spacing-sm)',
                backgroundColor: 'transparent',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
                fontSize: '0.75rem',
                fontWeight: 500,
                transition: 'all var(--transition-fast)',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--accent-primary)';
                e.currentTarget.style.color = 'var(--accent-primary)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border-default)';
                e.currentTarget.style.color = 'var(--text-secondary)';
              }}
            >
              Manage Schedules
            </button>
          </div>
          <div style={{ ...sectionContentStyles, padding: 0 }}>
            {schedulesLoading ? (
              <div style={{ padding: 'var(--spacing-lg)' }}>
                <Skeleton variant="rectangular" height={400} />
              </div>
            ) : (
              <ScheduleCalendar
                schedules={schedules}
                onScheduleClick={handleScheduleClick}
              />
            )}
          </div>
        </div>

        {/* Upcoming Runs */}
        <div style={{ height: '100%' }}>
          {schedulesLoading ? (
            <div style={sectionCardStyles}>
              <div style={sectionHeaderStyles}>
                <div>
                  <Skeleton variant="text" width={120} height={16} />
                  <Skeleton variant="text" width={80} height={12} style={{ marginTop: 4 }} />
                </div>
              </div>
              <div style={sectionContentStyles}>
                {Array.from({ length: 5 }).map((_, i) => (
                  <div
                    key={i}
                    style={{
                      padding: 'var(--spacing-sm)',
                      marginBottom: 'var(--spacing-sm)',
                    }}
                  >
                    <Skeleton variant="text" width="70%" height={14} style={{ marginBottom: 4 }} />
                    <Skeleton variant="text" width="50%" height={12} />
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <UpcomingRuns
              schedules={schedules}
              onScheduleClick={handleScheduleClick}
              limit={5}
            />
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}

export default Dashboard;

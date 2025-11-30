/**
 * Hook for critical metrics with WebSocket + REST polling fallback.
 *
 * Combines real-time WebSocket data with REST polling (1-second interval)
 * for critical dashboard metrics with automatic fallback.
 */

import { useMemo, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import {
  useMetricsStore,
  selectFleetMetrics,
  selectQueueDepth,
  type FleetMetrics,
} from '@/store/metricsStore';

// ============================================================================
// Configuration
// ============================================================================

const CRITICAL_METRICS_POLL_INTERVAL_MS = 1000; // 1 second for critical metrics
const STALE_TIME_MS = 500; // Consider data stale after 500ms

// Query keys
const QUERY_KEYS = {
  fleetMetrics: ['fleet', 'metrics', 'critical'] as const,
  analytics: ['analytics', 'summary', 'critical'] as const,
};

// ============================================================================
// Types
// ============================================================================

interface CriticalMetrics {
  totalRobots: number;
  activeRobots: number;
  idleRobots: number;
  offlineRobots: number;
  activeJobs: number;
  queueDepth: number;
  successRate: number;
  totalJobsToday: number;
  averageJobDurationSeconds: number;
  isLoading: boolean;
  isError: boolean;
  lastUpdated: string | null;
  refresh: () => void;
}

interface AnalyticsSummary {
  success_rate: number;
  failure_rate: number;
  p50_duration_ms: number;
  p90_duration_ms: number;
  p99_duration_ms: number;
}

// ============================================================================
// REST API Fetchers
// ============================================================================

async function fetchFleetMetrics(): Promise<FleetMetrics> {
  const { data } = await apiClient.get<FleetMetrics>('/api/v1/metrics/fleet');
  return data;
}

async function fetchAnalyticsSummary(): Promise<AnalyticsSummary> {
  const { data } = await apiClient.get<AnalyticsSummary>('/api/v1/analytics/summary');
  return data;
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useCriticalMetrics(): CriticalMetrics {
  const queryClient = useQueryClient();

  // Get real-time data from Zustand store (updated via WebSocket)
  const wsFleetMetrics = useMetricsStore(selectFleetMetrics);
  const wsQueueDepth = useMetricsStore(selectQueueDepth);
  const wsLastUpdated = useMetricsStore((state) => state.lastUpdated);
  const robotStatuses = useMetricsStore((state) => state.robotStatuses);

  // REST polling for fleet metrics (fallback)
  const {
    data: restFleetMetrics,
    isLoading: isFleetLoading,
    isError: isFleetError,
  } = useQuery<FleetMetrics>({
    queryKey: QUERY_KEYS.fleetMetrics,
    queryFn: fetchFleetMetrics,
    refetchInterval: CRITICAL_METRICS_POLL_INTERVAL_MS,
    staleTime: STALE_TIME_MS,
  });

  // REST polling for analytics (for success rate)
  const {
    data: analyticsData,
    isLoading: isAnalyticsLoading,
    isError: isAnalyticsError,
  } = useQuery<AnalyticsSummary>({
    queryKey: QUERY_KEYS.analytics,
    queryFn: fetchAnalyticsSummary,
    refetchInterval: CRITICAL_METRICS_POLL_INTERVAL_MS * 5, // 5 seconds for analytics
    staleTime: STALE_TIME_MS * 5,
  });

  // Calculate robot counts from WebSocket robot statuses
  const wsRobotCounts = useMemo(() => {
    let active = 0;
    let idle = 0;
    let offline = 0;
    let busy = 0;

    Object.values(robotStatuses).forEach((robot) => {
      switch (robot.status) {
        case 'busy':
          busy++;
          active++;
          break;
        case 'idle':
          idle++;
          active++;
          break;
        case 'offline':
        case 'failed':
          offline++;
          break;
      }
    });

    return {
      total: Object.keys(robotStatuses).length,
      active,
      idle,
      offline,
      busy,
    };
  }, [robotStatuses]);

  // Merge WebSocket data with REST fallback
  const mergedMetrics = useMemo((): Omit<CriticalMetrics, 'isLoading' | 'isError' | 'lastUpdated' | 'refresh'> => {
    // Prefer WebSocket data if available and fresh
    const hasWsData = wsFleetMetrics !== null;
    const hasRestData = restFleetMetrics !== undefined;

    // Use WebSocket robot counts if we have real-time status data
    const hasWsRobotStatuses = Object.keys(robotStatuses).length > 0;

    // Total robots: prefer REST (more authoritative) or WS
    const totalRobots = hasRestData
      ? restFleetMetrics.total_robots
      : hasWsData
        ? wsFleetMetrics.total_robots
        : 0;

    // Active/idle robots: prefer WS real-time counts if available
    const activeRobots = hasWsRobotStatuses
      ? wsRobotCounts.active
      : hasWsData
        ? wsFleetMetrics.active_robots
        : hasRestData
          ? restFleetMetrics.active_robots
          : 0;

    const idleRobots = hasWsRobotStatuses
      ? wsRobotCounts.idle
      : hasWsData
        ? wsFleetMetrics.idle_robots
        : hasRestData
          ? restFleetMetrics.idle_robots
          : 0;

    // Offline robots: calculate from total and active
    const offlineRobots = hasWsRobotStatuses
      ? wsRobotCounts.offline
      : totalRobots - activeRobots;

    // Active jobs: prefer WS for real-time, fall back to REST
    const activeJobs = hasWsData
      ? wsFleetMetrics.active_jobs
      : hasRestData
        ? restFleetMetrics.active_jobs
        : 0;

    // Queue depth: prefer WS for most real-time value
    const queueDepth = wsQueueDepth > 0
      ? wsQueueDepth
      : hasWsData
        ? wsFleetMetrics.queue_depth
        : hasRestData
          ? restFleetMetrics.queue_depth
          : 0;

    // Total jobs today: prefer REST (accumulated value)
    const totalJobsToday = hasRestData
      ? restFleetMetrics.total_jobs_today
      : hasWsData
        ? wsFleetMetrics.total_jobs_today
        : 0;

    // Average job duration: prefer REST
    const averageJobDurationSeconds = hasRestData
      ? restFleetMetrics.average_job_duration_seconds
      : hasWsData
        ? wsFleetMetrics.average_job_duration_seconds
        : 0;

    // Success rate: from analytics endpoint
    const successRate = analyticsData?.success_rate ?? 0;

    return {
      totalRobots,
      activeRobots,
      idleRobots,
      offlineRobots,
      activeJobs,
      queueDepth,
      successRate,
      totalJobsToday,
      averageJobDurationSeconds,
    };
  }, [
    wsFleetMetrics,
    wsQueueDepth,
    restFleetMetrics,
    analyticsData,
    robotStatuses,
    wsRobotCounts,
  ]);

  // Manual refresh function
  const refresh = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: QUERY_KEYS.fleetMetrics });
    queryClient.invalidateQueries({ queryKey: QUERY_KEYS.analytics });
  }, [queryClient]);

  // Determine last updated timestamp
  const lastUpdated = useMemo(() => {
    if (wsLastUpdated) {
      return wsLastUpdated;
    }
    return new Date().toISOString();
  }, [wsLastUpdated]);

  return {
    ...mergedMetrics,
    isLoading: isFleetLoading || isAnalyticsLoading,
    isError: isFleetError || isAnalyticsError,
    lastUpdated,
    refresh,
  };
}

// ============================================================================
// Additional Hooks for Specific Use Cases
// ============================================================================

/**
 * Hook for just the robot counts (lighter weight).
 */
export function useRobotCounts() {
  const robotStatuses = useMetricsStore((state) => state.robotStatuses);

  return useMemo(() => {
    let active = 0;
    let idle = 0;
    let offline = 0;
    let failed = 0;

    Object.values(robotStatuses).forEach((robot) => {
      switch (robot.status) {
        case 'busy':
          active++;
          break;
        case 'idle':
          idle++;
          break;
        case 'offline':
          offline++;
          break;
        case 'failed':
          failed++;
          break;
      }
    });

    return {
      total: Object.keys(robotStatuses).length,
      active,
      idle,
      offline,
      failed,
      online: active + idle,
    };
  }, [robotStatuses]);
}

/**
 * Hook for queue metrics only.
 */
export function useQueueMetrics() {
  const queueDepth = useMetricsStore(selectQueueDepth);
  const fleetMetrics = useMetricsStore(selectFleetMetrics);

  const { data: restMetrics, isLoading } = useQuery<FleetMetrics>({
    queryKey: ['queue', 'metrics'],
    queryFn: fetchFleetMetrics,
    refetchInterval: CRITICAL_METRICS_POLL_INTERVAL_MS,
    staleTime: STALE_TIME_MS,
  });

  return useMemo(() => ({
    queueDepth: queueDepth > 0 ? queueDepth : (restMetrics?.queue_depth ?? 0),
    activeJobs: fleetMetrics?.active_jobs ?? restMetrics?.active_jobs ?? 0,
    isLoading,
  }), [queueDepth, fleetMetrics, restMetrics, isLoading]);
}

/**
 * Hook for job success/failure metrics.
 */
export function useJobSuccessMetrics() {
  const { data: analytics, isLoading, isError } = useQuery<AnalyticsSummary>({
    queryKey: QUERY_KEYS.analytics,
    queryFn: fetchAnalyticsSummary,
    refetchInterval: CRITICAL_METRICS_POLL_INTERVAL_MS * 5,
    staleTime: STALE_TIME_MS * 5,
  });

  return useMemo(() => ({
    successRate: analytics?.success_rate ?? 0,
    failureRate: analytics?.failure_rate ?? 0,
    p50DurationMs: analytics?.p50_duration_ms ?? 0,
    p90DurationMs: analytics?.p90_duration_ms ?? 0,
    p99DurationMs: analytics?.p99_duration_ms ?? 0,
    isLoading,
    isError,
  }), [analytics, isLoading, isError]);
}

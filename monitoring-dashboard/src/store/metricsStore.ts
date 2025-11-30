/**
 * Zustand store for real-time metrics state management.
 *
 * Manages fleet metrics, robot statuses, queue depth, and activity events
 * with immer middleware for immutable updates.
 */

import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';

// ============================================================================
// Types
// ============================================================================

export interface FleetMetrics {
  total_robots: number;
  active_robots: number;
  idle_robots: number;
  total_jobs_today: number;
  active_jobs: number;
  queue_depth: number;
  average_job_duration_seconds: number;
}

export interface RobotStatus {
  robot_id: string;
  status: 'idle' | 'busy' | 'offline' | 'failed';
  cpu_percent: number;
  memory_mb: number;
  current_job_id: string | null;
  timestamp: string;
}

export interface ActivityEvent {
  id: string;
  type: 'job_started' | 'job_completed' | 'job_failed' | 'robot_online' | 'robot_offline' | 'schedule_triggered';
  timestamp: string;
  title: string;
  details?: string;
  robotId?: string;
  jobId?: string;
}

// ============================================================================
// Store State and Actions
// ============================================================================

interface MetricsState {
  fleetMetrics: FleetMetrics | null;
  robotStatuses: Record<string, RobotStatus>;
  queueDepth: number;
  activityEvents: ActivityEvent[];
  lastUpdated: string | null;
}

interface MetricsActions {
  updateFleetMetrics: (metrics: FleetMetrics) => void;
  updateRobotStatus: (status: RobotStatus) => void;
  batchUpdateRobotStatuses: (statuses: RobotStatus[]) => void;
  addActivityEvent: (event: ActivityEvent) => void;
  setQueueDepth: (depth: number) => void;
  reset: () => void;
}

type MetricsStore = MetricsState & MetricsActions;

// Ring buffer max size for activity events
const MAX_ACTIVITY_EVENTS = 100;

// Initial state
const initialState: MetricsState = {
  fleetMetrics: null,
  robotStatuses: {},
  queueDepth: 0,
  activityEvents: [],
  lastUpdated: null,
};

// ============================================================================
// Store Implementation
// ============================================================================

export const useMetricsStore = create<MetricsStore>()(
  immer((set) => ({
    ...initialState,

    updateFleetMetrics: (metrics: FleetMetrics) => {
      set((state) => {
        state.fleetMetrics = metrics;
        state.queueDepth = metrics.queue_depth;
        state.lastUpdated = new Date().toISOString();
      });
    },

    updateRobotStatus: (status: RobotStatus) => {
      set((state) => {
        state.robotStatuses[status.robot_id] = status;
        state.lastUpdated = new Date().toISOString();
      });
    },

    batchUpdateRobotStatuses: (statuses: RobotStatus[]) => {
      set((state) => {
        for (const status of statuses) {
          state.robotStatuses[status.robot_id] = status;
        }
        state.lastUpdated = new Date().toISOString();
      });
    },

    addActivityEvent: (event: ActivityEvent) => {
      set((state) => {
        // Ring buffer: add new event and trim to max size
        state.activityEvents.unshift(event);
        if (state.activityEvents.length > MAX_ACTIVITY_EVENTS) {
          state.activityEvents = state.activityEvents.slice(0, MAX_ACTIVITY_EVENTS);
        }
        state.lastUpdated = new Date().toISOString();
      });
    },

    setQueueDepth: (depth: number) => {
      set((state) => {
        state.queueDepth = depth;
        state.lastUpdated = new Date().toISOString();
      });
    },

    reset: () => {
      set(() => ({
        ...initialState,
        robotStatuses: {},
        activityEvents: [],
      }));
    },
  }))
);

// ============================================================================
// Selectors (for optimized re-renders)
// ============================================================================

export const selectFleetMetrics = (state: MetricsStore) => state.fleetMetrics;
export const selectRobotStatuses = (state: MetricsStore) => state.robotStatuses;
export const selectQueueDepth = (state: MetricsStore) => state.queueDepth;
export const selectActivityEvents = (state: MetricsStore) => state.activityEvents;
export const selectLastUpdated = (state: MetricsStore) => state.lastUpdated;

// Derived selectors
export const selectActiveRobotCount = (state: MetricsStore): number => {
  return Object.values(state.robotStatuses).filter(
    (robot) => robot.status === 'busy' || robot.status === 'idle'
  ).length;
};

export const selectOfflineRobotCount = (state: MetricsStore): number => {
  return Object.values(state.robotStatuses).filter(
    (robot) => robot.status === 'offline'
  ).length;
};

export const selectRobotById = (robotId: string) => (state: MetricsStore): RobotStatus | undefined => {
  return state.robotStatuses[robotId];
};

export const selectRecentEvents = (count: number) => (state: MetricsStore): ActivityEvent[] => {
  return state.activityEvents.slice(0, count);
};

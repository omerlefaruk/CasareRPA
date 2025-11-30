import { describe, it, expect, beforeEach } from 'vitest';
import { useMetricsStore, type FleetMetrics, type RobotStatus, type ActivityEvent } from './metricsStore';

describe('metricsStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useMetricsStore.getState().reset();
  });

  describe('fleetMetrics', () => {
    it('should initialize with null fleetMetrics', () => {
      const state = useMetricsStore.getState();
      expect(state.fleetMetrics).toBeNull();
    });

    it('should update fleetMetrics', () => {
      const metrics: FleetMetrics = {
        total_robots: 10,
        active_robots: 5,
        idle_robots: 3,
        total_jobs_today: 100,
        active_jobs: 2,
        queue_depth: 5,
        average_job_duration_seconds: 45.5,
      };

      useMetricsStore.getState().updateFleetMetrics(metrics);

      const state = useMetricsStore.getState();
      expect(state.fleetMetrics).toEqual(metrics);
      expect(state.queueDepth).toBe(5);
      expect(state.lastUpdated).toBeTruthy();
    });
  });

  describe('robotStatuses', () => {
    it('should initialize with empty robotStatuses', () => {
      const state = useMetricsStore.getState();
      expect(state.robotStatuses).toEqual({});
    });

    it('should update a single robot status', () => {
      const robot: RobotStatus = {
        robot_id: 'robot-1',
        status: 'busy',
        cpu_percent: 45.5,
        memory_mb: 1024,
        current_job_id: 'job-123',
        timestamp: new Date().toISOString(),
      };

      useMetricsStore.getState().updateRobotStatus(robot);

      const state = useMetricsStore.getState();
      expect(state.robotStatuses['robot-1']).toEqual(robot);
    });

    it('should batch update robot statuses', () => {
      const robots: RobotStatus[] = [
        {
          robot_id: 'robot-1',
          status: 'busy',
          cpu_percent: 45.5,
          memory_mb: 1024,
          current_job_id: 'job-1',
          timestamp: new Date().toISOString(),
        },
        {
          robot_id: 'robot-2',
          status: 'idle',
          cpu_percent: 10.0,
          memory_mb: 512,
          current_job_id: null,
          timestamp: new Date().toISOString(),
        },
      ];

      useMetricsStore.getState().batchUpdateRobotStatuses(robots);

      const state = useMetricsStore.getState();
      expect(Object.keys(state.robotStatuses)).toHaveLength(2);
      expect(state.robotStatuses['robot-1'].status).toBe('busy');
      expect(state.robotStatuses['robot-2'].status).toBe('idle');
    });

    it('should overwrite existing robot status on update', () => {
      const robot1: RobotStatus = {
        robot_id: 'robot-1',
        status: 'idle',
        cpu_percent: 10.0,
        memory_mb: 512,
        current_job_id: null,
        timestamp: new Date().toISOString(),
      };

      const robot1Updated: RobotStatus = {
        robot_id: 'robot-1',
        status: 'busy',
        cpu_percent: 75.0,
        memory_mb: 2048,
        current_job_id: 'job-456',
        timestamp: new Date().toISOString(),
      };

      useMetricsStore.getState().updateRobotStatus(robot1);
      useMetricsStore.getState().updateRobotStatus(robot1Updated);

      const state = useMetricsStore.getState();
      expect(state.robotStatuses['robot-1'].status).toBe('busy');
      expect(state.robotStatuses['robot-1'].cpu_percent).toBe(75.0);
    });
  });

  describe('activityEvents (ring buffer)', () => {
    it('should initialize with empty activityEvents', () => {
      const state = useMetricsStore.getState();
      expect(state.activityEvents).toEqual([]);
    });

    it('should add activity event to the front', () => {
      const event: ActivityEvent = {
        id: 'event-1',
        type: 'job_started',
        timestamp: new Date().toISOString(),
        title: 'Job Started',
        details: 'Test job',
        jobId: 'job-1',
      };

      useMetricsStore.getState().addActivityEvent(event);

      const state = useMetricsStore.getState();
      expect(state.activityEvents).toHaveLength(1);
      expect(state.activityEvents[0]).toEqual(event);
    });

    it('should prepend new events (most recent first)', () => {
      const event1: ActivityEvent = {
        id: 'event-1',
        type: 'job_started',
        timestamp: '2024-01-01T00:00:00Z',
        title: 'First Event',
      };
      const event2: ActivityEvent = {
        id: 'event-2',
        type: 'job_completed',
        timestamp: '2024-01-01T00:01:00Z',
        title: 'Second Event',
      };

      useMetricsStore.getState().addActivityEvent(event1);
      useMetricsStore.getState().addActivityEvent(event2);

      const state = useMetricsStore.getState();
      expect(state.activityEvents[0].id).toBe('event-2');
      expect(state.activityEvents[1].id).toBe('event-1');
    });

    it('should limit events to MAX_ACTIVITY_EVENTS (100)', () => {
      // Add 105 events
      for (let i = 0; i < 105; i++) {
        const event: ActivityEvent = {
          id: `event-${i}`,
          type: 'job_started',
          timestamp: new Date().toISOString(),
          title: `Event ${i}`,
        };
        useMetricsStore.getState().addActivityEvent(event);
      }

      const state = useMetricsStore.getState();
      expect(state.activityEvents).toHaveLength(100);
      // Most recent should be event-104 (last added)
      expect(state.activityEvents[0].id).toBe('event-104');
      // Oldest should be event-5 (first 5 were dropped)
      expect(state.activityEvents[99].id).toBe('event-5');
    });
  });

  describe('queueDepth', () => {
    it('should initialize queueDepth to 0', () => {
      const state = useMetricsStore.getState();
      expect(state.queueDepth).toBe(0);
    });

    it('should set queueDepth', () => {
      useMetricsStore.getState().setQueueDepth(42);

      const state = useMetricsStore.getState();
      expect(state.queueDepth).toBe(42);
    });
  });

  describe('reset', () => {
    it('should reset store to initial state', () => {
      // Add some data
      useMetricsStore.getState().updateFleetMetrics({
        total_robots: 10,
        active_robots: 5,
        idle_robots: 3,
        total_jobs_today: 100,
        active_jobs: 2,
        queue_depth: 5,
        average_job_duration_seconds: 45.5,
      });
      useMetricsStore.getState().updateRobotStatus({
        robot_id: 'robot-1',
        status: 'busy',
        cpu_percent: 45.5,
        memory_mb: 1024,
        current_job_id: 'job-1',
        timestamp: new Date().toISOString(),
      });
      useMetricsStore.getState().addActivityEvent({
        id: 'event-1',
        type: 'job_started',
        timestamp: new Date().toISOString(),
        title: 'Test',
      });
      useMetricsStore.getState().setQueueDepth(10);

      // Reset
      useMetricsStore.getState().reset();

      const state = useMetricsStore.getState();
      expect(state.fleetMetrics).toBeNull();
      expect(state.robotStatuses).toEqual({});
      expect(state.activityEvents).toEqual([]);
      expect(state.queueDepth).toBe(0);
      expect(state.lastUpdated).toBeNull();
    });
  });
});

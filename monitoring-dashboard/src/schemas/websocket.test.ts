import { describe, it, expect } from 'vitest';
import {
  RobotStatusSchema,
  FleetMetricsSchema,
  RobotBatchSchema,
  QueueDepthSchema,
  RobotEventSchema,
  ScheduleEventSchema,
  JobEventSchema,
  safeParseMessage,
} from './websocket';

describe('websocket schemas', () => {
  describe('RobotStatusSchema', () => {
    it('should validate a valid robot status', () => {
      const validStatus = {
        robot_id: 'robot-1',
        status: 'busy',
        cpu_percent: 45.5,
        memory_mb: 1024,
        current_job_id: 'job-123',
        timestamp: '2024-01-01T00:00:00Z',
      };

      const result = RobotStatusSchema.safeParse(validStatus);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.robot_id).toBe('robot-1');
        expect(result.data.status).toBe('busy');
      }
    });

    it('should allow null current_job_id', () => {
      const validStatus = {
        robot_id: 'robot-1',
        status: 'idle',
        cpu_percent: 10,
        memory_mb: 512,
        current_job_id: null,
        timestamp: '2024-01-01T00:00:00Z',
      };

      const result = RobotStatusSchema.safeParse(validStatus);
      expect(result.success).toBe(true);
    });

    it('should reject invalid status values', () => {
      const invalidStatus = {
        robot_id: 'robot-1',
        status: 'invalid_status',
        cpu_percent: 45.5,
        memory_mb: 1024,
        current_job_id: null,
        timestamp: '2024-01-01T00:00:00Z',
      };

      const result = RobotStatusSchema.safeParse(invalidStatus);
      expect(result.success).toBe(false);
    });

    it('should reject cpu_percent outside 0-100 range', () => {
      const invalidStatus = {
        robot_id: 'robot-1',
        status: 'busy',
        cpu_percent: 150,
        memory_mb: 1024,
        current_job_id: null,
        timestamp: '2024-01-01T00:00:00Z',
      };

      const result = RobotStatusSchema.safeParse(invalidStatus);
      expect(result.success).toBe(false);
    });

    it('should reject negative memory_mb', () => {
      const invalidStatus = {
        robot_id: 'robot-1',
        status: 'busy',
        cpu_percent: 50,
        memory_mb: -100,
        current_job_id: null,
        timestamp: '2024-01-01T00:00:00Z',
      };

      const result = RobotStatusSchema.safeParse(invalidStatus);
      expect(result.success).toBe(false);
    });
  });

  describe('FleetMetricsSchema', () => {
    it('should validate valid fleet metrics', () => {
      const validMetrics = {
        total_robots: 10,
        active_robots: 5,
        idle_robots: 3,
        total_jobs_today: 100,
        active_jobs: 2,
        queue_depth: 5,
        average_job_duration_seconds: 45.5,
      };

      const result = FleetMetricsSchema.safeParse(validMetrics);
      expect(result.success).toBe(true);
    });

    it('should reject non-integer robot counts', () => {
      const invalidMetrics = {
        total_robots: 10.5,
        active_robots: 5,
        idle_robots: 3,
        total_jobs_today: 100,
        active_jobs: 2,
        queue_depth: 5,
        average_job_duration_seconds: 45.5,
      };

      const result = FleetMetricsSchema.safeParse(invalidMetrics);
      expect(result.success).toBe(false);
    });

    it('should reject negative values', () => {
      const invalidMetrics = {
        total_robots: -1,
        active_robots: 5,
        idle_robots: 3,
        total_jobs_today: 100,
        active_jobs: 2,
        queue_depth: 5,
        average_job_duration_seconds: 45.5,
      };

      const result = FleetMetricsSchema.safeParse(invalidMetrics);
      expect(result.success).toBe(false);
    });
  });

  describe('RobotBatchSchema', () => {
    it('should validate a batch of robots', () => {
      const validBatch = {
        robots: [
          {
            robot_id: 'robot-1',
            status: 'busy',
            cpu_percent: 45.5,
            memory_mb: 1024,
            current_job_id: 'job-1',
            timestamp: '2024-01-01T00:00:00Z',
          },
          {
            robot_id: 'robot-2',
            status: 'idle',
            cpu_percent: 10,
            memory_mb: 512,
            current_job_id: null,
            timestamp: '2024-01-01T00:00:00Z',
          },
        ],
      };

      const result = RobotBatchSchema.safeParse(validBatch);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.robots).toHaveLength(2);
      }
    });

    it('should allow empty robots array', () => {
      const validBatch = { robots: [] };

      const result = RobotBatchSchema.safeParse(validBatch);
      expect(result.success).toBe(true);
    });
  });

  describe('QueueDepthSchema', () => {
    it('should validate valid queue depth', () => {
      const valid = { queue_depth: 42 };

      const result = QueueDepthSchema.safeParse(valid);
      expect(result.success).toBe(true);
    });

    it('should reject negative queue depth', () => {
      const invalid = { queue_depth: -5 };

      const result = QueueDepthSchema.safeParse(invalid);
      expect(result.success).toBe(false);
    });
  });

  describe('RobotEventSchema', () => {
    it('should validate robot_online event', () => {
      const valid = {
        type: 'robot_online',
        robot_id: 'robot-1',
        timestamp: '2024-01-01T00:00:00Z',
      };

      const result = RobotEventSchema.safeParse(valid);
      expect(result.success).toBe(true);
    });

    it('should validate robot_offline event', () => {
      const valid = {
        type: 'robot_offline',
        robot_id: 'robot-1',
      };

      const result = RobotEventSchema.safeParse(valid);
      expect(result.success).toBe(true);
    });

    it('should reject invalid event types', () => {
      const invalid = {
        type: 'robot_exploded',
        robot_id: 'robot-1',
      };

      const result = RobotEventSchema.safeParse(invalid);
      expect(result.success).toBe(false);
    });
  });

  describe('ScheduleEventSchema', () => {
    it('should validate schedule_triggered event', () => {
      const valid = {
        type: 'schedule_triggered',
        schedule_name: 'Daily Backup',
        job_id: 'job-123',
        timestamp: '2024-01-01T00:00:00Z',
      };

      const result = ScheduleEventSchema.safeParse(valid);
      expect(result.success).toBe(true);
    });

    it('should allow optional fields to be missing', () => {
      const valid = {
        type: 'schedule_triggered',
      };

      const result = ScheduleEventSchema.safeParse(valid);
      expect(result.success).toBe(true);
    });
  });

  describe('JobEventSchema', () => {
    it('should validate job_started event', () => {
      const valid = {
        type: 'job_started',
        job_id: 'job-123',
        robot_id: 'robot-1',
        workflow_name: 'Test Workflow',
        timestamp: '2024-01-01T00:00:00Z',
      };

      const result = JobEventSchema.safeParse(valid);
      expect(result.success).toBe(true);
    });

    it('should validate job_completed event', () => {
      const valid = {
        type: 'job_completed',
        job_id: 'job-123',
      };

      const result = JobEventSchema.safeParse(valid);
      expect(result.success).toBe(true);
    });

    it('should validate job_failed event', () => {
      const valid = {
        type: 'job_failed',
        job_id: 'job-123',
        robot_id: 'robot-1',
      };

      const result = JobEventSchema.safeParse(valid);
      expect(result.success).toBe(true);
    });

    it('should reject invalid event types', () => {
      const invalid = {
        type: 'job_exploded',
        job_id: 'job-123',
      };

      const result = JobEventSchema.safeParse(invalid);
      expect(result.success).toBe(false);
    });
  });

  describe('safeParseMessage', () => {
    it('should return parsed data on success', () => {
      const data = {
        robot_id: 'robot-1',
        status: 'busy',
        cpu_percent: 50,
        memory_mb: 1024,
        current_job_id: null,
        timestamp: '2024-01-01T00:00:00Z',
      };

      const result = safeParseMessage(RobotStatusSchema, data);
      expect(result).toBeDefined();
      expect(result?.robot_id).toBe('robot-1');
    });

    it('should return undefined on validation failure', () => {
      const invalidData = {
        robot_id: 'robot-1',
        status: 'invalid',
        cpu_percent: 50,
        memory_mb: 1024,
        current_job_id: null,
        timestamp: '2024-01-01T00:00:00Z',
      };

      const result = safeParseMessage(RobotStatusSchema, invalidData);
      expect(result).toBeUndefined();
    });

    it('should return undefined for null input', () => {
      const result = safeParseMessage(RobotStatusSchema, null);
      expect(result).toBeUndefined();
    });

    it('should return undefined for undefined input', () => {
      const result = safeParseMessage(RobotStatusSchema, undefined);
      expect(result).toBeUndefined();
    });
  });
});

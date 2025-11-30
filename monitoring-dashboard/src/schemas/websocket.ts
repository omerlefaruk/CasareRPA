/**
 * Zod schemas for WebSocket message validation.
 * Provides runtime type safety for incoming WebSocket data.
 */

import { z } from 'zod';

// Robot status schema
export const RobotStatusSchema = z.object({
  robot_id: z.string(),
  status: z.enum(['idle', 'busy', 'offline', 'failed']),
  cpu_percent: z.number().min(0).max(100),
  memory_mb: z.number().min(0),
  current_job_id: z.string().nullable(),
  timestamp: z.string(),
});

export type RobotStatusMessage = z.infer<typeof RobotStatusSchema>;

// Fleet metrics schema
export const FleetMetricsSchema = z.object({
  total_robots: z.number().int().min(0),
  active_robots: z.number().int().min(0),
  idle_robots: z.number().int().min(0),
  total_jobs_today: z.number().int().min(0),
  active_jobs: z.number().int().min(0),
  queue_depth: z.number().int().min(0),
  average_job_duration_seconds: z.number().min(0),
});

export type FleetMetricsMessage = z.infer<typeof FleetMetricsSchema>;

// Robot batch message schema
export const RobotBatchSchema = z.object({
  robots: z.array(RobotStatusSchema),
});

// Queue depth update schema
export const QueueDepthSchema = z.object({
  queue_depth: z.number().int().min(0),
});

// Event type schemas
export const RobotEventSchema = z.object({
  type: z.enum(['robot_online', 'robot_offline']),
  robot_id: z.string(),
  timestamp: z.string().optional(),
});

export const ScheduleEventSchema = z.object({
  type: z.literal('schedule_triggered'),
  schedule_name: z.string().optional(),
  job_id: z.string().optional(),
  timestamp: z.string().optional(),
});

export const JobEventSchema = z.object({
  type: z.enum(['job_started', 'job_completed', 'job_failed']),
  job_id: z.string(),
  robot_id: z.string().optional(),
  workflow_name: z.string().optional(),
  timestamp: z.string().optional(),
});

/**
 * Safely parse a WebSocket message with a Zod schema.
 * Returns undefined if validation fails.
 */
export function safeParseMessage<T>(
  schema: z.ZodSchema<T>,
  data: unknown
): T | undefined {
  const result = schema.safeParse(data);
  if (result.success) {
    return result.data;
  }
  if (import.meta.env.DEV) {
    console.warn('[Schema] Validation failed:', result.error.issues);
  }
  return undefined;
}

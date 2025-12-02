/**
 * TypeScript type definitions for CasareRPA monitoring dashboard.
 *
 * Updated to match backend Python Pydantic models exactly.
 */

export interface FleetMetrics {
  total_robots: number;
  active_robots: number;
  idle_robots: number;
  total_jobs_today: number;
  active_jobs: number;
  queue_depth: number;
  average_job_duration_seconds: number;
}

export interface RobotCapabilities {
  platform: string;
  browser_engines: string[];
  desktop_automation: boolean;
  max_concurrent_jobs: number;
  cpu_cores: number;
  memory_gb: number;
  tags: string[];
}

export interface RobotSummary {
  robot_id: string;
  hostname: string;
  capabilities?: Record<string, any>;  // Optional - not all robots report capabilities yet
  status: 'idle' | 'busy' | 'offline' | 'failed';
  current_job_id: string | null;
  cpu_percent: number;
  memory_mb: number;
  last_heartbeat: string;  // Backend field name
  last_seen?: string;  // Deprecated - use last_heartbeat
}

export interface RobotMetrics {
  robot_id: string;
  hostname: string;
  status: string;
  current_job_id: string | null;
  cpu_percent: number;
  memory_percent: number;
  memory_mb: number;
  jobs_completed_today: number;
  jobs_failed_today: number;
  average_job_duration_seconds: number;
  last_heartbeat: string;  // Required field from backend
}

export interface JobSummary {
  job_id: string;
  workflow_id: string;
  workflow_name: string | null;  // Optional in backend
  robot_id: string | null;
  status: 'pending' | 'claimed' | 'completed' | 'failed';
  created_at: string;
  started_at?: string | null;  // Optional - not all jobs have started_at yet
  completed_at: string | null;
  duration_ms: number | null;
  variables?: Record<string, any>;  // Optional - not stored in all backends
  result?: Record<string, any> | null;  // Optional - not stored in all backends
}

export interface JobDetails {
  job: JobSummary;
  workflow_status: Record<string, any> | null;
  checkpoints: Record<string, any>[];
}

export interface AnalyticsSummary {
  throughput_trends: Array<{
    timestamp: string;
    jobs_per_hour: number;
  }>;
  success_rate: number;
  failure_rate: number;
  p50_duration_ms: number;
  p90_duration_ms: number;
  p99_duration_ms: number;
  error_distribution: Array<{
    error_type: string;
    count: number;
  }>;
  self_healing_success_rate: number | null;
  slowest_workflows: Array<{
    workflow_id: string;
    workflow_name: string;
    average_duration_ms: number;
  }>;
}

export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: string;
}

// Re-export MetricsSnapshot from client.ts for convenience
export type { MetricsSnapshot } from '@/api/client';

/**
 * Real-time metrics snapshot from WebSocket stream.
 * Includes fleet, job, system, and self-healing metrics.
 */
export interface MetricsSnapshotExtended {
  timestamp: string;
  environment: string;

  // Fleet metrics
  queue_depth: number;
  active_jobs: number;
  total_robots: number;
  busy_robots: number;
  idle_robots: number;
  fleet_utilization_percent: number;

  // Job metrics (aggregated)
  jobs_completed: number;
  jobs_failed: number;
  jobs_cancelled: number;
  job_success_rate: number;
  average_job_duration_seconds: number;
  average_queue_wait_seconds: number;

  // System metrics
  process_cpu_percent: number;
  process_memory_mb: number;
  system_cpu_percent: number;
  system_memory_percent: number;

  // Self-healing stats
  healing_attempts: number;
  healing_successes: number;
  healing_success_rate: number;

  // Top executed nodes
  top_nodes: NodeMetricsSummary[];
}

export interface NodeMetricsSummary {
  node_type: string;
  total_executions: number;
  success_rate: number;
  avg_duration_ms: number;
}

/**
 * TypeScript type definitions for CasareRPA monitoring dashboard.
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
  capabilities: Record<string, any>;
  status: 'idle' | 'busy' | 'offline' | 'failed';
  current_job_id: string | null;
  last_seen: string;
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
  last_heartbeat: string | null;
}

export interface JobSummary {
  job_id: string;
  workflow_id: string;
  workflow_name: string;
  robot_id: string | null;
  status: 'pending' | 'claimed' | 'completed' | 'failed';
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  variables: Record<string, any>;
  result: Record<string, any> | null;
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

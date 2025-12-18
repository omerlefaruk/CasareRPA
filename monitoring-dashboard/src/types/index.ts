// Robot types
export interface Robot {
  robot_id: string
  name: string
  hostname: string
  status: RobotStatus
  environment: string
  max_concurrent_jobs: number
  capabilities: string[]
  tags: string[]
  current_job_ids: string[]
  last_seen: string | null
  last_heartbeat: string | null
  created_at: string | null
  metrics: Record<string, unknown>
}

export type RobotStatus = 'offline' | 'idle' | 'online' | 'busy' | 'error' | 'maintenance'

export interface RobotListResponse {
  robots: Robot[]
  total: number
}

// Job types
export interface Job {
  job_id: string
  workflow_id: string
  workflow_name?: string
  status: JobStatus
  priority: number
  environment?: string
  assigned_robot_id: string | null
  input: Record<string, unknown>
  result: Record<string, unknown> | null
  error: string | null
  progress: number | null
  current_node: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
  retry_count: number
  max_retries: number
}

export type JobStatus = 'queued' | 'assigned' | 'running' | 'completed' | 'failed' | 'cancelled' | 'timeout'

export interface JobListResponse {
  jobs: Job[]
  total: number
}

export interface JobClaimRequest {
  environment?: string
  limit?: number
  visibility_timeout_seconds?: number
}

// Schedule types
export interface Schedule {
  schedule_id: string
  workflow_id: string
  name: string
  cron_expression: string
  timezone: string
  enabled: boolean
  priority: number
  next_run_at: string | null
  last_run_at: string | null
  created_at: string
  input: Record<string, unknown>
}

export interface ScheduleListResponse {
  schedules: Schedule[]
  total: number
}

export interface ScheduleCreateRequest {
  workflow_id: string
  cron_expression: string
  environment?: string
  is_enabled?: boolean
  variables?: Record<string, unknown>
}

// API Key types
export interface ApiKey {
  key_id: string
  robot_id: string | null
  name: string
  key_prefix: string
  revoked: boolean
  created_at: string
  expires_at: string
  last_used_at: string | null
}

export interface ApiKeyListResponse {
  api_keys: ApiKey[]
  total: number
}

export interface ApiKeyCreateRequest {
  robot_id: string
  name: string
  expires_days?: number
}

export interface ApiKeyCreateResponse {
  id: string
  robot_id: string
  name: string
  api_key: string // Full key, shown only once
  expires_at: string | null
}

// DLQ types
export interface DLQEntry {
  entry_id: string
  job_id: string
  workflow_id: string
  error_message: string
  error_stack: string | null
  input: Record<string, unknown> | null
  retry_count: number
  failed_at: string
  original_created_at: string | null
  created_at: string
}

export interface DLQListResponse {
  entries: DLQEntry[]
  total: number
  pending: number
  limit: number
  offset: number
}

// Analytics types
export interface FleetMetrics {
  total_robots: number
  active_robots: number
  idle_robots: number
  offline_robots: number
  total_jobs: number
  completed_jobs: number
  running_jobs: number
  queued_jobs: number
  failed_jobs: number
  success_rate: number
  avg_execution_time: number
  dlq_count: number
}

export interface RobotMetrics {
  robot_id: string
  name: string
  jobs_completed: number
  jobs_failed: number
  average_execution_time_ms: number
  uptime_percent: number
}

// WebSocket message types
export interface WSJobUpdate {
  type: 'job_status'
  ts: string
  tenant_id: string | null
  workspace_id: string | null
  data: {
    job_id: string
    status: JobStatus
    progress?: number
    current_node?: string
    robot_id?: string
  }
}

export interface WSRobotUpdate {
  type: 'robot_heartbeat' | 'robot_status'
  ts: string
  tenant_id: string | null
  workspace_id: string | null
  data: {
    robot_id: string
    status: RobotStatus
    metrics?: Record<string, unknown>
  }
}

export interface WSQueueUpdate {
  type: 'queue_depth'
  ts: string
  data: {
    pending: number
    running: number
    by_environment: Record<string, number>
  }
}

export type WSMessage = WSJobUpdate | WSRobotUpdate | WSQueueUpdate

// Common filter types
export interface ListFilters {
  tenant_id?: string | null
  workspace_id?: string | null
  environment?: string
  status?: string
  limit?: number
  offset?: number
}

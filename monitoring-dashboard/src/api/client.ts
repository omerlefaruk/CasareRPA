/**
 * API client for CasareRPA Orchestrator
 */

const API_BASE = '/api/v1'

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  body?: unknown
  headers?: Record<string, string>
}

class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, headers = {} } = options

  const config: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
  }

  if (body) {
    config.body = JSON.stringify(body)
  }

  const response = await fetch(`${API_BASE}${endpoint}`, config)

  if (!response.ok) {
    let detail = 'Request failed'
    try {
      const error = await response.json()
      detail = error.detail || error.message || detail
    } catch {
      detail = response.statusText
    }
    throw new ApiError(response.status, detail)
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T
  }

  return response.json()
}

// Robots API
export const robotsApi = {
  list: (params?: { tenant_id?: string; workspace_id?: string; environment?: string; status?: string }) => {
    const query = new URLSearchParams()
    if (params?.tenant_id) query.set('tenant_id', params.tenant_id)
    if (params?.workspace_id) query.set('workspace_id', params.workspace_id)
    if (params?.environment) query.set('environment', params.environment)
    if (params?.status) query.set('status', params.status)
    const qs = query.toString()
    return request<{ robots: unknown[]; total: number }>(`/robots${qs ? `?${qs}` : ''}`)
  },

  get: (robotId: string) => request<unknown>(`/robots/${robotId}`),

  delete: (robotId: string) => request<void>(`/robots/${robotId}`, { method: 'DELETE' }),

  updateStatus: (robotId: string, status: string) =>
    request<unknown>(`/robots/${robotId}/status`, { method: 'PUT', body: { status } }),
}

// Jobs API
export const jobsApi = {
  list: (params?: {
    tenant_id?: string
    workspace_id?: string
    status?: string
    environment?: string
    limit?: number
    offset?: number
  }) => {
    const query = new URLSearchParams()
    if (params?.tenant_id) query.set('tenant_id', params.tenant_id)
    if (params?.workspace_id) query.set('workspace_id', params.workspace_id)
    if (params?.status) query.set('status', params.status)
    if (params?.environment) query.set('environment', params.environment)
    if (params?.limit) query.set('limit', params.limit.toString())
    if (params?.offset) query.set('offset', params.offset.toString())
    const qs = query.toString()
    return request<{ jobs: unknown[]; total: number }>(`/jobs${qs ? `?${qs}` : ''}`)
  },

  cancel: (jobId: string) => request<unknown>(`/jobs/${jobId}/cancel`, { method: 'POST' }),

  retry: (jobId: string) => request<unknown>(`/jobs/${jobId}/retry`, { method: 'POST' }),
}

// Schedules API
export const schedulesApi = {
  list: (params?: { tenant_id?: string; workspace_id?: string }) => {
    const query = new URLSearchParams()
    if (params?.tenant_id) query.set('tenant_id', params.tenant_id)
    if (params?.workspace_id) query.set('workspace_id', params.workspace_id)
    const qs = query.toString()
    return request<{ schedules: unknown[]; total: number }>(`/schedules${qs ? `?${qs}` : ''}`)
  },

  create: (data: {
    tenant_id: string
    workspace_id: string
    name: string
    workflow_id: string
    cron_expression: string
    timezone: string
    input?: Record<string, unknown>
    priority?: number
  }) => request<unknown>('/schedules', { method: 'POST', body: data }),

  update: (scheduleId: string, data: { enabled?: boolean; cron_expression?: string; timezone?: string }) =>
    request<unknown>(`/schedules/${scheduleId}`, { method: 'PUT', body: data }),

  delete: (scheduleId: string) => request<void>(`/schedules/${scheduleId}`, { method: 'DELETE' }),

  runNow: (scheduleId: string) => request<unknown>(`/schedules/${scheduleId}/run`, { method: 'POST' }),
}

// API Keys API
export const apiKeysApi = {
  list: (params?: { tenant_id?: string; robot_id?: string }) => {
    const query = new URLSearchParams()
    if (params?.tenant_id) query.set('tenant_id', params.tenant_id)
    if (params?.robot_id) query.set('robot_id', params.robot_id)
    const qs = query.toString()
    return request<{ api_keys: unknown[]; total: number }>(`/robot-api-keys${qs ? `?${qs}` : ''}`)
  },

  create: (data: { tenant_id: string; name: string; robot_id?: string; expires_in_days?: number }) =>
    request<{ id: string; api_key: string }>('/robot-api-keys', { method: 'POST', body: data }),

  revoke: (keyId: string) => request<void>(`/robot-api-keys/${keyId}`, { method: 'DELETE' }),

  rotate: (keyId: string) =>
    request<{ id: string; api_key: string }>(`/robot-api-keys/${keyId}/rotate`, { method: 'POST' }),
}

// DLQ API
export const dlqApi = {
  list: (params?: { tenant_id?: string; workspace_id?: string; limit?: number; offset?: number; status?: string }) => {
    const query = new URLSearchParams()
    if (params?.tenant_id) query.set('tenant_id', params.tenant_id)
    if (params?.workspace_id) query.set('workspace_id', params.workspace_id)
    if (params?.limit) query.set('limit', params.limit.toString())
    if (params?.offset) query.set('offset', params.offset.toString())
    if (params?.status) query.set('status', params.status)
    const qs = query.toString()
    return request<{ entries: unknown[]; total: number; pending: number }>(`/dlq${qs ? `?${qs}` : ''}`)
  },

  retry: (entryId: string) => request<{ new_job_id: string }>(`/dlq/${entryId}/retry`, { method: 'POST' }),

  purge: (entryId: string) => request<void>(`/dlq/${entryId}`, { method: 'DELETE' }),
}

// Analytics API
export const analyticsApi = {
  getMetrics: (params?: { tenant_id?: string; workspace_id?: string; time_range?: string }) => {
    const query = new URLSearchParams()
    if (params?.tenant_id) query.set('tenant_id', params.tenant_id)
    if (params?.workspace_id) query.set('workspace_id', params.workspace_id)
    if (params?.time_range) query.set('time_range', params.time_range)
    const qs = query.toString()
    return request<unknown>(`/metrics/fleet${qs ? `?${qs}` : ''}`)
  },

  robotMetrics: (robotId: string, params?: { days?: number }) => {
    const query = new URLSearchParams()
    if (params?.days) query.set('days', params.days.toString())
    const qs = query.toString()
    return request<unknown>(`/metrics/robot/${robotId}${qs ? `?${qs}` : ''}`)
  },

  jobStats: (params?: { tenant_id?: string; days?: number }) => {
    const query = new URLSearchParams()
    if (params?.tenant_id) query.set('tenant_id', params.tenant_id)
    if (params?.days) query.set('days', params.days.toString())
    const qs = query.toString()
    return request<unknown>(`/metrics/jobs${qs ? `?${qs}` : ''}`)
  },
}

export { ApiError }

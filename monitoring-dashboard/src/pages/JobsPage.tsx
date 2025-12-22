import { useEffect, useState, useCallback } from 'react'
import { useApi } from '../api/ApiContext'
import { useJobsWebSocket } from '../hooks/useWebSocket'
import type { Job, JobStatus, WSJobUpdate } from '../types'
import { formatDistanceToNow, format } from 'date-fns'
import { RefreshCw, XCircle, RotateCcw, Eye } from 'lucide-react'

interface Props {
  tenantId: string | null
  workspaceId: string | null
}

const statusColors: Record<JobStatus, string> = {
  queued: 'bg-gray-500',
  assigned: 'bg-blue-500',
  running: 'bg-warning',
  completed: 'bg-success',
  failed: 'bg-error',
  cancelled: 'bg-gray-600',
  timeout: 'bg-error',
}

const statusLabels: Record<JobStatus, string> = {
  queued: 'Queued',
  assigned: 'Assigned',
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
  cancelled: 'Cancelled',
  timeout: 'Timeout',
}

export default function JobsPage({ tenantId, workspaceId }: Props) {
  const api = useApi()
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [selectedJob, setSelectedJob] = useState<Job | null>(null)

  const loadJobs = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.jobs.list({
        tenant_id: tenantId || undefined,
        workspace_id: workspaceId || undefined,
        status: statusFilter || undefined,
        limit: 100,
      })
      setJobs(response.jobs as Job[])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load jobs')
    } finally {
      setLoading(false)
    }
  }, [api.jobs, tenantId, workspaceId, statusFilter])

  useEffect(() => {
    loadJobs()
  }, [loadJobs])

  // Real-time updates
  useJobsWebSocket((update: WSJobUpdate) => {
    setJobs((prev) => {
      const exists = prev.find((j) => j.job_id === update.data.job_id)
      if (exists) {
        return prev.map((job) =>
          job.job_id === update.data.job_id
            ? { ...job, status: update.data.status, progress: update.data.progress || job.progress }
            : job
        )
      }
      // New job - prepend
      return [update.data as Job, ...prev].slice(0, 100)
    })
  })

  const handleCancel = async (jobId: string) => {
    if (!confirm('Cancel this job?')) return
    try {
      await api.jobs.cancel(jobId)
      loadJobs()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to cancel job')
    }
  }

  const handleRetry = async (jobId: string) => {
    try {
      await api.jobs.retry(jobId)
      loadJobs()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to retry job')
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Jobs</h2>
        <div className="flex items-center gap-4">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-surface border border-gray-600 rounded px-3 py-2 text-sm"
          >
            <option value="">All Status</option>
            <option value="queued">Queued</option>
            <option value="assigned">Assigned</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <button
            onClick={loadJobs}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded text-sm transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-error/20 border border-error rounded p-4 mb-6 text-error">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-8 h-8 animate-spin text-primary-500" />
        </div>
      )}

      {/* Jobs Table */}
      {!loading && (
        <div className="bg-surface-elevated rounded-lg border border-gray-700 overflow-hidden">
          <table className="w-full">
            <thead className="bg-surface">
              <tr className="text-left text-sm text-gray-400 border-b border-gray-700">
                <th className="px-4 py-3">Job ID</th>
                <th className="px-4 py-3">Workflow</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Progress</th>
                <th className="px-4 py-3">Robot</th>
                <th className="px-4 py-3">Created</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr
                  key={job.job_id}
                  className="border-b border-gray-700/50 hover:bg-surface-hover transition-colors"
                >
                  <td className="px-4 py-3">
                    <span className="font-mono text-sm">{job.job_id.slice(0, 8)}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-sm text-gray-300">
                      {job.workflow_id.slice(0, 8)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${statusColors[job.status]}`} />
                      <span className="text-sm">{statusLabels[job.status]}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {job.progress !== undefined && job.progress !== null && (
                      <div className="flex items-center gap-2">
                        <div className="w-20 bg-surface rounded-full h-2">
                          <div
                            className="bg-primary-500 h-2 rounded-full transition-all"
                            style={{ width: `${job.progress}%` }}
                          />
                        </div>
                        <span className="text-sm text-gray-400">{job.progress}%</span>
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {job.assigned_robot_id ? (
                      <span className="font-mono text-sm text-gray-300">
                        {job.assigned_robot_id.slice(0, 8)}
                      </span>
                    ) : (
                      <span className="text-gray-500">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-400">
                    {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => setSelectedJob(job)}
                        className="p-1.5 hover:bg-surface rounded transition-colors"
                        title="View Details"
                      >
                        <Eye className="w-4 h-4 text-gray-400" />
                      </button>
                      {['queued', 'assigned', 'running'].includes(job.status) && (
                        <button
                          onClick={() => handleCancel(job.job_id)}
                          className="p-1.5 hover:bg-error/20 rounded transition-colors"
                          title="Cancel"
                        >
                          <XCircle className="w-4 h-4 text-error" />
                        </button>
                      )}
                      {['failed', 'timeout', 'cancelled'].includes(job.status) && (
                        <button
                          onClick={() => handleRetry(job.job_id)}
                          className="p-1.5 hover:bg-primary-600/20 rounded transition-colors"
                          title="Retry"
                        >
                          <RotateCcw className="w-4 h-4 text-primary-400" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {jobs.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-gray-500">
                    No jobs found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Job Detail Modal */}
      {selectedJob && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={() => setSelectedJob(null)}
        >
          <div
            className="bg-surface-elevated rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-xl font-bold">Job Details</h3>
              <button
                onClick={() => setSelectedJob(null)}
                className="text-gray-400 hover:text-white"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Job ID</span>
                  <p className="font-mono">{selectedJob.job_id}</p>
                </div>
                <div>
                  <span className="text-gray-400">Workflow ID</span>
                  <p className="font-mono">{selectedJob.workflow_id}</p>
                </div>
                <div>
                  <span className="text-gray-400">Status</span>
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${statusColors[selectedJob.status]}`} />
                    {statusLabels[selectedJob.status]}
                  </div>
                </div>
                <div>
                  <span className="text-gray-400">Priority</span>
                  <p>{selectedJob.priority}</p>
                </div>
                <div>
                  <span className="text-gray-400">Created</span>
                  <p>{format(new Date(selectedJob.created_at), 'PPpp')}</p>
                </div>
                {selectedJob.started_at && (
                  <div>
                    <span className="text-gray-400">Started</span>
                    <p>{format(new Date(selectedJob.started_at), 'PPpp')}</p>
                  </div>
                )}
                {selectedJob.completed_at && (
                  <div>
                    <span className="text-gray-400">Completed</span>
                    <p>{format(new Date(selectedJob.completed_at), 'PPpp')}</p>
                  </div>
                )}
              </div>

              {selectedJob.error && (
                <div>
                  <span className="text-gray-400 text-sm">Error</span>
                  <pre className="bg-error/10 border border-error/30 rounded p-3 mt-1 text-sm text-error overflow-x-auto">
                    {selectedJob.error}
                  </pre>
                </div>
              )}

              {selectedJob.result && (
                <div>
                  <span className="text-gray-400 text-sm">Result</span>
                  <pre className="bg-surface rounded p-3 mt-1 text-sm overflow-x-auto">
                    {JSON.stringify(selectedJob.result, null, 2)}
                  </pre>
                </div>
              )}

              {selectedJob.input && Object.keys(selectedJob.input).length > 0 && (
                <div>
                  <span className="text-gray-400 text-sm">Input</span>
                  <pre className="bg-surface rounded p-3 mt-1 text-sm overflow-x-auto">
                    {JSON.stringify(selectedJob.input, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

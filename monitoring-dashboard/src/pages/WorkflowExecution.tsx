import { useState } from 'react'
import { useJobs } from '@/hooks/useJobs'
import { useLiveJobs } from '@/api/websockets'

function WorkflowExecution() {
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [limit] = useState(50)

  const { data: jobs, isLoading, error, refetch } = useJobs({
    status: statusFilter,
    limit,
  })

  // WebSocket for live job updates
  useLiveJobs((message) => {
    console.log('[Live Job Update]', message)
    // Invalidate query to refetch
    refetch()
  })

  if (isLoading) {
    return (
      <div className="page">
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Loading job history...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page">
        <div className="error">
          <p>Failed to load job history</p>
          <p>{error.message}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Workflow Execution</h1>
        <p className="page-subtitle">Monitor job execution history and live updates</p>
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <label style={{ color: '#999', fontSize: '0.875rem' }}>
            Status:
            <select
              value={statusFilter ?? ''}
              onChange={(e) => setStatusFilter(e.target.value || undefined)}
              style={{
                marginLeft: '0.5rem',
                padding: '0.5rem',
                backgroundColor: '#1a1a1a',
                border: '1px solid #333',
                borderRadius: '4px',
                color: '#fff',
              }}
            >
              <option value="">All</option>
              <option value="pending">Pending</option>
              <option value="claimed">Running</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
          </label>
        </div>
      </div>

      {/* Job History Table */}
      <div className="card">
        <h2 className="card-title">Job History ({jobs?.length ?? 0} jobs)</h2>

        {jobs && jobs.length > 0 ? (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Job ID</th>
                  <th>Workflow</th>
                  <th>Robot</th>
                  <th>Status</th>
                  <th>Duration</th>
                  <th>Created</th>
                  <th>Completed</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <tr key={job.job_id}>
                    <td>
                      <code style={{ fontSize: '0.875rem' }}>
                        {job.job_id.slice(0, 8)}
                      </code>
                    </td>
                    <td>{job.workflow_name || job.workflow_id}</td>
                    <td>
                      {job.robot_id ? (
                        <code style={{ fontSize: '0.875rem' }}>
                          {job.robot_id.slice(0, 8)}
                        </code>
                      ) : (
                        <span style={{ color: '#999' }}>—</span>
                      )}
                    </td>
                    <td>
                      <span className={`status-badge ${job.status}`}>
                        {job.status}
                      </span>
                    </td>
                    <td>
                      {job.duration_ms ? (
                        <span style={{ color: '#999' }}>
                          {(job.duration_ms / 1000).toFixed(1)}s
                        </span>
                      ) : (
                        <span style={{ color: '#999' }}>—</span>
                      )}
                    </td>
                    <td style={{ color: '#999', fontSize: '0.875rem' }}>
                      {new Date(job.created_at).toLocaleString()}
                    </td>
                    <td style={{ color: '#999', fontSize: '0.875rem' }}>
                      {job.completed_at ? (
                        new Date(job.completed_at).toLocaleString()
                      ) : (
                        <span style={{ color: '#fbbf24' }}>Running...</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#999' }}>
            <p>No jobs found</p>
            {statusFilter && (
              <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
                Try changing the status filter
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default WorkflowExecution

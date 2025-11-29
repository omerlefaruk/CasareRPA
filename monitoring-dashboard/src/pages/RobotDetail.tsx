import { useParams, Link } from 'react-router-dom'
import { useRobotDetails } from '@/hooks/useRobots'
import { useJobs } from '@/hooks/useJobs'

function RobotDetail() {
  const { robotId } = useParams<{ robotId: string }>()

  const { data: robot, isLoading, error } = useRobotDetails(robotId!)
  const { data: robotJobs } = useJobs({ robot_id: robotId, limit: 20 })

  if (isLoading) {
    return (
      <div className="page">
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Loading robot details...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page">
        <div className="error">
          <p>Failed to load robot details</p>
          <p>{error.message}</p>
        </div>
      </div>
    )
  }

  if (!robot) {
    return (
      <div className="page">
        <div className="error">
          <p>Robot not found</p>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="page-header">
        <Link to="/" style={{ color: '#646cff', textDecoration: 'none', fontSize: '0.875rem' }}>
          ← Back to Fleet
        </Link>
        <h1 className="page-title" style={{ marginTop: '0.5rem' }}>
          Robot: {robot.hostname}
        </h1>
        <p className="page-subtitle">
          <code>{robot.robot_id}</code>
        </p>
      </div>

      {/* Robot Status */}
      <div className="grid grid-cols-4" style={{ marginBottom: '2rem' }}>
        <div className="metric-card">
          <div className="metric-label">Status</div>
          <div style={{ marginTop: '0.5rem' }}>
            <span className={`status-badge ${robot.status}`}>{robot.status}</span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">CPU Usage</div>
          <div className="metric-value" style={{ color: robot.cpu_percent > 80 ? '#f87171' : '#4ade80' }}>
            {robot.cpu_percent.toFixed(1)}%
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Memory</div>
          <div className="metric-value">{robot.memory_mb.toFixed(0)} MB</div>
          <div className="metric-change">{robot.memory_percent.toFixed(1)}%</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Current Job</div>
          <div style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>
            {robot.current_job_id ? (
              <code>{robot.current_job_id.slice(0, 12)}</code>
            ) : (
              <span style={{ color: '#999' }}>Idle</span>
            )}
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-3" style={{ marginBottom: '2rem' }}>
        <div className="metric-card">
          <div className="metric-label">Jobs Completed Today</div>
          <div className="metric-value" style={{ color: '#4ade80' }}>
            {robot.jobs_completed_today}
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Jobs Failed Today</div>
          <div className="metric-value" style={{ color: robot.jobs_failed_today > 0 ? '#f87171' : '#999' }}>
            {robot.jobs_failed_today}
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Avg Duration</div>
          <div className="metric-value">{robot.average_job_duration_seconds.toFixed(1)}s</div>
        </div>
      </div>

      {/* Recent Jobs */}
      <div className="card">
        <h2 className="card-title">Recent Jobs ({robotJobs?.length ?? 0})</h2>

        {robotJobs && robotJobs.length > 0 ? (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Job ID</th>
                  <th>Workflow</th>
                  <th>Status</th>
                  <th>Duration</th>
                  <th>Completed</th>
                </tr>
              </thead>
              <tbody>
                {robotJobs.map((job) => (
                  <tr key={job.job_id}>
                    <td>
                      <code style={{ fontSize: '0.875rem' }}>{job.job_id.slice(0, 8)}</code>
                    </td>
                    <td>{job.workflow_name || job.workflow_id}</td>
                    <td>
                      <span className={`status-badge ${job.status}`}>{job.status}</span>
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
                      {job.completed_at ? new Date(job.completed_at).toLocaleString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#999' }}>
            <p>No recent jobs</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default RobotDetail

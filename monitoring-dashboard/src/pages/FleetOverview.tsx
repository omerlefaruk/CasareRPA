import { useFleetMetrics } from '@/hooks/useFleetMetrics'
import { useRobots } from '@/hooks/useRobots'
import { useQueueMetrics } from '@/api/websockets'
import { Link } from 'react-router-dom'

function FleetOverview() {
  const { data: fleetMetrics, isLoading: metricsLoading, error: metricsError } = useFleetMetrics()
  const { data: robots, isLoading: robotsLoading } = useRobots()

  // WebSocket for real-time queue depth
  const { lastMessage: queueMessage } = useQueueMetrics()

  if (metricsLoading) {
    return (
      <div className="page">
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Loading fleet metrics...</p>
        </div>
      </div>
    )
  }

  if (metricsError) {
    return (
      <div className="page">
        <div className="error">
          <p>Failed to load fleet metrics</p>
          <p>{metricsError.message}</p>
        </div>
      </div>
    )
  }

  const queueDepth = queueMessage?.depth ?? fleetMetrics?.queue_depth ?? 0

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Fleet Overview</h1>
        <p className="page-subtitle">Monitor your multi-robot RPA fleet in real-time</p>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-4" style={{ marginBottom: '2rem' }}>
        <div className="metric-card">
          <div className="metric-label">Total Robots</div>
          <div className="metric-value">{fleetMetrics?.total_robots ?? 0}</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Active Robots</div>
          <div className="metric-value" style={{ color: '#4ade80' }}>
            {fleetMetrics?.active_robots ?? 0}
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Active Jobs</div>
          <div className="metric-value" style={{ color: '#fbbf24' }}>
            {fleetMetrics?.active_jobs ?? 0}
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Queue Depth</div>
          <div className="metric-value" style={{ color: queueDepth > 10 ? '#f87171' : '#646cff' }}>
            {queueDepth}
          </div>
          {queueMessage && (
            <div className="metric-change" style={{ color: '#4ade80' }}>
              ● Live
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2" style={{ marginBottom: '2rem' }}>
        <div className="metric-card">
          <div className="metric-label">Jobs Today</div>
          <div className="metric-value">{fleetMetrics?.total_jobs_today ?? 0}</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Avg Duration</div>
          <div className="metric-value">
            {fleetMetrics?.average_job_duration_seconds?.toFixed(1) ?? '0.0'}s
          </div>
        </div>
      </div>

      {/* Robot Status Grid */}
      <div className="card">
        <h2 className="card-title">Robot Status</h2>

        {robotsLoading ? (
          <div className="loading">
            <div className="loading-spinner"></div>
            <p>Loading robots...</p>
          </div>
        ) : robots && robots.length > 0 ? (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Robot ID</th>
                  <th>Hostname</th>
                  <th>Status</th>
                  <th>Current Job</th>
                  <th>Last Seen</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {robots.map((robot) => (
                  <tr key={robot.robot_id}>
                    <td>
                      <code style={{ fontSize: '0.875rem' }}>{robot.robot_id.slice(0, 8)}</code>
                    </td>
                    <td>{robot.hostname}</td>
                    <td>
                      <span className={`status-badge ${robot.status}`}>
                        {robot.status}
                      </span>
                    </td>
                    <td>
                      {robot.current_job_id ? (
                        <code style={{ fontSize: '0.875rem' }}>
                          {robot.current_job_id.slice(0, 8)}
                        </code>
                      ) : (
                        <span style={{ color: '#999' }}>—</span>
                      )}
                    </td>
                    <td style={{ color: '#999', fontSize: '0.875rem' }}>
                      {new Date(robot.last_seen).toLocaleString()}
                    </td>
                    <td>
                      <Link
                        to={`/robots/${robot.robot_id}`}
                        style={{
                          color: '#646cff',
                          textDecoration: 'none',
                          fontSize: '0.875rem',
                        }}
                      >
                        View Details →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#999' }}>
            <p>No robots registered yet</p>
            <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
              Robots will appear here once they connect to the orchestrator
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default FleetOverview

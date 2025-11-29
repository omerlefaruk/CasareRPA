import { useAnalytics } from '@/hooks/useAnalytics'

function Analytics() {
  const { data: analytics, isLoading, error } = useAnalytics()

  if (isLoading) {
    return (
      <div className="page">
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Loading analytics...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page">
        <div className="error">
          <p>Failed to load analytics</p>
          <p>{error.message}</p>
        </div>
      </div>
    )
  }

  if (!analytics) {
    return null
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Analytics</h1>
        <p className="page-subtitle">Workflow execution insights and trends</p>
      </div>

      {/* Success Rate */}
      <div className="grid grid-cols-3" style={{ marginBottom: '2rem' }}>
        <div className="metric-card">
          <div className="metric-label">Success Rate</div>
          <div className="metric-value" style={{ color: '#4ade80' }}>
            {analytics.success_rate.toFixed(1)}%
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Failure Rate</div>
          <div className="metric-value" style={{ color: analytics.failure_rate > 10 ? '#f87171' : '#999' }}>
            {analytics.failure_rate.toFixed(1)}%
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Self-Healing Success</div>
          <div className="metric-value">
            {analytics.self_healing_success_rate ? (
              <span style={{ color: '#4ade80' }}>{analytics.self_healing_success_rate.toFixed(1)}%</span>
            ) : (
              <span style={{ color: '#999' }}>N/A</span>
            )}
          </div>
        </div>
      </div>

      {/* Duration Percentiles */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <h2 className="card-title">Job Duration Percentiles</h2>
        <div className="grid grid-cols-3">
          <div className="metric-card">
            <div className="metric-label">P50 (Median)</div>
            <div className="metric-value">{(analytics.p50_duration_ms / 1000).toFixed(1)}s</div>
            <div className="metric-change" style={{ color: '#999' }}>
              50% of jobs complete within this time
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-label">P90</div>
            <div className="metric-value">{(analytics.p90_duration_ms / 1000).toFixed(1)}s</div>
            <div className="metric-change" style={{ color: '#999' }}>
              90% of jobs complete within this time
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-label">P99</div>
            <div className="metric-value" style={{ color: '#fbbf24' }}>
              {(analytics.p99_duration_ms / 1000).toFixed(1)}s
            </div>
            <div className="metric-change" style={{ color: '#999' }}>
              99% of jobs complete within this time
            </div>
          </div>
        </div>
      </div>

      {/* Slowest Workflows */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <h2 className="card-title">Slowest Workflows</h2>

        {analytics.slowest_workflows.length > 0 ? (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Workflow Name</th>
                  <th>Workflow ID</th>
                  <th>Average Duration</th>
                </tr>
              </thead>
              <tbody>
                {analytics.slowest_workflows.map((workflow, index) => (
                  <tr key={workflow.workflow_id}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span
                          style={{
                            display: 'inline-block',
                            width: '1.5rem',
                            textAlign: 'center',
                            color: '#999',
                            fontSize: '0.875rem',
                          }}
                        >
                          {index + 1}
                        </span>
                        {workflow.workflow_name}
                      </div>
                    </td>
                    <td>
                      <code style={{ fontSize: '0.875rem' }}>{workflow.workflow_id}</code>
                    </td>
                    <td style={{ color: '#fbbf24', fontWeight: 600 }}>
                      {(workflow.average_duration_ms / 1000).toFixed(1)}s
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#999' }}>
            <p>No workflow data available</p>
          </div>
        )}
      </div>

      {/* Error Distribution */}
      <div className="card">
        <h2 className="card-title">Error Distribution</h2>

        {analytics.error_distribution.length > 0 ? (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Error Type</th>
                  <th>Count</th>
                  <th>Percentage</th>
                </tr>
              </thead>
              <tbody>
                {analytics.error_distribution.map((error) => {
                  const totalErrors = analytics.error_distribution.reduce(
                    (sum, e) => sum + e.count,
                    0
                  )
                  const percentage = (error.count / totalErrors) * 100

                  return (
                    <tr key={error.error_type}>
                      <td>
                        <code style={{ fontSize: '0.875rem', color: '#f87171' }}>
                          {error.error_type}
                        </code>
                      </td>
                      <td>{error.count}</td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <div
                            style={{
                              flex: 1,
                              height: '8px',
                              backgroundColor: '#333',
                              borderRadius: '4px',
                              overflow: 'hidden',
                            }}
                          >
                            <div
                              style={{
                                width: `${percentage}%`,
                                height: '100%',
                                backgroundColor: '#f87171',
                              }}
                            />
                          </div>
                          <span style={{ color: '#999', fontSize: '0.875rem', minWidth: '3rem' }}>
                            {percentage.toFixed(1)}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#999' }}>
            <p>No error data available</p>
            <p style={{ fontSize: '0.875rem', marginTop: '0.5rem', color: '#4ade80' }}>
              ✓ No errors detected - great job!
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Analytics

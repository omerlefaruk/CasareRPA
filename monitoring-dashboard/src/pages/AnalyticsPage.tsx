import { useEffect, useState, useCallback } from 'react'
import { useApi } from '../api/ApiContext'
import type { FleetMetrics } from '../types'
import { RefreshCw, Bot, Briefcase, Clock, AlertTriangle, CheckCircle } from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'

interface Props {
  tenantId: string | null
  workspaceId: string | null
}

const COLORS = ['#4ade80', '#f97316', '#ef4444', '#6366f1', '#8b5cf6']

export default function AnalyticsPage({ tenantId, workspaceId }: Props) {
  const api = useApi()
  const [metrics, setMetrics] = useState<FleetMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [timeRange, setTimeRange] = useState('24h')

  const loadMetrics = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.analytics.getMetrics({
        tenant_id: tenantId || undefined,
        workspace_id: workspaceId || undefined,
        time_range: timeRange,
      })
      setMetrics(response as FleetMetrics)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load metrics')
    } finally {
      setLoading(false)
    }
  }, [api.analytics, tenantId, workspaceId, timeRange])

  useEffect(() => {
    loadMetrics()
    // Auto-refresh every 30s
    const interval = setInterval(loadMetrics, 30000)
    return () => clearInterval(interval)
  }, [loadMetrics])

  // Mock time series data for demo
  const timeSeriesData = [
    { time: '00:00', jobs: 12, success: 10, failed: 2 },
    { time: '04:00', jobs: 8, success: 7, failed: 1 },
    { time: '08:00', jobs: 25, success: 22, failed: 3 },
    { time: '12:00', jobs: 45, success: 40, failed: 5 },
    { time: '16:00', jobs: 38, success: 35, failed: 3 },
    { time: '20:00', jobs: 20, success: 18, failed: 2 },
  ]

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Analytics</h2>
        <div className="flex items-center gap-4">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="bg-surface border border-gray-600 rounded px-3 py-2 text-sm"
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
          <button
            onClick={loadMetrics}
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
      {loading && !metrics && (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-8 h-8 animate-spin text-primary-500" />
        </div>
      )}

      {/* Metrics Dashboard */}
      {metrics && (
        <div className="space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-surface-elevated rounded-lg p-4 border border-gray-700">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary-600/20 rounded-lg">
                  <Bot className="w-5 h-5 text-primary-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Active Robots</p>
                  <p className="text-2xl font-bold">{metrics.active_robots}</p>
                </div>
              </div>
            </div>

            <div className="bg-surface-elevated rounded-lg p-4 border border-gray-700">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-success/20 rounded-lg">
                  <CheckCircle className="w-5 h-5 text-success" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Success Rate</p>
                  <p className="text-2xl font-bold">{metrics.success_rate.toFixed(1)}%</p>
                </div>
              </div>
            </div>

            <div className="bg-surface-elevated rounded-lg p-4 border border-gray-700">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-warning/20 rounded-lg">
                  <Briefcase className="w-5 h-5 text-warning" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Jobs Today</p>
                  <p className="text-2xl font-bold">{metrics.total_jobs}</p>
                </div>
              </div>
            </div>

            <div className="bg-surface-elevated rounded-lg p-4 border border-gray-700">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-500/20 rounded-lg">
                  <Clock className="w-5 h-5 text-purple-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Avg Duration</p>
                  <p className="text-2xl font-bold">{(metrics.avg_execution_time / 1000).toFixed(1)}s</p>
                </div>
              </div>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Jobs Over Time */}
            <div className="bg-surface-elevated rounded-lg p-4 border border-gray-700">
              <h3 className="font-semibold mb-4">Jobs Over Time</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={timeSeriesData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="time" stroke="#9ca3af" />
                    <YAxis stroke="#9ca3af" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1e1e2e',
                        border: '1px solid #374151',
                        borderRadius: '8px',
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="success"
                      stroke="#4ade80"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="failed"
                      stroke="#ef4444"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Job Status Distribution */}
            <div className="bg-surface-elevated rounded-lg p-4 border border-gray-700">
              <h3 className="font-semibold mb-4">Job Status Distribution</h3>
              <div className="h-64 flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Completed', value: metrics.completed_jobs },
                        { name: 'Running', value: metrics.running_jobs },
                        { name: 'Failed', value: metrics.failed_jobs },
                        { name: 'Queued', value: metrics.queued_jobs },
                      ]}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {COLORS.map((color, index) => (
                        <Cell key={`cell-${index}`} fill={color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1e1e2e',
                        border: '1px solid #374151',
                        borderRadius: '8px',
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex flex-wrap justify-center gap-4 mt-2">
                {[
                  { name: 'Completed', color: COLORS[0] },
                  { name: 'Running', color: COLORS[1] },
                  { name: 'Failed', color: COLORS[2] },
                  { name: 'Queued', color: COLORS[3] },
                ].map((item) => (
                  <div key={item.name} className="flex items-center gap-2">
                    <span
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-sm text-gray-400">{item.name}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Secondary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-surface-elevated rounded-lg p-4 border border-gray-700">
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Total Robots</span>
                <span className="text-xl font-semibold">{metrics.total_robots}</span>
              </div>
              <div className="mt-2 flex items-center gap-2 text-sm">
                <span className="text-success">{metrics.active_robots} active</span>
                <span className="text-gray-500">•</span>
                <span className="text-gray-400">{metrics.idle_robots} idle</span>
              </div>
            </div>

            <div className="bg-surface-elevated rounded-lg p-4 border border-gray-700">
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Queue Depth</span>
                <span className="text-xl font-semibold">{metrics.queued_jobs}</span>
              </div>
              <div className="mt-2 h-2 bg-surface rounded-full overflow-hidden">
                <div
                  className="h-full bg-warning transition-all"
                  style={{ width: `${Math.min((metrics.queued_jobs / 100) * 100, 100)}%` }}
                />
              </div>
            </div>

            <div className="bg-surface-elevated rounded-lg p-4 border border-gray-700">
              <div className="flex items-center justify-between">
                <span className="text-gray-400">DLQ Items</span>
                <span className="text-xl font-semibold text-error">{metrics.dlq_count}</span>
              </div>
              {metrics.dlq_count > 0 && (
                <div className="mt-2 flex items-center gap-1 text-sm text-error">
                  <AlertTriangle className="w-4 h-4" />
                  <span>Requires attention</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

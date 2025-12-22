import { useEffect, useState, useCallback } from 'react'
import { useApi } from '../api/ApiContext'
import { useRobotsWebSocket } from '../hooks/useWebSocket'
import type { Robot, RobotStatus, WSRobotUpdate } from '../types'
import { formatDistanceToNow } from 'date-fns'
import { RefreshCw, Trash2, Settings } from 'lucide-react'

interface Props {
  tenantId: string | null
  workspaceId: string | null
}

const statusColors: Record<RobotStatus, string> = {
  online: 'bg-success',
  idle: 'bg-success',
  busy: 'bg-warning',
  offline: 'bg-gray-500',
  error: 'bg-error',
  maintenance: 'bg-purple-500',
}

const statusLabels: Record<RobotStatus, string> = {
  online: 'Online',
  idle: 'Idle',
  busy: 'Busy',
  offline: 'Offline',
  error: 'Error',
  maintenance: 'Maintenance',
}

export default function RobotsPage({ tenantId, workspaceId }: Props) {
  const api = useApi()
  const [robots, setRobots] = useState<Robot[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('')

  const loadRobots = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.robots.list({
        tenant_id: tenantId || undefined,
        workspace_id: workspaceId || undefined,
        status: statusFilter || undefined,
      })
      setRobots(response.robots as Robot[])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load robots')
    } finally {
      setLoading(false)
    }
  }, [api.robots, tenantId, workspaceId, statusFilter])

  useEffect(() => {
    loadRobots()
  }, [loadRobots])

  // Real-time updates
  useRobotsWebSocket((update: WSRobotUpdate) => {
    setRobots((prev) =>
      prev.map((robot) =>
        robot.robot_id === update.data.robot_id
          ? { ...robot, status: update.data.status, metrics: update.data.metrics || robot.metrics }
          : robot
      )
    )
  })

  const handleDelete = async (robotId: string) => {
    if (!confirm('Are you sure you want to delete this robot?')) return
    try {
      await api.robots.delete(robotId)
      setRobots((prev) => prev.filter((r) => r.robot_id !== robotId))
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete robot')
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Robots</h2>
        <div className="flex items-center gap-4">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-surface border border-gray-600 rounded px-3 py-2 text-sm"
          >
            <option value="">All Status</option>
            <option value="online">Online</option>
            <option value="idle">Idle</option>
            <option value="busy">Busy</option>
            <option value="offline">Offline</option>
            <option value="error">Error</option>
          </select>
          <button
            onClick={loadRobots}
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

      {/* Robot Grid */}
      {!loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {robots.map((robot) => (
            <div
              key={robot.robot_id}
              className="bg-surface-elevated rounded-lg p-4 border border-gray-700 hover:border-gray-600 transition-colors"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-lg">{robot.name}</h3>
                  <p className="text-sm text-gray-400">{robot.hostname}</p>
                </div>
                <div className="flex items-center gap-1">
                  <span
                    className={`w-3 h-3 rounded-full ${statusColors[robot.status]}`}
                  />
                  <span className="text-sm text-gray-300">
                    {statusLabels[robot.status]}
                  </span>
                </div>
              </div>

              {/* Details */}
              <div className="space-y-2 text-sm text-gray-400">
                <div className="flex justify-between">
                  <span>Environment:</span>
                  <span className="text-gray-200">{robot.environment}</span>
                </div>
                <div className="flex justify-between">
                  <span>Concurrent Jobs:</span>
                  <span className="text-gray-200">
                    {robot.current_job_ids.length} / {robot.max_concurrent_jobs}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Last Seen:</span>
                  <span className="text-gray-200">
                    {robot.last_seen
                      ? formatDistanceToNow(new Date(robot.last_seen), { addSuffix: true })
                      : 'Never'}
                  </span>
                </div>
                {robot.capabilities.length > 0 && (
                  <div className="flex flex-wrap gap-1 pt-2">
                    {robot.capabilities.map((cap) => (
                      <span
                        key={cap}
                        className="px-2 py-0.5 bg-surface rounded text-xs text-gray-300"
                      >
                        {cap}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-2 mt-4 pt-4 border-t border-gray-700">
                <button className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 bg-surface hover:bg-surface-hover rounded text-sm transition-colors">
                  <Settings className="w-4 h-4" />
                  Configure
                </button>
                <button
                  onClick={() => handleDelete(robot.robot_id)}
                  className="flex items-center justify-center gap-1 px-3 py-1.5 bg-error/20 hover:bg-error/30 text-error rounded text-sm transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}

          {robots.length === 0 && !loading && (
            <div className="col-span-full text-center py-12 text-gray-500">
              No robots found
            </div>
          )}
        </div>
      )}
    </div>
  )
}

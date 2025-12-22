import { useEffect, useState, useCallback } from 'react'
import { useApi } from '../api/ApiContext'
import type { Schedule } from '../types'
import { formatDistanceToNow } from 'date-fns'
import { RefreshCw, Plus, Trash2, Play, Pause, Calendar, Clock } from 'lucide-react'

interface Props {
  tenantId: string | null
  workspaceId: string | null
}

export default function SchedulesPage({ tenantId, workspaceId }: Props) {
  const api = useApi()
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)

  // Create form state
  const [newSchedule, setNewSchedule] = useState({
    name: '',
    workflow_id: '',
    cron_expression: '0 9 * * *', // Default: 9 AM daily
    timezone: 'UTC',
    input: '{}',
    priority: 5,
  })

  const loadSchedules = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.schedules.list({
        tenant_id: tenantId || undefined,
        workspace_id: workspaceId || undefined,
      })
      setSchedules(response.schedules as Schedule[])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load schedules')
    } finally {
      setLoading(false)
    }
  }, [api.schedules, tenantId, workspaceId])

  useEffect(() => {
    loadSchedules()
  }, [loadSchedules])

  const handleToggle = async (scheduleId: string, enabled: boolean) => {
    try {
      await api.schedules.update(scheduleId, { enabled })
      setSchedules((prev) =>
        prev.map((s) => (s.schedule_id === scheduleId ? { ...s, enabled } : s))
      )
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update schedule')
    }
  }

  const handleRunNow = async (scheduleId: string) => {
    try {
      await api.schedules.runNow(scheduleId)
      alert('Job triggered successfully')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to trigger job')
    }
  }

  const handleDelete = async (scheduleId: string) => {
    if (!confirm('Delete this schedule?')) return
    try {
      await api.schedules.delete(scheduleId)
      setSchedules((prev) => prev.filter((s) => s.schedule_id !== scheduleId))
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete schedule')
    }
  }

  const handleCreate = async () => {
    try {
      let input: Record<string, unknown> = {}
      if (newSchedule.input.trim()) {
        input = JSON.parse(newSchedule.input)
      }
      await api.schedules.create({
        tenant_id: tenantId || 'default',
        workspace_id: workspaceId || 'default',
        name: newSchedule.name,
        workflow_id: newSchedule.workflow_id,
        cron_expression: newSchedule.cron_expression,
        timezone: newSchedule.timezone,
        input,
        priority: newSchedule.priority,
      })
      setShowCreate(false)
      setNewSchedule({
        name: '',
        workflow_id: '',
        cron_expression: '0 9 * * *',
        timezone: 'UTC',
        input: '{}',
        priority: 5,
      })
      loadSchedules()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create schedule')
    }
  }

  // Cron presets
  const cronPresets = [
    { label: 'Every hour', cron: '0 * * * *' },
    { label: 'Daily at 9 AM', cron: '0 9 * * *' },
    { label: 'Daily at midnight', cron: '0 0 * * *' },
    { label: 'Every Monday 9 AM', cron: '0 9 * * 1' },
    { label: 'First of month', cron: '0 9 1 * *' },
  ]

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Schedules</h2>
        <div className="flex items-center gap-4">
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 bg-success hover:bg-success/80 rounded text-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Schedule
          </button>
          <button
            onClick={loadSchedules}
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

      {/* Schedules List */}
      {!loading && (
        <div className="space-y-4">
          {schedules.map((schedule) => (
            <div
              key={schedule.schedule_id}
              className={`bg-surface-elevated rounded-lg p-4 border transition-colors ${
                schedule.enabled ? 'border-gray-700' : 'border-gray-800 opacity-60'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="font-semibold text-lg">{schedule.name}</h3>
                    <span
                      className={`px-2 py-0.5 rounded text-xs ${
                        schedule.enabled
                          ? 'bg-success/20 text-success'
                          : 'bg-gray-600/20 text-gray-400'
                      }`}
                    >
                      {schedule.enabled ? 'Active' : 'Disabled'}
                    </span>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-4 text-sm text-gray-400">
                    <div className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      <code className="bg-surface px-2 py-0.5 rounded">
                        {schedule.cron_expression}
                      </code>
                    </div>
                    <div className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      <span>{schedule.timezone}</span>
                    </div>
                    <div>
                      Workflow:{' '}
                      <span className="font-mono text-gray-300">
                        {schedule.workflow_id.slice(0, 8)}
                      </span>
                    </div>
                    <div>Priority: {schedule.priority}</div>
                  </div>
                  <div className="mt-2 text-sm text-gray-500">
                    {schedule.next_run_at && (
                      <span>
                        Next run:{' '}
                        {formatDistanceToNow(new Date(schedule.next_run_at), { addSuffix: true })}
                      </span>
                    )}
                    {schedule.last_run_at && (
                      <span className="ml-4">
                        Last run:{' '}
                        {formatDistanceToNow(new Date(schedule.last_run_at), { addSuffix: true })}
                      </span>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleRunNow(schedule.schedule_id)}
                    className="p-2 hover:bg-primary-600/20 rounded transition-colors"
                    title="Run Now"
                  >
                    <Play className="w-4 h-4 text-primary-400" />
                  </button>
                  <button
                    onClick={() => handleToggle(schedule.schedule_id, !schedule.enabled)}
                    className="p-2 hover:bg-surface rounded transition-colors"
                    title={schedule.enabled ? 'Disable' : 'Enable'}
                  >
                    {schedule.enabled ? (
                      <Pause className="w-4 h-4 text-warning" />
                    ) : (
                      <Play className="w-4 h-4 text-success" />
                    )}
                  </button>
                  <button
                    onClick={() => handleDelete(schedule.schedule_id)}
                    className="p-2 hover:bg-error/20 rounded transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4 text-error" />
                  </button>
                </div>
              </div>
            </div>
          ))}

          {schedules.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No schedules found. Create one to automate your workflows.
            </div>
          )}
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={() => setShowCreate(false)}
        >
          <div
            className="bg-surface-elevated rounded-lg p-6 max-w-lg w-full mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-xl font-bold mb-4">Create Schedule</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Name</label>
                <input
                  type="text"
                  value={newSchedule.name}
                  onChange={(e) => setNewSchedule({ ...newSchedule, name: e.target.value })}
                  className="w-full bg-surface border border-gray-600 rounded px-3 py-2"
                  placeholder="Daily Report"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Workflow ID</label>
                <input
                  type="text"
                  value={newSchedule.workflow_id}
                  onChange={(e) => setNewSchedule({ ...newSchedule, workflow_id: e.target.value })}
                  className="w-full bg-surface border border-gray-600 rounded px-3 py-2 font-mono"
                  placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">CRON Expression</label>
                <input
                  type="text"
                  value={newSchedule.cron_expression}
                  onChange={(e) =>
                    setNewSchedule({ ...newSchedule, cron_expression: e.target.value })
                  }
                  className="w-full bg-surface border border-gray-600 rounded px-3 py-2 font-mono"
                  placeholder="0 9 * * *"
                />
                <div className="flex flex-wrap gap-2 mt-2">
                  {cronPresets.map((preset) => (
                    <button
                      key={preset.cron}
                      onClick={() => setNewSchedule({ ...newSchedule, cron_expression: preset.cron })}
                      className="px-2 py-1 bg-surface hover:bg-surface-hover rounded text-xs transition-colors"
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Timezone</label>
                  <select
                    value={newSchedule.timezone}
                    onChange={(e) => setNewSchedule({ ...newSchedule, timezone: e.target.value })}
                    className="w-full bg-surface border border-gray-600 rounded px-3 py-2"
                  >
                    <option value="UTC">UTC</option>
                    <option value="America/New_York">America/New_York</option>
                    <option value="America/Los_Angeles">America/Los_Angeles</option>
                    <option value="Europe/London">Europe/London</option>
                    <option value="Europe/Istanbul">Europe/Istanbul</option>
                    <option value="Asia/Tokyo">Asia/Tokyo</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Priority</label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={newSchedule.priority}
                    onChange={(e) =>
                      setNewSchedule({ ...newSchedule, priority: parseInt(e.target.value) || 5 })
                    }
                    className="w-full bg-surface border border-gray-600 rounded px-3 py-2"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Input (JSON)</label>
                <textarea
                  value={newSchedule.input}
                  onChange={(e) => setNewSchedule({ ...newSchedule, input: e.target.value })}
                  className="w-full bg-surface border border-gray-600 rounded px-3 py-2 font-mono text-sm h-24"
                  placeholder="{}"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  onClick={() => setShowCreate(false)}
                  className="px-4 py-2 bg-surface hover:bg-surface-hover rounded transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreate}
                  className="px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded transition-colors"
                >
                  Create
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

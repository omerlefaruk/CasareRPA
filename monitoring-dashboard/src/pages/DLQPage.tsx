import { useEffect, useState, useCallback } from 'react'
import { useApi } from '../api/ApiContext'
import type { DLQEntry } from '../types'
import { formatDistanceToNow } from 'date-fns'
import { RefreshCw, RotateCcw, Trash2, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react'

interface Props {
  tenantId: string | null
  workspaceId: string | null
}

export default function DLQPage({ tenantId, workspaceId }: Props) {
  const api = useApi()
  const [entries, setEntries] = useState<DLQEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())

  const loadEntries = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.dlq.list({
        tenant_id: tenantId || undefined,
        workspace_id: workspaceId || undefined,
      })
      setEntries(response.entries as DLQEntry[])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load DLQ entries')
    } finally {
      setLoading(false)
    }
  }, [api.dlq, tenantId, workspaceId])

  useEffect(() => {
    loadEntries()
  }, [loadEntries])

  const handleRetry = async (entryId: string) => {
    try {
      await api.dlq.retry(entryId)
      setEntries((prev) => prev.filter((e) => e.entry_id !== entryId))
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to retry entry')
    }
  }

  const handlePurge = async (entryId: string) => {
    if (!confirm('Permanently delete this entry?')) return
    try {
      await api.dlq.purge(entryId)
      setEntries((prev) => prev.filter((e) => e.entry_id !== entryId))
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to purge entry')
    }
  }

  const handleBulkRetry = async () => {
    if (selectedIds.size === 0) return
    if (!confirm(`Retry ${selectedIds.size} selected entries?`)) return

    try {
      await Promise.all(Array.from(selectedIds).map((id) => api.dlq.retry(id)))
      setEntries((prev) => prev.filter((e) => !selectedIds.has(e.entry_id)))
      setSelectedIds(new Set())
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to retry entries')
    }
  }

  const handleBulkPurge = async () => {
    if (selectedIds.size === 0) return
    if (!confirm(`Permanently delete ${selectedIds.size} selected entries?`)) return

    try {
      await Promise.all(Array.from(selectedIds).map((id) => api.dlq.purge(id)))
      setEntries((prev) => prev.filter((e) => !selectedIds.has(e.entry_id)))
      setSelectedIds(new Set())
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to purge entries')
    }
  }

  const toggleSelect = (entryId: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(entryId)) {
        next.delete(entryId)
      } else {
        next.add(entryId)
      }
      return next
    })
  }

  const toggleSelectAll = () => {
    if (selectedIds.size === entries.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(entries.map((e) => e.entry_id)))
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold">Dead Letter Queue</h2>
          {entries.length > 0 && (
            <span className="px-2 py-1 bg-error/20 text-error rounded text-sm">
              {entries.length} items
            </span>
          )}
        </div>
        <div className="flex items-center gap-4">
          {selectedIds.size > 0 && (
            <>
              <button
                onClick={handleBulkRetry}
                className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded text-sm transition-colors"
              >
                <RotateCcw className="w-4 h-4" />
                Retry Selected ({selectedIds.size})
              </button>
              <button
                onClick={handleBulkPurge}
                className="flex items-center gap-2 px-4 py-2 bg-error hover:bg-error/80 rounded text-sm transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                Purge Selected
              </button>
            </>
          )}
          <button
            onClick={loadEntries}
            className="flex items-center gap-2 px-4 py-2 bg-surface hover:bg-surface-hover rounded text-sm transition-colors"
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

      {/* Empty State */}
      {!loading && entries.length === 0 && (
        <div className="text-center py-16">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-success/20 rounded-full mb-4">
            <AlertTriangle className="w-8 h-8 text-success" />
          </div>
          <h3 className="text-xl font-semibold mb-2">All Clear!</h3>
          <p className="text-gray-400">No failed jobs in the dead letter queue.</p>
        </div>
      )}

      {/* DLQ Entries */}
      {!loading && entries.length > 0 && (
        <div className="space-y-2">
          {/* Select All Header */}
          <div className="flex items-center gap-3 px-4 py-2 bg-surface rounded-t-lg border border-gray-700 border-b-0">
            <input
              type="checkbox"
              checked={selectedIds.size === entries.length}
              onChange={toggleSelectAll}
              className="w-4 h-4 rounded"
            />
            <span className="text-sm text-gray-400">
              {selectedIds.size > 0
                ? `${selectedIds.size} of ${entries.length} selected`
                : 'Select all'}
            </span>
          </div>

          {/* Entries List */}
          <div className="bg-surface-elevated rounded-b-lg border border-gray-700 divide-y divide-gray-700/50">
            {entries.map((entry) => (
              <div key={entry.entry_id}>
                <div className="flex items-start gap-4 p-4">
                  <input
                    type="checkbox"
                    checked={selectedIds.has(entry.entry_id)}
                    onChange={() => toggleSelect(entry.entry_id)}
                    className="w-4 h-4 rounded mt-1"
                  />

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3">
                      <AlertTriangle className="w-4 h-4 text-error flex-shrink-0" />
                      <span className="font-mono text-sm">{entry.job_id}</span>
                      <span className="px-2 py-0.5 bg-surface rounded text-xs text-gray-400">
                        Attempt {entry.retry_count + 1}
                      </span>
                    </div>

                    <div className="mt-2 text-sm text-error bg-error/10 rounded p-2 font-mono overflow-x-auto">
                      {entry.error_message}
                    </div>

                    <div className="mt-2 flex flex-wrap gap-4 text-sm text-gray-400">
                      <span>
                        Workflow:{' '}
                        <span className="font-mono text-gray-300">
                          {entry.workflow_id.slice(0, 8)}
                        </span>
                      </span>
                      <span>
                        Failed:{' '}
                        {formatDistanceToNow(new Date(entry.failed_at), { addSuffix: true })}
                      </span>
                      {entry.original_created_at && (
                        <span>
                          Original:{' '}
                          {formatDistanceToNow(new Date(entry.original_created_at), {
                            addSuffix: true,
                          })}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      onClick={() =>
                        setExpandedId(expandedId === entry.entry_id ? null : entry.entry_id)
                      }
                      className="p-2 hover:bg-surface rounded transition-colors"
                      title="View Details"
                    >
                      {expandedId === entry.entry_id ? (
                        <ChevronUp className="w-4 h-4 text-gray-400" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-gray-400" />
                      )}
                    </button>
                    <button
                      onClick={() => handleRetry(entry.entry_id)}
                      className="p-2 hover:bg-primary-600/20 rounded transition-colors"
                      title="Retry"
                    >
                      <RotateCcw className="w-4 h-4 text-primary-400" />
                    </button>
                    <button
                      onClick={() => handlePurge(entry.entry_id)}
                      className="p-2 hover:bg-error/20 rounded transition-colors"
                      title="Purge"
                    >
                      <Trash2 className="w-4 h-4 text-error" />
                    </button>
                  </div>
                </div>

                {/* Expanded Details */}
                {expandedId === entry.entry_id && (
                  <div className="px-4 pb-4 pl-12">
                    <div className="bg-surface rounded p-4 space-y-4">
                      <div>
                        <h4 className="text-sm font-semibold text-gray-400 mb-2">Full Error</h4>
                        <pre className="text-sm text-error overflow-x-auto whitespace-pre-wrap">
                          {entry.error_stack || entry.error_message}
                        </pre>
                      </div>

                      {entry.input && Object.keys(entry.input).length > 0 && (
                        <div>
                          <h4 className="text-sm font-semibold text-gray-400 mb-2">Input</h4>
                          <pre className="text-sm overflow-x-auto">
                            {JSON.stringify(entry.input, null, 2)}
                          </pre>
                        </div>
                      )}

                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-400">Entry ID:</span>
                          <p className="font-mono">{entry.entry_id}</p>
                        </div>
                        <div>
                          <span className="text-gray-400">Job ID:</span>
                          <p className="font-mono">{entry.job_id}</p>
                        </div>
                        <div>
                          <span className="text-gray-400">Workflow ID:</span>
                          <p className="font-mono">{entry.workflow_id}</p>
                        </div>
                        <div>
                          <span className="text-gray-400">Retry Count:</span>
                          <p>{entry.retry_count}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

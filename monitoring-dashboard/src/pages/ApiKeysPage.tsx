import { useEffect, useState, useCallback } from 'react'
import { useApi } from '../api/ApiContext'
import type { ApiKey } from '../types'
import { formatDistanceToNow } from 'date-fns'
import { RefreshCw, Plus, Trash2, Copy, Key, RotateCcw } from 'lucide-react'

interface Props {
  tenantId: string | null
  workspaceId: string | null
}

export default function ApiKeysPage({ tenantId }: Props) {
  const api = useApi()
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [newKeyResult, setNewKeyResult] = useState<string | null>(null)

  // Create form
  const [newKey, setNewKey] = useState({
    name: '',
    robot_id: '',
    expires_in_days: 365,
  })

  const loadApiKeys = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.apiKeys.list({
        tenant_id: tenantId || undefined,
      })
      setApiKeys(response.api_keys as ApiKey[])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load API keys')
    } finally {
      setLoading(false)
    }
  }, [api.apiKeys, tenantId])

  useEffect(() => {
    loadApiKeys()
  }, [loadApiKeys])

  const handleCreate = async () => {
    try {
      const result = await api.apiKeys.create({
        tenant_id: tenantId || 'default',
        name: newKey.name,
        robot_id: newKey.robot_id || undefined,
        expires_in_days: newKey.expires_in_days,
      })
      setNewKeyResult(result.api_key)
      setShowCreate(false)
      setNewKey({ name: '', robot_id: '', expires_in_days: 365 })
      loadApiKeys()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create API key')
    }
  }

  const handleRevoke = async (keyId: string) => {
    if (!confirm('Revoke this API key? This action cannot be undone.')) return
    try {
      await api.apiKeys.revoke(keyId)
      setApiKeys((prev) =>
        prev.map((k) => (k.key_id === keyId ? { ...k, revoked: true } : k))
      )
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to revoke API key')
    }
  }

  const handleRotate = async (keyId: string) => {
    if (!confirm('Rotate this API key? The old key will be immediately invalidated.')) return
    try {
      const result = await api.apiKeys.rotate(keyId)
      setNewKeyResult(result.api_key)
      loadApiKeys()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to rotate API key')
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    alert('Copied to clipboard')
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">API Keys</h2>
        <div className="flex items-center gap-4">
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 bg-success hover:bg-success/80 rounded text-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            New API Key
          </button>
          <button
            onClick={loadApiKeys}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded text-sm transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* New Key Result */}
      {newKeyResult && (
        <div className="bg-success/20 border border-success rounded p-4 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-semibold text-success">API Key Created!</p>
              <p className="text-sm text-gray-400 mt-1">
                Copy this key now. You won&apos;t be able to see it again.
              </p>
            </div>
            <button
              onClick={() => setNewKeyResult(null)}
              className="text-gray-400 hover:text-white"
            >
              ×
            </button>
          </div>
          <div className="mt-3 flex items-center gap-2">
            <code className="flex-1 bg-surface p-2 rounded font-mono text-sm break-all">
              {newKeyResult}
            </code>
            <button
              onClick={() => copyToClipboard(newKeyResult)}
              className="p-2 bg-surface hover:bg-surface-hover rounded transition-colors"
            >
              <Copy className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

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

      {/* API Keys Table */}
      {!loading && (
        <div className="bg-surface-elevated rounded-lg border border-gray-700 overflow-hidden">
          <table className="w-full">
            <thead className="bg-surface">
              <tr className="text-left text-sm text-gray-400 border-b border-gray-700">
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Key Prefix</th>
                <th className="px-4 py-3">Robot</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Expires</th>
                <th className="px-4 py-3">Last Used</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {apiKeys.map((key) => (
                <tr
                  key={key.key_id}
                  className={`border-b border-gray-700/50 ${
                    key.revoked ? 'opacity-50' : ''
                  }`}
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Key className="w-4 h-4 text-gray-400" />
                      <span className="font-medium">{key.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <code className="text-sm text-gray-400">{key.key_prefix}...</code>
                  </td>
                  <td className="px-4 py-3">
                    {key.robot_id ? (
                      <span className="font-mono text-sm text-gray-300">
                        {key.robot_id.slice(0, 8)}
                      </span>
                    ) : (
                      <span className="text-gray-500">All robots</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {key.revoked ? (
                      <span className="px-2 py-0.5 bg-error/20 text-error rounded text-xs">
                        Revoked
                      </span>
                    ) : new Date(key.expires_at) < new Date() ? (
                      <span className="px-2 py-0.5 bg-warning/20 text-warning rounded text-xs">
                        Expired
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 bg-success/20 text-success rounded text-xs">
                        Active
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-400">
                    {formatDistanceToNow(new Date(key.expires_at), { addSuffix: true })}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-400">
                    {key.last_used_at
                      ? formatDistanceToNow(new Date(key.last_used_at), { addSuffix: true })
                      : 'Never'}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      {!key.revoked && (
                        <>
                          <button
                            onClick={() => handleRotate(key.key_id)}
                            className="p-1.5 hover:bg-primary-600/20 rounded transition-colors"
                            title="Rotate Key"
                          >
                            <RotateCcw className="w-4 h-4 text-primary-400" />
                          </button>
                          <button
                            onClick={() => handleRevoke(key.key_id)}
                            className="p-1.5 hover:bg-error/20 rounded transition-colors"
                            title="Revoke"
                          >
                            <Trash2 className="w-4 h-4 text-error" />
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {apiKeys.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-gray-500">
                    No API keys found. Create one to allow robots to authenticate.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={() => setShowCreate(false)}
        >
          <div
            className="bg-surface-elevated rounded-lg p-6 max-w-md w-full mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-xl font-bold mb-4">Create API Key</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Name</label>
                <input
                  type="text"
                  value={newKey.name}
                  onChange={(e) => setNewKey({ ...newKey, name: e.target.value })}
                  className="w-full bg-surface border border-gray-600 rounded px-3 py-2"
                  placeholder="Production Robot Key"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  Robot ID (optional - leave empty for all robots)
                </label>
                <input
                  type="text"
                  value={newKey.robot_id}
                  onChange={(e) => setNewKey({ ...newKey, robot_id: e.target.value })}
                  className="w-full bg-surface border border-gray-600 rounded px-3 py-2 font-mono"
                  placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Expires In</label>
                <select
                  value={newKey.expires_in_days}
                  onChange={(e) =>
                    setNewKey({ ...newKey, expires_in_days: parseInt(e.target.value) })
                  }
                  className="w-full bg-surface border border-gray-600 rounded px-3 py-2"
                >
                  <option value={30}>30 days</option>
                  <option value={90}>90 days</option>
                  <option value={180}>180 days</option>
                  <option value={365}>1 year</option>
                  <option value={730}>2 years</option>
                </select>
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
                  disabled={!newKey.name}
                  className="px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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

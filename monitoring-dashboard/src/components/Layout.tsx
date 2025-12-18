import { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import {
  Bot,
  Briefcase,
  Calendar,
  Key,
  BarChart3,
  AlertTriangle,
  Activity,
} from 'lucide-react'
import { useQueueWebSocket } from '../hooks/useWebSocket'
import { useState } from 'react'

interface LayoutProps {
  children: ReactNode
  tenantId: string | null
  workspaceId: string | null
  onTenantChange: (id: string | null) => void
  onWorkspaceChange: (id: string | null) => void
}

const navItems = [
  { path: '/robots', label: 'Robots', icon: Bot },
  { path: '/jobs', label: 'Jobs', icon: Briefcase },
  { path: '/schedules', label: 'Schedules', icon: Calendar },
  { path: '/api-keys', label: 'API Keys', icon: Key },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
  { path: '/dlq', label: 'Dead Letter Queue', icon: AlertTriangle },
]

export default function Layout({
  children,
  tenantId,
  workspaceId,
  onTenantChange,
  onWorkspaceChange,
}: LayoutProps) {
  const [queueDepth, setQueueDepth] = useState({ pending: 0, running: 0 })
  const { isConnected } = useQueueWebSocket((update) => {
    setQueueDepth({
      pending: update.data.pending,
      running: update.data.running,
    })
  })

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-surface-elevated flex flex-col">
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-gray-700">
          <Bot className="w-8 h-8 text-primary-500 mr-3" />
          <span className="text-xl font-bold">CasareRPA</span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4">
          {navItems.map(({ path, label, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              className={({ isActive }) =>
                `flex items-center px-6 py-3 text-sm transition-colors ${
                  isActive
                    ? 'bg-primary-600/20 text-primary-400 border-r-2 border-primary-500'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-surface-hover'
                }`
              }
            >
              <Icon className="w-5 h-5 mr-3" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Connection Status */}
        <div className="p-4 border-t border-gray-700">
          <div className="flex items-center text-sm">
            <Activity
              className={`w-4 h-4 mr-2 ${isConnected ? 'text-success' : 'text-error'}`}
            />
            <span className={isConnected ? 'text-success' : 'text-error'}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          <div className="mt-2 text-xs text-gray-500">
            Queue: {queueDepth.pending} pending, {queueDepth.running} running
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="h-16 bg-surface-elevated border-b border-gray-700 flex items-center justify-between px-6">
          <h1 className="text-lg font-semibold">Fleet Dashboard</h1>

          {/* Tenant/Workspace filters */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-400">Tenant:</label>
              <select
                value={tenantId || ''}
                onChange={(e) => onTenantChange(e.target.value || null)}
                className="bg-surface border border-gray-600 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-primary-500"
              >
                <option value="">All Tenants</option>
                {/* TODO: Populate from API */}
              </select>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-400">Workspace:</label>
              <select
                value={workspaceId || ''}
                onChange={(e) => onWorkspaceChange(e.target.value || null)}
                className="bg-surface border border-gray-600 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-primary-500"
              >
                <option value="">All Workspaces</option>
                {/* TODO: Populate from API */}
              </select>
            </div>
          </div>
        </header>

        {/* Page content */}
        <div className="flex-1 overflow-auto p-6">{children}</div>
      </main>
    </div>
  )
}

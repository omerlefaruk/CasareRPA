import { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import RobotsPage from './pages/RobotsPage'
import JobsPage from './pages/JobsPage'
import SchedulesPage from './pages/SchedulesPage'
import ApiKeysPage from './pages/ApiKeysPage'
import AnalyticsPage from './pages/AnalyticsPage'
import DLQPage from './pages/DLQPage'
import { ApiProvider } from './api/ApiContext'

function App() {
  const [tenantId, setTenantId] = useState<string | null>(null)
  const [workspaceId, setWorkspaceId] = useState<string | null>(null)

  return (
    <ApiProvider>
      <BrowserRouter>
        <Layout
          tenantId={tenantId}
          workspaceId={workspaceId}
          onTenantChange={setTenantId}
          onWorkspaceChange={setWorkspaceId}
        >
          <Routes>
            <Route path="/" element={<Navigate to="/robots" replace />} />
            <Route path="/robots" element={<RobotsPage tenantId={tenantId} workspaceId={workspaceId} />} />
            <Route path="/jobs" element={<JobsPage tenantId={tenantId} workspaceId={workspaceId} />} />
            <Route path="/schedules" element={<SchedulesPage tenantId={tenantId} workspaceId={workspaceId} />} />
            <Route path="/api-keys" element={<ApiKeysPage tenantId={tenantId} workspaceId={workspaceId} />} />
            <Route path="/analytics" element={<AnalyticsPage tenantId={tenantId} workspaceId={workspaceId} />} />
            <Route path="/dlq" element={<DLQPage tenantId={tenantId} workspaceId={workspaceId} />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ApiProvider>
  )
}

export default App

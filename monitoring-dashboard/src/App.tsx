import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import FleetOverview from './pages/FleetOverview'
import WorkflowExecution from './pages/WorkflowExecution'
import RobotDetail from './pages/RobotDetail'
import Schedules from './pages/Schedules'
import Analytics from './pages/Analytics'

/**
 * App - Root component with routing configuration.
 *
 * Routes:
 * - / : Dashboard (unified home)
 * - /fleet : FleetOverview (robot management)
 * - /robots/:robotId : RobotDetail (single robot view)
 * - /jobs : WorkflowExecution (job queue)
 * - /schedules : Schedules (schedule management)
 * - /analytics : Analytics (metrics and reports)
 *
 * Note: DashboardLayout is applied within each page component
 * to allow page-specific customization of title, subtitle, etc.
 */
function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/fleet" element={<FleetOverview />} />
      <Route path="/robots/:robotId" element={<RobotDetail />} />
      <Route path="/jobs" element={<WorkflowExecution />} />
      <Route path="/schedules" element={<Schedules />} />
      <Route path="/analytics" element={<Analytics />} />
    </Routes>
  )
}

export default App

import { Routes, Route, Link, useLocation } from 'react-router-dom'
import FleetOverview from './pages/FleetOverview'
import WorkflowExecution from './pages/WorkflowExecution'
import RobotDetail from './pages/RobotDetail'
import Analytics from './pages/Analytics'
import './App.css'

function App() {
  const location = useLocation()

  const isActive = (path: string) => {
    return location.pathname === path ? 'nav-link active' : 'nav-link'
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>CasareRPA Monitoring Dashboard</h1>
        <nav className="app-nav">
          <Link to="/" className={isActive('/')}>
            Fleet Overview
          </Link>
          <Link to="/workflows" className={isActive('/workflows')}>
            Workflow Execution
          </Link>
          <Link to="/analytics" className={isActive('/analytics')}>
            Analytics
          </Link>
        </nav>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<FleetOverview />} />
          <Route path="/workflows" element={<WorkflowExecution />} />
          <Route path="/robots/:robotId" element={<RobotDetail />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </main>
    </div>
  )
}

export default App

import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import DashboardPage from './pages/DashboardPage'
import VendorsPage from './pages/VendorsPage'
import PlansPage from './pages/PlansPage'
import UsagePage from './pages/UsagePage'
import AlertsPage from './pages/AlertsPage'
import SettingsPage from './pages/SettingsPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="vendors" element={<VendorsPage />} />
        <Route path="plans" element={<PlansPage />} />
        <Route path="usage" element={<UsagePage />} />
        <Route path="alerts" element={<AlertsPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  )
}

export default App

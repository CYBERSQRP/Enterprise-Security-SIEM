import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import { LoginPage } from './pages/LoginPage';
import { DashboardLayout } from './layouts/DashboardLayout';
import { DashboardPage } from './pages/DashboardPage';
import { EventsPage } from './pages/EventsPage';
import { AlertsPage } from './pages/AlertsPage';
import { IncidentsPage } from './pages/IncidentsPage';
import { ThreatIntelPage } from './pages/ThreatIntelPage';
import { ForensicsPage } from './pages/ForensicsPage';
import { CollaborationPage } from './pages/CollaborationPage';
import { SupplyChainPage } from './pages/SupplyChainPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { ConfigurationPage } from './pages/ConfigurationPage';
import { ToastProvider } from './components/ui/Toast';

function App() {
  const { isAuthenticated } = useAuthStore();

  return (
    <ToastProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/*"
            element={
              isAuthenticated ? (
                <DashboardLayout>
                  <Routes>
                    <Route path="/" element={<DashboardPage />} />
                    <Route path="/events" element={<EventsPage />} />
                    <Route path="/alerts" element={<AlertsPage />} />
                    <Route path="/incidents" element={<IncidentsPage />} />
                    <Route path="/threat-intel" element={<ThreatIntelPage />} />
                    <Route path="/forensics" element={<ForensicsPage />} />
                    <Route path="/collaboration" element={<CollaborationPage />} />
                    <Route path="/supply-chain" element={<SupplyChainPage />} />
                    <Route path="/analytics" element={<AnalyticsPage />} />
                    <Route path="/config" element={<ConfigurationPage />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
                </DashboardLayout>
              ) : (
                <Navigate to="/login" replace />
              )
            }
          />
        </Routes>
      </Router>
    </ToastProvider>
  );
}

export default App;

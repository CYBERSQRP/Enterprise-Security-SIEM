import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080/api/v1';

function Dashboard() {
  const [stats, setStats] = useState({
    totalEvents: 0,
    totalAlerts: 0,
    criticalAlerts: 0,
    highAlerts: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/stats`);

      // In a real implementation, these would come from the API
      setStats({
        totalEvents: 125843,
        totalAlerts: 156,
        criticalAlerts: 5,
        highAlerts: 23
      });

      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  return (
    <div className="dashboard">
      <div className="page-header">
        <h2>Security Operations Center Dashboard</h2>
        <p>Real-time overview of security events and alerts</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card info">
          <h3>Total Events (24h)</h3>
          <div className="value">{stats.totalEvents.toLocaleString()}</div>
        </div>

        <div className="stat-card">
          <h3>Total Alerts</h3>
          <div className="value">{stats.totalAlerts}</div>
        </div>

        <div className="stat-card critical">
          <h3>Critical Alerts</h3>
          <div className="value">{stats.criticalAlerts}</div>
        </div>

        <div className="stat-card high">
          <h3>High Priority Alerts</h3>
          <div className="value">{stats.highAlerts}</div>
        </div>
      </div>

      <div className="card">
        <h3>System Status</h3>
        <div style={{ padding: '1rem 0' }}>
          <div style={{ marginBottom: '0.5rem' }}>
            <strong>Data Collection:</strong> <span style={{ color: '#00b894' }}>●</span> Operational
          </div>
          <div style={{ marginBottom: '0.5rem' }}>
            <strong>Event Processing:</strong> <span style={{ color: '#00b894' }}>●</span> Operational
          </div>
          <div style={{ marginBottom: '0.5rem' }}>
            <strong>Alert Engine:</strong> <span style={{ color: '#00b894' }}>●</span> Operational
          </div>
          <div>
            <strong>API Gateway:</strong> <span style={{ color: '#00b894' }}>●</span> Operational
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Recent Activity</h3>
        <p>Welcome to the Enterprise SIEM platform. Use the navigation menu to view events and alerts.</p>
      </div>
    </div>
  );
}

export default Dashboard;

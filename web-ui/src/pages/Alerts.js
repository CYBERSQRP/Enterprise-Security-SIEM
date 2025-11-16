import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080/api/v1';

function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/alerts`);

      // Extract hits from Elasticsearch response
      let alertList = [];
      if (response.data.hits && response.data.hits.hits) {
        alertList = response.data.hits.hits.map(hit => hit._source);
      }

      setAlerts(alertList);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching alerts:', err);
      setError(err.message);
      setLoading(false);
      // Set empty array for demonstration
      setAlerts([]);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const getSeverityBadgeClass = (severity) => {
    const severityMap = {
      'critical': 'critical',
      'high': 'high',
      'medium': 'medium',
      'low': 'low',
      'info': 'info'
    };
    return severityMap[severity?.toLowerCase()] || 'info';
  };

  const getStatusBadgeClass = (status) => {
    const statusMap = {
      'new': 'new',
      'investigating': 'investigating',
      'resolved': 'resolved',
      'false_positive': 'info'
    };
    return statusMap[status?.toLowerCase()] || 'new';
  };

  if (loading) {
    return <div className="loading">Loading alerts...</div>;
  }

  return (
    <div className="alerts">
      <div className="page-header">
        <h2>Security Alerts</h2>
        <p>Monitor and manage security alerts</p>
      </div>

      {error && (
        <div className="error">
          Error loading alerts: {error}
          <p>Make sure the API Gateway is running and Elasticsearch is accessible.</p>
        </div>
      )}

      <div className="stats-grid">
        <div className="stat-card critical">
          <h3>Critical</h3>
          <div className="value">
            {alerts.filter(a => a.severity === 'critical').length}
          </div>
        </div>
        <div className="stat-card high">
          <h3>High</h3>
          <div className="value">
            {alerts.filter(a => a.severity === 'high').length}
          </div>
        </div>
        <div className="stat-card medium">
          <h3>Medium</h3>
          <div className="value">
            {alerts.filter(a => a.severity === 'medium').length}
          </div>
        </div>
        <div className="stat-card info">
          <h3>Low/Info</h3>
          <div className="value">
            {alerts.filter(a => a.severity === 'low' || a.severity === 'info').length}
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Active Alerts</h3>
        {alerts.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
            <p>No alerts found.</p>
            <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
              Alerts will appear here when detection rules are triggered.
            </p>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Title</th>
                  <th>Severity</th>
                  <th>Status</th>
                  <th>Risk Score</th>
                  <th>Rule</th>
                  <th>Assigned To</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((alert, index) => (
                  <tr key={alert.alert_id || index}>
                    <td className="timestamp">
                      {formatTimestamp(alert.timestamp)}
                    </td>
                    <td>{alert.title || 'Untitled Alert'}</td>
                    <td>
                      <span className={`badge ${getSeverityBadgeClass(alert.severity)}`}>
                        {alert.severity || 'INFO'}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${getStatusBadgeClass(alert.status)}`}>
                        {alert.status || 'NEW'}
                      </span>
                    </td>
                    <td>{alert.risk_score || 0}</td>
                    <td>{alert.rule?.name || 'N/A'}</td>
                    <td>{alert.assignment?.assigned_to || 'Unassigned'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default Alerts;

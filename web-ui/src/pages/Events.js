import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080/api/v1';

function Events() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_URL}/events/search`, {
        query: {
          match_all: {}
        },
        size: 50,
        sort: [
          { timestamp: 'desc' }
        ]
      });

      const eventList = response.data.hits || [];
      setEvents(eventList);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching events:', err);
      setError(err.message);
      setLoading(false);
      // Set some mock data for demonstration
      setEvents([]);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  if (loading) {
    return <div className="loading">Loading events...</div>;
  }

  return (
    <div className="events">
      <div className="page-header">
        <h2>Security Events</h2>
        <p>View and search security events from all sources</p>
      </div>

      <div className="search-box">
        <input
          type="text"
          placeholder="Search events... (e.g., source.ip:10.0.1.100)"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              fetchEvents();
            }
          }}
        />
      </div>

      {error && (
        <div className="error">
          Error loading events: {error}
          <p>Make sure the API Gateway is running and Elasticsearch is accessible.</p>
        </div>
      )}

      <div className="card">
        <h3>Event Log</h3>
        {events.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
            <p>No events found.</p>
            <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
              Events will appear here once data collection is active.
            </p>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Source</th>
                  <th>Event Type</th>
                  <th>Action</th>
                  <th>Severity</th>
                  <th>User</th>
                </tr>
              </thead>
              <tbody>
                {events.map((event, index) => (
                  <tr key={event.event_id || index}>
                    <td className="timestamp">
                      {formatTimestamp(event.timestamp)}
                    </td>
                    <td>
                      {event.source?.hostname || event.source?.ip || 'Unknown'}
                    </td>
                    <td>{event.event?.type || 'N/A'}</td>
                    <td>{event.event?.action || 'N/A'}</td>
                    <td>
                      <span className={`badge ${event.event?.severity || 'info'}`}>
                        {event.event?.severity || 'INFO'}
                      </span>
                    </td>
                    <td>{event.user?.username || 'N/A'}</td>
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

export default Events;

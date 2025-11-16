# Web Portal Integration Guide - Quick Reference

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────┐
│                    WEB PORTAL (React)                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Dashboard │ Alerts │ Incidents │ Threats │ Reports │ Config │
│                                                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              REST API + WebSocket Gateway                    │
│  (Authentication, Rate Limiting, Routing)                   │
└──────────┬─────────┬─────────┬──────────┬────────────────────┘
           │         │         │          │
      ┌────▼────┐┌──▼───┐┌────▼──┐┌─────▼──┐
      │ Threat  ││Supply││Forensic│Collabor│
      │ Intel   ││Chain ││Collect.│ation   │
      │(Go)     ││(Py)  ││ (Py)   ║(Go)    │
      └────┬────┘└──┬───┘└────┬──┘└─────┬──┘
           │        │         │         │
      ┌────▴────┬───▴─────┬───▴──┬─────▴──┐
      │  Kafka  │ Redis   │  PostgreSQL  │
      │  Topics │ Cache   │  Metadata    │
      └─────────┴─────────┴──────────────┘
           │
      ┌────▼──────────────┐
      │  Elasticsearch    │
      │  (Hot Storage)    │
      └───────────────────┘
```

## 10 Key Integration Points

### 1. Authentication & Authorization
**Endpoint**: API Gateway
**Methods**: JWT, OAuth 2.0, API Keys, SAML/SSO
**Flow**:
1. User logs in to web portal
2. Portal generates JWT token via `/auth/login`
3. Token included in all API requests (Authorization: Bearer <token>)
4. API Gateway validates token and enforces RBAC

**Implementation**:
```typescript
// Portal Auth Integration
const authService = {
  login: async (credentials) => {
    const response = await fetch('http://api-gateway:8080/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials)
    });
    return response.json(); // Returns { token, user_id, roles }
  },
  
  makeAuthenticatedRequest: async (endpoint, options = {}) => {
    return fetch(endpoint, {
      ...options,
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      }
    });
  }
};
```

### 2. Real-Time Events & Alerts
**WebSocket Endpoint**: `ws://localhost:8083/ws/events`
**Use Case**: Display live security events and alerts
**Data Flow**:
1. Portal connects to WebSocket
2. Filters events by severity/type
3. Updates dashboard in real-time

**Implementation**:
```typescript
const eventSocket = new WebSocket('ws://api.siem/v1/stream/events');
eventSocket.onmessage = (event) => {
  const alert = JSON.parse(event.data);
  // Update dashboard with new alert
  updateDashboard(alert);
};
```

### 3. Event Search & Analytics
**Endpoints**: 
- `POST /events/search` - Advanced search with filters
- `GET /events/{event_id}` - Specific event details
- `GET /analytics/statistics` - Aggregated metrics

**Use Case**: Event search interface, analytics dashboard
**Example Query**:
```json
{
  "query": {
    "bool": {
      "must": [
        {"match": {"event.type": "authentication"}},
        {"range": {"timestamp": {"gte": "2024-11-16T00:00:00Z"}}}
      ]
    }
  },
  "aggregations": {
    "by_severity": {"terms": {"field": "severity"}}
  },
  "size": 100
}
```

### 4. Alert Management Dashboard
**Endpoints**:
- `GET /alerts` - List all alerts (filterable)
- `PATCH /alerts/{alert_id}` - Update alert status
- `POST /alerts/{alert_id}/notes` - Add investigative notes

**Portal Features**:
- Alert list with filtering (severity, status, date)
- Alert detail view with timeline
- Bulk operations (acknowledge, assign, resolve)

**Alert Lifecycle**:
```
new → acknowledged → investigating → resolved
                          ↓
                    false_positive
```

### 5. Incident Management
**Endpoints**:
- `POST /incidents` - Create incident from alerts
- `PATCH /incidents/{incident_id}` - Update incident
- `POST /incidents/{id}/evidence` - Attach forensic evidence
- `POST /incidents/{id}/playbooks/{pid}/execute` - Run automated responses

**Portal Integration**:
```typescript
// Create incident from alert
const createIncidentFromAlert = async (alertId) => {
  const response = await fetch('/incidents', {
    method: 'POST',
    body: JSON.stringify({
      title: 'Incident from Alert ' + alertId,
      alert_ids: [alertId],
      severity: 'high'
    })
  });
  return response.json();
};
```

### 6. Real-Time Collaboration
**WebSocket Endpoint**: `ws://localhost:8083/ws/sessions/{session_id}`
**Features**:
- Multi-user investigation sessions
- Real-time chat and annotations
- Live cursor tracking
- Shared findings

**Join Session**:
```typescript
const joinColaborationSession = async (incidentId) => {
  // 1. Create or get session
  const session = await fetch(`/collaboration/sessions/${incidentId}`);
  
  // 2. Connect WebSocket
  const ws = new WebSocket(
    `ws://api.siem:8083/ws/sessions/${session.id}?user_id=${userId}`
  );
  
  // 3. Listen for messages
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    handleCollaborationMessage(message);
  };
};
```

### 7. Threat Intelligence Lookup
**Endpoints**:
- `POST /threat-intel/iocs/check` - Batch IOC lookup
- `GET /threat-intel/feeds` - List available threat feeds
- `POST /threat-intel/iocs` - Add custom IOCs

**Portal Use Cases**:
- Check if IP/domain is malicious during investigation
- Display threat context in alerts
- Custom IOC database for organization

**Example**:
```typescript
const checkThreatIntel = async (ioc) => {
  const response = await fetch('/threat-intel/iocs/check', {
    method: 'POST',
    body: JSON.stringify({
      iocs: [{ type: 'ip', value: ioc }]
    })
  });
  const { results } = await response.json();
  return results[0]; // { is_malicious, threat_level, sources }
};
```

### 8. Custom Dashboards & Reports
**Endpoints**:
- `POST /dashboards` - Create custom dashboard
- `GET /dashboards/{id}` - Get dashboard config
- `POST /reports/generate` - Generate report

**Dashboard Widget Types**:
- Metrics (number, gauge, trend)
- Charts (bar, line, pie)
- Tables (events, alerts)
- Heatmaps (source IPs, users)
- Time series (trends over time)

**Report Types**: compliance, executive, incident, custom

### 9. Detection Rules Management
**Endpoints**:
- `POST /rules` - Create custom detection rule
- `GET /rules` - List all rules
- `POST /rules/{id}/test` - Test rule on historical data

**Rule Example**:
```json
{
  "name": "Failed Login Attempts",
  "type": "threshold",
  "logic": {
    "query": "event.type:authentication AND action:failed",
    "threshold": {
      "count": 5,
      "timeframe": "5m",
      "group_by": ["user.username"]
    }
  },
  "actions": {
    "create_alert": true,
    "alert_severity": "medium"
  }
}
```

### 10. System Configuration
**Endpoints**:
- `GET /config` - Get system configuration
- `PATCH /config` - Update settings
- `GET /config/data-sources` - List data sources

**Configurable Items**:
- Retention policies (hot/warm/cold)
- Notification channels (email, Slack)
- Alert escalation rules
- Data source connections

---

## Service Port Reference

```
Service                  Port    Endpoint
─────────────────────────────────────────────────────────
API Gateway              8080    http://localhost:8080
Threat Intel             8080    http://localhost:8080/api/v1/feeds
Supply Chain Monitor     8081    http://localhost:8081/api/v1/vendors
Forensics Collector      8082    http://localhost:8082/api/v1/evidence
Collaboration Hub        8083    ws://localhost:8083/ws/sessions
Predictive Analytics     8084    http://localhost:8084/api/v1/models
─────────────────────────────────────────────────────────
Grafana Dashboards       3001    http://localhost:3001
Kibana Logs              5601    http://localhost:5601
Jaeger Tracing           16686   http://localhost:16686
```

---

## SDK Usage Examples

### Python SDK
```python
from siem_sdk import SIEMClient

client = SIEMClient(
    api_url="http://api.siem/v1",
    api_key="your-api-key"
)

# Search events
events = client.events.search(
    query="failed_login",
    time_range="last_24h"
)

# List alerts
alerts = client.alerts.list(status="new", severity="high")

# Check threat intel
threat_data = client.threat_intel.lookup_ioc("192.0.2.1", "ip")
```

### JavaScript SDK
```typescript
import { SIEMClient } from '@enterprise-siem/sdk';

const client = new SIEMClient({
  apiUrl: 'http://api.siem/v1',
  apiKey: 'your-api-key'
});

// Search events
const events = await client.events.search({
  query: 'failed_login',
  timeRange: 'last_24h'
});

// Create alert
const alert = await client.alerts.create({
  severity: 'high',
  title: 'Suspicious Activity',
  description: 'Multiple failed login attempts'
});
```

---

## Rate Limits & Quotas

| User Type | Requests/Hour | Concurrent |
|-----------|---------------|-----------|
| Standard  | 1,000         | 10        |
| Premium   | 10,000        | 100       |
| Service   | 50,000        | 500       |

---

## Authentication Flow Diagram

```
User                Portal              API Gateway         SIEM Backend
 │                   │                       │                  │
 ├─ Login ──────────→ │                       │                  │
 │                   ├─ POST /auth/login ──→ │                  │
 │                   │                       ├─ Validate ──────→ │
 │                   │                       │ ← JWT Token ─────┤
 │                   │ ← { token } ──────── │                  │
 │ ← Store token ──┤                       │                  │
 │                   │                       │                  │
 │ Search Events ──→ │                       │                  │
 │                   ├─ GET /events/search──→ │                  │
 │                   │  with Bearer Token    ├─ Verify Token ──→│
 │                   │                       │ ← Events ────────┤
 │ ← Display ────── │ ← Events ──────────── │                  │
```

---

## Error Handling

**Standard Error Response**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": [
      {
        "field": "severity",
        "message": "Must be one of: critical, high, medium, low, info"
      }
    ],
    "request_id": "req_123456",
    "timestamp": "2024-11-16T10:30:45Z"
  }
}
```

**HTTP Status Codes**:
- 200 OK - Success
- 201 Created - Resource created
- 400 Bad Request - Invalid input
- 401 Unauthorized - Authentication failed
- 403 Forbidden - Insufficient permissions
- 429 Too Many Requests - Rate limit exceeded
- 500 Internal Server Error - Server error

---

## Testing Integration Locally

```bash
# Start all services
docker-compose -f docker-compose-phase6.yaml up -d

# Wait for services to be healthy
sleep 30

# Test threat intel API
curl http://localhost:8080/api/v1/feeds

# Test alerts API
curl http://localhost:8080/alerts

# Test collaboration
wscat -c "ws://localhost:8083/ws/sessions/test-session"

# Run integration tests
pytest tests/test_phase6.py -v
```

---

## Performance Considerations

**Optimal Query Parameters**:
- Use pagination for large result sets: `limit=100, offset=0`
- Filter early: Use `from_time` and `to_time` to limit results
- Index frequently searched fields (source.ip, user.username, event.type)
- Use aggregations instead of processing all results client-side

**Caching Strategy**:
- Cache threat intel lookups (changes less frequently)
- Cache user/asset information (relatively stable)
- Cache dashboard configurations (user preferences)
- Don't cache real-time alert data

**Batch Operations**:
- Use bulk update for multiple alerts: `POST /alerts/bulk-update`
- Export for analysis instead of streaming all events

---

## Webhook Integration

**Register Webhook**:
```bash
curl -X POST http://localhost:8080/webhooks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "url": "https://your-portal.com/webhooks/siem",
    "events": ["alert.created", "incident.created"],
    "secret": "webhook_secret"
  }'
```

**Verify Webhook Signature**:
```python
import hmac
import hashlib

def verify_webhook(payload_bytes, signature, secret):
    expected_sig = hmac.new(
        secret.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, 'sha256=' + expected_sig)
```

---

## Next Steps for Portal Development

1. **Phase 1**: Authentication & Dashboard
   - Implement login/logout
   - Build event search interface
   - Create basic alert dashboard

2. **Phase 2**: Alert Management
   - Alert list with filtering
   - Alert detail view
   - Status updates and notes

3. **Phase 3**: Incident Management
   - Incident creation from alerts
   - Incident tracking and updates
   - Evidence attachment

4. **Phase 4**: Collaboration & Real-time
   - WebSocket integration for live updates
   - Collaboration sessions
   - Investigation annotations

5. **Phase 5**: Advanced Features
   - Custom dashboards
   - Report generation
   - Threat intelligence lookup
   - Custom rule creation

---

**Document Created**: November 2024
**Framework Recommendations**: React + TypeScript + SIEM SDK
**Testing Framework**: Jest + React Testing Library

# SIEM API Specification

## Overview

The SIEM platform exposes a comprehensive REST API and GraphQL endpoint for all operations.

## Base URL

```
Production: https://api.siem.example.com/v1
Staging: https://api-staging.siem.example.com/v1
```

## Authentication

### API Key Authentication
```http
Authorization: Bearer <api-key>
```

### OAuth 2.0
```http
Authorization: Bearer <access-token>
```

### Service Account (JWT)
```http
Authorization: Bearer <jwt-token>
```

## Rate Limiting

- **Standard Users**: 1000 requests/hour
- **Premium Users**: 10000 requests/hour
- **Service Accounts**: 50000 requests/hour

Headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1642089600
```

## Common Response Codes

```
200 OK - Success
201 Created - Resource created
204 No Content - Success with no body
400 Bad Request - Invalid input
401 Unauthorized - Authentication required
403 Forbidden - Insufficient permissions
404 Not Found - Resource not found
422 Unprocessable Entity - Validation error
429 Too Many Requests - Rate limit exceeded
500 Internal Server Error - Server error
503 Service Unavailable - Temporary outage
```

## Error Response Format

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
    "timestamp": "2025-01-15T10:30:45Z"
  }
}
```

---

## Events API

### Search Events

```http
POST /events/search
```

**Request:**
```json
{
  "query": {
    "bool": {
      "must": [
        {
          "match": {
            "event.type": "authentication"
          }
        },
        {
          "range": {
            "timestamp": {
              "gte": "2025-01-15T00:00:00Z",
              "lte": "2025-01-15T23:59:59Z"
            }
          }
        }
      ]
    }
  },
  "sort": [
    {
      "timestamp": "desc"
    }
  ],
  "from": 0,
  "size": 100,
  "fields": ["timestamp", "source.ip", "user.username", "event.action"]
}
```

**Response:**
```json
{
  "total": 1523,
  "hits": [
    {
      "event_id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2025-01-15T10:30:45Z",
      "source": {
        "ip": "10.0.1.100",
        "hostname": "web-server-01"
      },
      "user": {
        "username": "john.doe"
      },
      "event": {
        "type": "authentication",
        "action": "login",
        "outcome": "success"
      }
    }
  ],
  "aggregations": {
    "by_action": {
      "buckets": [
        {
          "key": "success",
          "doc_count": 1200
        },
        {
          "key": "failed",
          "doc_count": 323
        }
      ]
    }
  }
}
```

### Get Event by ID

```http
GET /events/{event_id}
```

**Response:**
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-15T10:30:45Z",
  ... // Full event object
}
```

### Get Event Context

```http
GET /events/{event_id}/context
```

Returns related events before and after the specified event.

**Parameters:**
- `before`: Number of events before (default: 10, max: 100)
- `after`: Number of events after (default: 10, max: 100)

### Export Events

```http
POST /events/export
```

**Request:**
```json
{
  "query": { ... },
  "format": "json|csv|parquet",
  "compression": "none|gzip|zip",
  "fields": ["timestamp", "source.ip", "event.type"]
}
```

**Response:**
```json
{
  "export_id": "export_123",
  "status": "processing",
  "download_url": null,
  "expires_at": "2025-01-16T10:30:45Z"
}
```

Check export status:
```http
GET /events/export/{export_id}
```

---

## Alerts API

### List Alerts

```http
GET /alerts
```

**Query Parameters:**
- `status`: Filter by status (new, acknowledged, investigating, resolved)
- `severity`: Filter by severity (critical, high, medium, low, info)
- `from_time`: Start time (ISO 8601)
- `to_time`: End time (ISO 8601)
- `assigned_to`: Filter by assignee
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 50, max: 1000)

**Response:**
```json
{
  "total": 523,
  "page": 1,
  "per_page": 50,
  "alerts": [
    {
      "alert_id": "alert_123",
      "timestamp": "2025-01-15T10:30:45Z",
      "title": "SSH Brute Force Attack Detected",
      "severity": "high",
      "status": "new",
      "risk_score": 85,
      "rule": {
        "id": "rule_001",
        "name": "SSH Brute Force Detection"
      },
      "entities": {
        "source_ips": ["203.0.113.50"],
        "users": ["root"]
      }
    }
  ]
}
```

### Get Alert Details

```http
GET /alerts/{alert_id}
```

### Create Alert

```http
POST /alerts
```

**Request:**
```json
{
  "title": "Suspicious Activity Detected",
  "description": "Manual alert creation",
  "severity": "medium",
  "entities": {
    "source_ips": ["192.0.2.100"],
    "users": ["suspicious.user"]
  },
  "rule_id": null,
  "event_ids": ["event_1", "event_2"]
}
```

### Update Alert

```http
PATCH /alerts/{alert_id}
```

**Request:**
```json
{
  "status": "investigating",
  "assigned_to": "analyst_jane",
  "notes": "Investigating suspicious login pattern"
}
```

### Bulk Update Alerts

```http
POST /alerts/bulk-update
```

**Request:**
```json
{
  "alert_ids": ["alert_1", "alert_2", "alert_3"],
  "updates": {
    "status": "false_positive",
    "disposition": "false_positive"
  }
}
```

### Get Alert Timeline

```http
GET /alerts/{alert_id}/timeline
```

Returns chronological history of the alert.

### Add Alert Note

```http
POST /alerts/{alert_id}/notes
```

**Request:**
```json
{
  "note": "Confirmed false positive - automated scanner from security team"
}
```

---

## Incidents API

### List Incidents

```http
GET /incidents
```

**Query Parameters:**
- `status`: Filter by status
- `severity`: Filter by severity
- `from_time`: Start time
- `to_time`: End time
- `assigned_to`: Filter by assignee
- `category`: Filter by category

### Get Incident

```http
GET /incidents/{incident_id}
```

### Create Incident

```http
POST /incidents
```

**Request:**
```json
{
  "title": "Data Exfiltration Attempt",
  "description": "Unusual data transfer detected",
  "severity": "critical",
  "category": "data_breach",
  "alert_ids": ["alert_1", "alert_2"],
  "assigned_to": "incident_manager_john"
}
```

### Update Incident

```http
PATCH /incidents/{incident_id}
```

### Add Evidence to Incident

```http
POST /incidents/{incident_id}/evidence
```

**Request (multipart/form-data):**
```
file: <binary>
type: log|screenshot|memory_dump|pcap|other
description: Memory dump from compromised host
```

### Execute Playbook

```http
POST /incidents/{incident_id}/playbooks/{playbook_id}/execute
```

**Request:**
```json
{
  "parameters": {
    "isolation_level": "full",
    "notify_users": true
  }
}
```

### Close Incident

```http
POST /incidents/{incident_id}/close
```

**Request:**
```json
{
  "resolution": "Threat contained and remediated",
  "root_cause": "Phishing email with malicious attachment",
  "lessons_learned": "Implement email sandboxing",
  "actions_taken": [
    "Isolated affected hosts",
    "Reset user passwords",
    "Patched vulnerability"
  ]
}
```

---

## Detection Rules API

### List Rules

```http
GET /rules
```

**Query Parameters:**
- `enabled`: Filter by status (true/false)
- `type`: Filter by rule type
- `category`: Filter by category
- `tags`: Filter by tags (comma-separated)

### Get Rule

```http
GET /rules/{rule_id}
```

### Create Rule

```http
POST /rules
```

**Request:**
```json
{
  "name": "Multiple Failed Logins",
  "description": "Detects multiple failed login attempts",
  "type": "threshold",
  "category": "authentication",
  "severity": "medium",
  "logic": {
    "query": "event_type:authentication AND action:failed",
    "threshold": {
      "count": 5,
      "timeframe": "5m",
      "group_by": ["user.username"]
    }
  },
  "actions": {
    "create_alert": true,
    "alert_severity": "medium",
    "notify": ["soc_team"]
  },
  "enabled": true
}
```

### Update Rule

```http
PUT /rules/{rule_id}
```

### Delete Rule

```http
DELETE /rules/{rule_id}
```

### Test Rule

```http
POST /rules/{rule_id}/test
```

**Request:**
```json
{
  "from_time": "2025-01-15T00:00:00Z",
  "to_time": "2025-01-15T23:59:59Z"
}
```

**Response:**
```json
{
  "test_id": "test_123",
  "matches": 15,
  "sample_events": [ ... ],
  "execution_time_ms": 250
}
```

### Enable/Disable Rule

```http
POST /rules/{rule_id}/enable
POST /rules/{rule_id}/disable
```

---

## Assets API

### List Assets

```http
GET /assets
```

**Query Parameters:**
- `type`: Filter by asset type
- `criticality`: Filter by criticality
- `zone`: Filter by network zone
- `owner`: Filter by owner
- `tags`: Filter by tags

### Get Asset

```http
GET /assets/{asset_id}
```

### Create Asset

```http
POST /assets
```

**Request:**
```json
{
  "hostname": "web-server-01",
  "ip_addresses": ["10.0.1.100"],
  "type": "server",
  "criticality": {
    "level": "high",
    "business_impact": "high",
    "compliance_scope": ["pci", "soc2"]
  },
  "ownership": {
    "owner": "john.doe",
    "department": "Engineering"
  }
}
```

### Update Asset

```http
PATCH /assets/{asset_id}
```

### Get Asset Events

```http
GET /assets/{asset_id}/events
```

### Get Asset Vulnerabilities

```http
GET /assets/{asset_id}/vulnerabilities
```

### Get Asset Risk Score

```http
GET /assets/{asset_id}/risk-score
```

**Response:**
```json
{
  "asset_id": "asset_123",
  "risk_score": 75,
  "risk_level": "high",
  "factors": [
    {
      "factor": "critical_vulnerabilities",
      "score": 30,
      "details": "3 critical CVEs unpatched"
    },
    {
      "factor": "recent_alerts",
      "score": 25,
      "details": "5 high severity alerts in last 7 days"
    },
    {
      "factor": "asset_criticality",
      "score": 20,
      "details": "Hosts customer-facing application"
    }
  ],
  "calculated_at": "2025-01-15T12:00:00Z"
}
```

---

## Users API

### List Users

```http
GET /users
```

### Get User

```http
GET /users/{user_id}
```

### Get User Risk Score

```http
GET /users/{user_id}/risk-score
```

### Get User Activity

```http
GET /users/{user_id}/activity
```

**Query Parameters:**
- `from_time`: Start time
- `to_time`: End time
- `activity_type`: Filter by type

### Get User Behavior Baseline

```http
GET /users/{user_id}/behavior-baseline
```

**Response:**
```json
{
  "user_id": "user_123",
  "baseline": {
    "normal_login_hours": "08:00-18:00",
    "normal_locations": ["New York", "Boston"],
    "avg_sessions_per_day": 5,
    "typical_resources": ["gitlab", "jira"]
  },
  "anomalies_detected": 2,
  "last_updated": "2025-01-15T00:00:00Z"
}
```

---

## Threat Intelligence API

### Search IOCs

```http
GET /threat-intel/iocs
```

**Query Parameters:**
- `type`: IOC type (ip, domain, hash, email, url)
- `value`: IOC value
- `threat_level`: Threat level
- `source`: Source feed

### Get IOC Details

```http
GET /threat-intel/iocs/{ioc_id}
```

### Check IOC

```http
POST /threat-intel/iocs/check
```

**Request:**
```json
{
  "iocs": [
    {
      "type": "ip",
      "value": "203.0.113.50"
    },
    {
      "type": "domain",
      "value": "malicious.example"
    },
    {
      "type": "hash",
      "value": "5d41402abc4b2a76b9719d911017c592"
    }
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "ioc": {
        "type": "ip",
        "value": "203.0.113.50"
      },
      "is_malicious": true,
      "threat_level": "high",
      "confidence": 0.95,
      "categories": ["malware_c2", "scanner"],
      "first_seen": "2025-01-01T00:00:00Z",
      "last_seen": "2025-01-15T10:00:00Z",
      "sources": ["alienvault", "emergingthreats"]
    }
  ]
}
```

### Add Custom IOC

```http
POST /threat-intel/iocs
```

**Request:**
```json
{
  "type": "ip",
  "value": "198.51.100.50",
  "threat_level": "high",
  "categories": ["malware_c2"],
  "description": "Known ransomware C2",
  "expires_at": "2025-12-31T23:59:59Z"
}
```

### Get Threat Feeds

```http
GET /threat-intel/feeds
```

### Enable/Disable Feed

```http
POST /threat-intel/feeds/{feed_id}/enable
POST /threat-intel/feeds/{feed_id}/disable
```

---

## Dashboards API

### List Dashboards

```http
GET /dashboards
```

### Get Dashboard

```http
GET /dashboards/{dashboard_id}
```

### Create Dashboard

```http
POST /dashboards
```

**Request:**
```json
{
  "name": "Executive Security Overview",
  "description": "High-level security metrics",
  "widgets": [
    {
      "type": "metric",
      "title": "Alerts Today",
      "query": {
        "metric": "alert_count",
        "timeframe": "24h",
        "filters": {}
      },
      "position": {
        "x": 0,
        "y": 0,
        "width": 4,
        "height": 2
      }
    },
    {
      "type": "chart",
      "title": "Alerts by Severity",
      "visualization": "bar",
      "query": {
        "aggregation": "count",
        "group_by": "severity",
        "timeframe": "7d"
      },
      "position": {
        "x": 4,
        "y": 0,
        "width": 8,
        "height": 4
      }
    }
  ],
  "sharing": {
    "visibility": "private|team|organization",
    "shared_with": ["team_soc"]
  }
}
```

### Update Dashboard

```http
PUT /dashboards/{dashboard_id}
```

### Delete Dashboard

```http
DELETE /dashboards/{dashboard_id}
```

---

## Reports API

### List Reports

```http
GET /reports
```

### Generate Report

```http
POST /reports/generate
```

**Request:**
```json
{
  "type": "compliance|executive|incident|custom",
  "template": "pci_dss_quarterly",
  "parameters": {
    "from_time": "2025-01-01T00:00:00Z",
    "to_time": "2025-03-31T23:59:59Z",
    "include_sections": ["summary", "findings", "recommendations"]
  },
  "format": "pdf|html|docx",
  "recipients": ["compliance@example.com"]
}
```

**Response:**
```json
{
  "report_id": "report_123",
  "status": "generating",
  "download_url": null,
  "eta_seconds": 120
}
```

### Get Report Status

```http
GET /reports/{report_id}
```

### Download Report

```http
GET /reports/{report_id}/download
```

---

## Search API

### Advanced Search

```http
POST /search
```

**Request:**
```json
{
  "query": "source.ip:10.0.1.100 AND user.username:john.doe",
  "timeframe": {
    "from": "2025-01-15T00:00:00Z",
    "to": "2025-01-15T23:59:59Z"
  },
  "filters": {
    "event.type": ["authentication", "network"],
    "severity": ["high", "critical"]
  },
  "aggregations": {
    "by_hour": {
      "date_histogram": {
        "field": "timestamp",
        "interval": "1h"
      }
    },
    "top_users": {
      "terms": {
        "field": "user.username",
        "size": 10
      }
    }
  },
  "sort": [{"timestamp": "desc"}],
  "from": 0,
  "size": 100
}
```

### Saved Searches

```http
GET /searches
POST /searches
GET /searches/{search_id}
PUT /searches/{search_id}
DELETE /searches/{search_id}
```

---

## Analytics API

### Get Statistics

```http
GET /analytics/statistics
```

**Query Parameters:**
- `metric`: Metric name (events_count, alerts_count, mttr, mttd)
- `timeframe`: Time period (1h, 24h, 7d, 30d)
- `group_by`: Group by field

**Response:**
```json
{
  "metric": "alerts_count",
  "timeframe": "24h",
  "current_value": 156,
  "previous_value": 142,
  "change_percent": 9.86,
  "trend": "increasing",
  "data_points": [
    {
      "timestamp": "2025-01-15T00:00:00Z",
      "value": 12
    }
  ]
}
```

### Get Trends

```http
GET /analytics/trends
```

### Get Top Entities

```http
GET /analytics/top/{entity_type}
```

**Entity Types:** `source_ips`, `users`, `destinations`, `alert_rules`

---

## Playbooks API

### List Playbooks

```http
GET /playbooks
```

### Get Playbook

```http
GET /playbooks/{playbook_id}
```

### Create Playbook

```http
POST /playbooks
```

**Request:**
```json
{
  "name": "Phishing Response",
  "description": "Automated response to phishing alerts",
  "trigger": {
    "type": "alert",
    "condition": "alert.rule.category == 'phishing'"
  },
  "steps": [
    {
      "name": "Quarantine Email",
      "action": "email.quarantine",
      "parameters": {
        "email_id": "{{alert.entities.email_id}}"
      }
    },
    {
      "name": "Extract IOCs",
      "action": "email.extract_iocs",
      "output": "iocs"
    },
    {
      "name": "Check Threat Intel",
      "action": "threat_intel.check",
      "input": "{{steps.extract_iocs.output.iocs}}"
    }
  ],
  "error_handling": {
    "on_failure": "notify_analyst",
    "retry": {
      "max_attempts": 3,
      "backoff": "exponential"
    }
  }
}
```

### Execute Playbook

```http
POST /playbooks/{playbook_id}/execute
```

### Get Playbook Execution History

```http
GET /playbooks/{playbook_id}/executions
```

---

## Configuration API

### Get System Configuration

```http
GET /config
```

### Update Configuration

```http
PATCH /config
```

**Request:**
```json
{
  "retention_policies": {
    "hot_storage_days": 30,
    "warm_storage_days": 90
  },
  "alerting": {
    "default_notification_channel": "email",
    "escalation_timeout_minutes": 30
  }
}
```

### Get Data Sources

```http
GET /config/data-sources
```

### Add Data Source

```http
POST /config/data-sources
```

**Request:**
```json
{
  "type": "syslog|api|agent",
  "name": "Firewall Logs",
  "config": {
    "host": "firewall.example.com",
    "port": 514,
    "protocol": "tcp",
    "tls": true
  },
  "parsing": {
    "format": "cef",
    "custom_parser": null
  },
  "enabled": true
}
```

---

## Audit Logs API

### Get Audit Logs

```http
GET /audit-logs
```

**Query Parameters:**
- `action`: Filter by action type
- `user`: Filter by user
- `resource_type`: Filter by resource type
- `from_time`: Start time
- `to_time`: End time

**Response:**
```json
{
  "total": 1532,
  "logs": [
    {
      "audit_id": "audit_123",
      "timestamp": "2025-01-15T10:30:45Z",
      "user": "admin@example.com",
      "action": "rule.update",
      "resource_type": "detection_rule",
      "resource_id": "rule_001",
      "changes": {
        "enabled": {
          "old": false,
          "new": true
        }
      },
      "ip_address": "192.0.2.100",
      "user_agent": "Mozilla/5.0..."
    }
  ]
}
```

---

## WebSocket API

### Real-time Events Stream

```
wss://api.siem.example.com/v1/stream/events
```

**Authentication:**
```json
{
  "type": "auth",
  "token": "Bearer <token>"
}
```

**Subscribe:**
```json
{
  "type": "subscribe",
  "channels": ["alerts", "critical_events"],
  "filters": {
    "severity": ["critical", "high"]
  }
}
```

**Message Format:**
```json
{
  "type": "alert",
  "channel": "alerts",
  "timestamp": "2025-01-15T10:30:45Z",
  "data": {
    "alert_id": "alert_123",
    ...
  }
}
```

---

## GraphQL API

**Endpoint:** `https://api.siem.example.com/v1/graphql`

### Example Query

```graphql
query {
  alerts(
    first: 10
    where: {
      severity: HIGH
      status: NEW
      timestamp_gte: "2025-01-15T00:00:00Z"
    }
    orderBy: timestamp_DESC
  ) {
    edges {
      node {
        id
        title
        severity
        riskScore
        rule {
          name
          category
        }
        entities {
          sourceIps
          users
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

### Example Mutation

```graphql
mutation {
  updateAlert(
    id: "alert_123"
    input: {
      status: INVESTIGATING
      assignedTo: "analyst_jane"
      notes: "Investigating brute force attempt"
    }
  ) {
    alert {
      id
      status
      assignedTo
    }
  }
}
```

---

## Pagination

### Cursor-based Pagination

```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTIzfQ==",
    "has_more": true
  }
}
```

Next request:
```http
GET /alerts?cursor=eyJpZCI6MTIzfQ==&limit=50
```

### Offset-based Pagination

```http
GET /alerts?page=2&per_page=50
```

---

## Filtering

### Query String Filters

```http
GET /events?source.ip=10.0.1.100&event.severity=high&timestamp_gte=2025-01-15T00:00:00Z
```

### Advanced Filters (JSON)

```json
{
  "filters": {
    "and": [
      {
        "field": "source.ip",
        "operator": "in",
        "value": ["10.0.1.100", "10.0.1.101"]
      },
      {
        "field": "event.severity",
        "operator": "gte",
        "value": "medium"
      }
    ]
  }
}
```

**Supported Operators:**
- `eq`, `ne` (equals, not equals)
- `gt`, `gte`, `lt`, `lte` (greater than, less than)
- `in`, `not_in` (in list, not in list)
- `contains`, `not_contains`
- `starts_with`, `ends_with`
- `regex`

---

## Webhooks

### Register Webhook

```http
POST /webhooks
```

**Request:**
```json
{
  "url": "https://example.com/webhook",
  "events": ["alert.created", "alert.updated", "incident.created"],
  "filters": {
    "severity": ["critical", "high"]
  },
  "secret": "webhook_secret_key",
  "enabled": true
}
```

### Webhook Payload

```json
{
  "webhook_id": "webhook_123",
  "event": "alert.created",
  "timestamp": "2025-01-15T10:30:45Z",
  "data": {
    "alert_id": "alert_123",
    ...
  },
  "signature": "sha256=..."
}
```

**Signature Verification:**
```
HMAC-SHA256(payload, secret)
```

---

## SDK Examples

### Python

```python
from siem_sdk import SIEMClient

client = SIEMClient(
    api_key="your_api_key",
    base_url="https://api.siem.example.com/v1"
)

# Search events
events = client.events.search(
    query="event.type:authentication AND event.outcome:failure",
    from_time="2025-01-15T00:00:00Z",
    to_time="2025-01-15T23:59:59Z"
)

# List alerts
alerts = client.alerts.list(
    status="new",
    severity=["critical", "high"]
)

# Update alert
client.alerts.update(
    alert_id="alert_123",
    status="investigating",
    assigned_to="analyst_jane"
)
```

### JavaScript

```javascript
const SIEMClient = require('@siem/sdk');

const client = new SIEMClient({
  apiKey: 'your_api_key',
  baseUrl: 'https://api.siem.example.com/v1'
});

// Search events
const events = await client.events.search({
  query: 'event.type:authentication AND event.outcome:failure',
  fromTime: '2025-01-15T00:00:00Z',
  toTime: '2025-01-15T23:59:59Z'
});

// Subscribe to real-time alerts
client.stream.subscribe('alerts', { severity: ['critical', 'high'] }, (alert) => {
  console.log('New alert:', alert);
});
```

---

## Best Practices

1. **Use API keys for service accounts**, OAuth for user-based access
2. **Implement exponential backoff** for rate limit handling
3. **Cache responses** when appropriate
4. **Use pagination** for large result sets
5. **Subscribe to webhooks** for real-time updates instead of polling
6. **Validate webhook signatures** to ensure authenticity
7. **Use cursor-based pagination** for consistent results
8. **Compress large payloads** with gzip
9. **Use field filtering** to reduce response size
10. **Monitor API usage** to avoid rate limits

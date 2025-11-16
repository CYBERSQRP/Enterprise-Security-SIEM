# AI Security Analyst Service

AI-powered security analyst assistant that provides intelligent recommendations, automated triage, and investigation guidance for security events.

## Features

- **Intelligent Analysis**: AI-driven security event analysis with contextual understanding
- **MITRE ATT&CK Mapping**: Automatic mapping of events to MITRE ATT&CK framework
- **Risk Assessment**: Comprehensive risk scoring for events and assets
- **Automated Triage**: Smart prioritization of alerts based on multiple factors
- **Investigation Recommendations**: AI-generated step-by-step investigation guidance
- **IOC Extraction**: Automatic extraction of indicators of compromise
- **Threat Context**: Enrichment with threat intelligence data
- **Event Correlation**: Identification of related security events
- **Next Steps**: Actionable recommendations for security analysts

## API Endpoints

### Health Check
```bash
GET /health
```

### Analyze Security Event
```bash
POST /api/v1/analyze
Content-Type: application/json

{
  "event_id": "evt-12345",
  "timestamp": "2024-01-15T10:30:00Z",
  "event_type": "malware_execution",
  "severity": "high",
  "source_ip": "192.168.1.100",
  "user": "jdoe",
  "process": "powershell.exe",
  "raw_log": "Suspicious PowerShell execution detected",
  "metadata": {}
}
```

Response:
```json
{
  "event_id": "evt-12345",
  "threat_context": {
    "threat_type": "Malware Execution",
    "mitre_tactics": ["Execution"],
    "mitre_techniques": ["T1204 - User Execution", "T1059 - Command and Scripting Interpreter"],
    "iocs": ["ip:192.168.1.100"],
    "confidence_score": 0.8,
    "risk_score": 0.7,
    "affected_assets": ["host:192.168.1.100", "user:jdoe"],
    "timeline": [...]
  },
  "risk_assessment": {
    "event_risk": 0.7,
    "asset_risk": 0.4,
    "overall_risk": 0.58,
    "risk_factors": ["High severity event"]
  },
  "related_events_count": 0,
  "recommendations": [
    {
      "recommendation_type": "forensics",
      "priority": 4,
      "description": "Collect forensic evidence",
      "action_items": [
        "Capture memory dump",
        "Collect disk images",
        "Preserve network traffic captures",
        "Document chain of custody"
      ],
      "rationale": "High severity event requires forensic analysis",
      "estimated_impact": "Enables detailed post-incident analysis",
      "confidence": 0.8
    }
  ],
  "next_steps": [
    "Capture memory dump",
    "Collect disk images",
    "Run query: Find all events from 192.168.1.100 in last 24h",
    "Check recent activity for user: jdoe"
  ],
  "triage_decision": {
    "triage_score": 0.74,
    "priority": "P2 - High",
    "recommended_action": "assign_to_analyst",
    "rationale": "Event severity: high | Risk score: 0.70 | Confidence: 0.80",
    "requires_human_review": true
  },
  "timestamp": "2024-01-15T10:30:05.123456"
}
```

### Quick Triage
```bash
POST /api/v1/triage
Content-Type: application/json

{
  "event_id": "evt-12345",
  "timestamp": "2024-01-15T10:30:00Z",
  "event_type": "brute_force_attack",
  "severity": "medium"
}
```

### Get MITRE Mapping
```bash
GET /api/v1/mitre/{event_type}
```

Example:
```bash
GET /api/v1/mitre/brute_force_attack
```

Response:
```json
{
  "event_type": "brute_force_attack",
  "mapping": {
    "tactics": ["Credential Access"],
    "techniques": ["T1110 - Brute Force", "T1110.001 - Password Guessing"]
  }
}
```

### Statistics
```bash
GET /api/v1/stats
```

### Metrics
```bash
GET /metrics
```

## Analysis Components

### 1. Threat Context Gathering
- MITRE ATT&CK mapping
- Threat intelligence lookup
- IOC extraction
- Asset identification
- Timeline construction

### 2. Risk Assessment
Calculates risk scores based on:
- Event severity
- Asset criticality
- Threat indicators
- Historical patterns

### 3. Investigation Recommendations
AI generates recommendations for:
- Immediate containment
- Deep investigation
- Proactive threat hunting
- Forensic collection

### 4. Automated Triage
Priority levels:
- **P1 - Critical**: Immediate escalation to incident response
- **P2 - High**: Assign to senior analyst
- **P3 - Medium**: Queue for review
- **P4 - Low**: Consider automated closure

## MITRE ATT&CK Coverage

Supported event types and mappings:

| Event Type | Tactics | Techniques |
|------------|---------|------------|
| brute_force_attack | Credential Access | T1110, T1110.001 |
| lateral_movement | Lateral Movement | T1021, T1570 |
| data_exfiltration | Exfiltration | T1041, T1048 |
| privilege_escalation | Privilege Escalation | T1068, T1134 |
| malware_execution | Execution | T1204, T1059 |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Service port | 8091 |
| `ENV` | Environment (development/production) | production |
| `ELASTICSEARCH_URL` | Elasticsearch URL for event queries | http://elasticsearch:9200 |
| `THREAT_INTEL_API` | Threat intelligence API endpoint | - |

## Running Locally

### With Docker
```bash
docker build -t ai-analyst .
docker run -p 8091:8091 ai-analyst
```

### With Python
```bash
pip install -r requirements.txt
python main.py
```

## Integration Examples

### Python
```python
import requests
from datetime import datetime

# Analyze an event
response = requests.post(
    "http://localhost:8091/api/v1/analyze",
    json={
        "event_id": "evt-12345",
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "lateral_movement",
        "severity": "high",
        "source_ip": "10.0.1.50",
        "dest_ip": "10.0.2.100",
        "user": "admin",
        "raw_log": "Suspicious RDP connection detected"
    }
)

analysis = response.json()
print(f"Priority: {analysis['triage_decision']['priority']}")
print(f"Next Steps: {analysis['next_steps']}")
```

### cURL
```bash
curl -X POST http://localhost:8091/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt-999",
    "timestamp": "2024-01-15T15:30:00Z",
    "event_type": "data_exfiltration",
    "severity": "critical",
    "source_ip": "192.168.1.50",
    "dest_ip": "203.0.113.42",
    "description": "Large data transfer to external IP"
  }'
```

## Monitoring

The service exposes Prometheus metrics at `/metrics`:

- `ai_analyst_requests_total` - Total analysis requests by severity
- `ai_analyst_duration_seconds` - Time spent analyzing events

## Development

### Adding New Event Types
1. Update `ThreatKnowledgeBase._load_mitre_mappings()` with new mappings
2. Add threat intelligence rules
3. Update documentation

### Extending Analysis Logic
1. Modify `AISecurityAnalyst.analyze_alert()` for new analysis steps
2. Update `_generate_recommendations()` for new recommendation types
3. Adjust `_auto_triage()` for custom triage logic

## License

Copyright © 2024 Enterprise Security SIEM

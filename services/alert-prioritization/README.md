# Alert Prioritization Service

Intelligent alert prioritization service using machine learning and rule-based logic to automatically classify and prioritize security alerts.

## Features

- **ML-Based Prioritization**: Neural network model trained on historical alert data
- **Rule-Based Adjustments**: Business rules to override ML when necessary
- **Multi-Factor Analysis**: Considers 50+ features including:
  - Alert severity and type
  - Asset criticality
  - User risk scores
  - IP reputation
  - Historical false positive rates
  - Time-based context
  - Attack pattern matching
  - Correlation with other alerts
- **Priority Levels**: 5 priority levels (P0-P4) with recommended SLAs
- **Automated Actions**: Suggests next steps based on priority
- **Batch Processing**: Efficient bulk alert prioritization
- **Prometheus Metrics**: Built-in monitoring and observability

## Priority Levels

| Level | Name | SLA | Use Case |
|-------|------|-----|----------|
| P0 | CRITICAL | 15 minutes | Immediate response required (ransomware, data exfiltration) |
| P1 | HIGH | 1 hour | Critical alerts requiring urgent attention |
| P2 | MEDIUM | 4 hours | Important alerts for investigation |
| P3 | LOW | 24 hours | Routine alerts |
| P4 | INFO | 7 days | Informational alerts |

## API Endpoints

### Health Check
```bash
GET /health
```

### Prioritize Single Alert
```bash
POST /api/v1/prioritize
Content-Type: application/json

{
  "alert_id": "alert-123",
  "timestamp": "2024-01-15T10:30:00Z",
  "alert_type": "ransomware",
  "severity": "critical",
  "source_ip": "192.168.1.100",
  "user": "admin",
  "asset": "prod-db-01",
  "description": "Ransomware activity detected"
}
```

Response:
```json
{
  "alert_id": "alert-123",
  "priority": "P0_CRITICAL",
  "priority_score": 0.95,
  "factors": {
    "critical_asset": 1.0,
    "known_attack_pattern": 0.9
  },
  "recommended_sla_minutes": 15,
  "reasoning": [
    "Alert classified as P0_CRITICAL (confidence: 0.95)",
    "Alert involves critical asset",
    "Matches known attack pattern"
  ],
  "auto_actions": [
    "Immediately notify on-call security engineer",
    "Create incident ticket",
    "Begin automated containment procedures",
    "Escalate to SOC manager"
  ]
}
```

### Batch Prioritization
```bash
POST /api/v1/prioritize/batch
Content-Type: application/json

{
  "alerts": [...]
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

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Service port | 8090 |
| `MODEL_PATH` | Path to trained ML model | None (uses default) |
| `ENV` | Environment (development/production) | production |

## Running Locally

### With Docker
```bash
docker build -t alert-prioritization .
docker run -p 8090:8090 alert-prioritization
```

### With Python
```bash
pip install -r requirements.txt
python main.py
```

## How It Works

1. **Feature Extraction**: Extracts 50 features from each alert including:
   - Basic: severity, alert type, asset criticality
   - Temporal: time of day, business hours, day of week
   - User context: privilege level, risk score
   - Network: IP reputation
   - Historical: false positive rate, alert frequency
   - Contextual: IOC matches, attack patterns

2. **ML Prediction**: Neural network predicts initial priority level

3. **Rule-Based Adjustment**: Business rules override ML when:
   - Alert involves critical assets
   - Matches known attack patterns
   - Part of correlated attack sequence
   - High false positive history

4. **Priority Calculation**: Combines ML confidence with rule factors

5. **Action Recommendation**: Suggests automated actions based on priority

## ML Model Architecture

- Input: 50 features
- Hidden layers: [256, 128, 64] with BatchNorm and Dropout
- Output: 5 priority levels (softmax)
- Framework: PyTorch

## Integration Examples

### Python
```python
import requests

response = requests.post(
    "http://localhost:8090/api/v1/prioritize",
    json={
        "alert_id": "alert-123",
        "timestamp": "2024-01-15T10:30:00Z",
        "alert_type": "malware_execution",
        "severity": "high",
        "description": "Suspicious process execution detected"
    }
)

result = response.json()
print(f"Priority: {result['priority']}")
print(f"Actions: {result['auto_actions']}")
```

### cURL
```bash
curl -X POST http://localhost:8090/api/v1/prioritize \
  -H "Content-Type: application/json" \
  -d '{
    "alert_id": "alert-123",
    "timestamp": "2024-01-15T10:30:00Z",
    "alert_type": "brute_force",
    "severity": "medium",
    "source_ip": "203.0.113.42",
    "description": "Multiple failed login attempts"
  }'
```

## Monitoring

The service exposes Prometheus metrics at `/metrics`:

- `alert_prioritization_requests_total` - Total prioritization requests by priority level
- `alert_prioritization_duration_seconds` - Time spent prioritizing alerts

## Development

### Adding New Features
1. Update `FeatureExtractor.extract_features()` to include new features
2. Ensure feature vector remains 50 dimensions
3. Retrain ML model with new features

### Adding New Rules
1. Update `_apply_priority_rules()` in `prioritizer.py`
2. Add factor to `rule_factors` dictionary
3. Update `_calculate_priority_score()` if needed

## License

Copyright © 2024 Enterprise Security SIEM

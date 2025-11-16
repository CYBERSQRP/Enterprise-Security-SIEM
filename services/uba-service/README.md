# User Behavior Analytics (UBA) Service

The UBA service provides advanced user behavior analytics capabilities to detect insider threats, compromised accounts, and anomalous user activities.

## Overview

This service implements user behavior profiling, peer group analysis, risk scoring, and behavioral anomaly detection to identify suspicious user activities that may indicate security threats.

## Features

### 1. Behavior Profiling
- **User baseline creation**: Establish normal behavior patterns for each user
- **Temporal patterns**: Time-based activity analysis (working hours, login times)
- **Access patterns**: Resource access frequency and patterns
- **Activity patterns**: User action sequences and workflows

### 2. Peer Group Analysis
- **Automatic peer grouping**: Group users by role, department, and behavior
- **Peer comparison**: Compare user behavior against peer baselines
- **Deviation detection**: Identify users deviating from peer norms
- **Dynamic group updates**: Automatically adjust peer groups over time

### 3. Risk Scoring
- **Multi-factor risk scoring**: Combine multiple risk signals
- **Real-time risk updates**: Update user risk scores in real-time
- **Risk thresholds**: Configurable thresholds for alerting
- **Historical risk tracking**: Track risk score evolution over time

### 4. Behavioral Anomaly Detection
- **Login anomalies**: Unusual login patterns, times, locations
- **Access anomalies**: Unusual file/resource access
- **Data exfiltration**: Detect unusual data download/transfer patterns
- **Privilege abuse**: Detect misuse of elevated privileges
- **Insider threat indicators**: Identify indicators of malicious insider activity

## Architecture

```
┌──────────────────┐
│  Event Streams   │
│  (Kafka Topics)  │
└────────┬─────────┘
         │
┌────────▼─────────┐
│ Event Processor  │
│  - User events   │
│  - Access events │
│  - Auth events   │
└────────┬─────────┘
         │
┌────────▼─────────┐
│ Behavior Engine  │
│  - Profiling     │
│  - Peer Analysis │
│  - Risk Scoring  │
└────────┬─────────┘
         │
┌────────▼─────────┐
│  Risk Database   │
│  (PostgreSQL +   │
│   TimescaleDB)   │
└────────┬─────────┘
         │
┌────────▼─────────┐
│   UBA API        │
│  - Risk scores   │
│  - User profiles │
│  - Alerts        │
└──────────────────┘
```

## API Endpoints

### User Risk Scoring

```http
GET /api/v1/uba/users/{user_id}/risk-score
```

Get current risk score for a user.

```http
GET /api/v1/uba/users/{user_id}/risk-history?start=2024-01-01&end=2024-01-31
```

Get historical risk scores for a user.

### Behavior Profiles

```http
GET /api/v1/uba/users/{user_id}/profile
```

Get behavior profile for a user.

```http
GET /api/v1/uba/users/{user_id}/anomalies
```

Get recent behavioral anomalies for a user.

### Peer Groups

```http
GET /api/v1/uba/peer-groups/{group_id}
```

Get peer group information.

```http
GET /api/v1/uba/users/{user_id}/peers
```

Get peer group for a specific user.

### High Risk Users

```http
GET /api/v1/uba/high-risk-users?threshold=80&limit=50
```

Get list of high-risk users.

## Data Models

### User Risk Score

```json
{
  "user_id": "user123",
  "risk_score": 75,
  "risk_level": "high",
  "risk_factors": [
    {
      "factor": "unusual_login_time",
      "score": 25,
      "details": "Login at 3:00 AM"
    },
    {
      "factor": "unusual_data_access",
      "score": 30,
      "details": "Accessed 500+ sensitive files"
    },
    {
      "factor": "peer_deviation",
      "score": 20,
      "details": "Activity differs significantly from peers"
    }
  ],
  "timestamp": "2024-01-15T14:30:00Z"
}
```

### Behavior Profile

```json
{
  "user_id": "user123",
  "profile": {
    "typical_login_hours": [8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
    "typical_login_locations": ["192.168.1.0/24"],
    "average_files_accessed_per_day": 45,
    "typical_applications": ["email", "crm", "document_editor"],
    "peer_group_id": "sales_team_west"
  },
  "last_updated": "2024-01-15T14:30:00Z"
}
```

## Configuration

Configuration is managed through environment variables and config files:

```yaml
# config/uba.yaml

behavior_profiling:
  baseline_period_days: 30
  min_events_for_baseline: 100
  profile_update_frequency: daily

peer_groups:
  min_group_size: 5
  similarity_threshold: 0.7
  auto_update_enabled: true

risk_scoring:
  score_range: [0, 100]
  high_risk_threshold: 75
  medium_risk_threshold: 50
  alert_on_score_change: 20

anomaly_detection:
  sensitivity: medium  # low, medium, high
  ml_model_path: /models/uba/behavioral_anomaly.pkl
```

## Technology Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL with TimescaleDB extension
- **Message Queue**: Kafka
- **ML Libraries**: scikit-learn, PyTorch
- **Async Processing**: Celery

## Running the Service

### Development

```bash
cd services/uba-service
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8005
```

### Docker

```bash
docker build -t siem-uba-service .
docker run -p 8005:8005 siem-uba-service
```

### Kubernetes

```bash
kubectl apply -f k8s/uba-service.yaml
```

## Monitoring

The service exposes Prometheus metrics at `/metrics`:

- `uba_risk_scores_calculated_total`
- `uba_anomalies_detected_total`
- `uba_profiles_updated_total`
- `uba_api_requests_total`
- `uba_api_latency_seconds`

## Testing

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Load tests
locust -f tests/load/locustfile.py
```

## Dependencies

See `requirements.txt` for full dependency list.

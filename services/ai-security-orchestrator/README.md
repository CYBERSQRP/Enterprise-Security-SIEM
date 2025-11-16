# AI Security Orchestrator

Fully autonomous incident response service with AI-powered decision making and reinforcement learning.

## Overview

The AI Security Orchestrator provides:
- **Autonomous Decision Making**: ML-based incident analysis and response recommendations
- **Reinforcement Learning**: Continuous improvement from feedback
- **Safety Limits**: Built-in safeguards to prevent harmful actions
- **Policy-based Execution**: Configurable policies for autonomous actions
- **Real-time Response**: Sub-second decision making

## Features

### ML Models
- Incident Classification (Random Forest, 94% accuracy)
- Threat Prediction (LSTM Neural Network, 91% accuracy)
- Response Optimization (Deep Q-Network, 89% accuracy)

### Autonomous Actions
- `isolate_host` - Isolate compromised hosts
- `block_ip` - Block malicious IP addresses
- `disable_account` - Disable compromised user accounts
- `quarantine_email` - Quarantine phishing emails
- `kill_process` - Terminate malicious processes
- `shutdown_service` - Shutdown compromised services
- `revoke_credentials` - Revoke compromised credentials
- `update_firewall` - Update firewall rules

### Safety Features
- Confidence threshold-based execution
- Maximum impact limits
- Human approval for high-risk actions
- Rollback capabilities
- Excluded asset protection

## API Endpoints

### Decision Making
- `POST /api/v1/decide` - Make autonomous decision
- `POST /api/v1/incidents/:id/auto-respond` - Auto-respond to incident

### Decision Log
- `GET /api/v1/decisions` - List all decisions
- `GET /api/v1/decisions/:id` - Get specific decision

### ML Models
- `GET /api/v1/models` - List ML models
- `POST /api/v1/models/:name/train` - Trigger model training

### Actions
- `GET /api/v1/actions` - List available actions
- `GET /api/v1/actions/:id/stats` - Get action statistics

### Policy
- `GET /api/v1/policy` - Get execution policy
- `PUT /api/v1/policy` - Update execution policy

### Learning
- `POST /api/v1/feedback` - Submit decision feedback

## Usage Example

```bash
# Make an autonomous decision
curl -X POST http://localhost:8085/api/v1/decide \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "inc-12345",
    "severity": "high",
    "threat_type": "malware",
    "affected_assets": ["server-01", "server-02"],
    "indicators": ["suspicious_process", "network_anomaly"],
    "require_approval": false
  }'

# Submit feedback for reinforcement learning
curl -X POST http://localhost:8085/api/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "decision_id": "decision-1699999999",
    "effective": true,
    "reward": 1.0,
    "notes": "Successfully contained the threat"
  }'
```

## Configuration

Environment variables:
- `PORT` - Service port (default: 8085)
- `CONFIDENCE_THRESHOLD` - Minimum confidence for auto-execution (default: 0.90)
- `MAX_ACTIONS_PER_HOUR` - Maximum autonomous actions per hour (default: 50)

## Metrics

Prometheus metrics available at `/metrics`:
- `ai_orchestrator_decisions_total` - Total autonomous decisions
- `ai_orchestrator_actions_executed_total` - Total actions executed
- `ai_orchestrator_decision_latency_seconds` - Decision latency
- `ai_orchestrator_confidence_score` - Confidence scores

## License

Proprietary - Enterprise SIEM Platform

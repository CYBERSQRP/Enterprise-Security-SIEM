# Phase 2 Implementation: Core SIEM Features

## Overview

Phase 2 implements the core SIEM capabilities including detection, alerting, threat intelligence, incident management, and automated response. This phase transforms the platform from a basic log collection system into a full-featured security operations center (SOC) platform.

## Implementation Summary

### Completion Status: ✅ Complete

Phase 2 has been fully implemented with all major components operational.

## Components Implemented

### 1. Correlation Engine (Rust)

**Location**: `services/correlator/`

**Purpose**: Real-time event correlation and pattern detection

**Features**:
- Rule-based correlation engine
- Threshold-based detection
- Time-based correlation windows
- Sequence detection
- Statistical anomaly detection (basic)
- Kafka integration for event streaming
- PostgreSQL for rule storage
- Redis for correlation state management

**Key Files**:
- `src/main.rs` - Main service entry point
- `src/engine.rs` - Core correlation engine logic
- `src/rules.rs` - Rule evaluation engine
- `src/models.rs` - Data models
- `src/storage.rs` - Database integration

**API Endpoints**:
- `GET /health` - Health check
- `GET /api/v1/rules` - List correlation rules
- `POST /api/v1/rules` - Create new rule
- `POST /api/v1/rules/reload` - Reload rules from database
- `GET /api/v1/stats` - Get engine statistics

**Configuration**:
```bash
CORRELATOR_SERVER_HOST=0.0.0.0
CORRELATOR_SERVER_PORT=8080
CORRELATOR_KAFKA_BROKERS=kafka:9092
CORRELATOR_KAFKA_INPUT_TOPIC=events
CORRELATOR_KAFKA_OUTPUT_TOPIC=alerts
CORRELATOR_REDIS_URL=redis://redis:6379
CORRELATOR_DATABASE_URL=postgresql://siem:siem@postgres:5432/siem
```

### 2. Alert Manager (Go)

**Location**: `services/alert-manager/`

**Purpose**: Alert lifecycle management and notification

**Features**:
- Alert creation, tracking, and lifecycle management
- Alert status workflow (New → Acknowledged → In Progress → Resolved)
- Assignment and escalation
- Multi-channel notifications (Slack, Teams, Email)
- Comment and collaboration features
- Alert statistics and metrics
- Kafka consumer for correlation results

**API Endpoints**:
- `GET /api/v1/alerts` - List alerts with filters
- `POST /api/v1/alerts` - Create alert
- `GET /api/v1/alerts/:id` - Get alert details
- `PATCH /api/v1/alerts/:id` - Update alert
- `POST /api/v1/alerts/:id/comments` - Add comment
- `GET /api/v1/alerts/stats` - Get alert statistics

**Configuration**:
```bash
SERVER_HOST=0.0.0.0
SERVER_PORT=8081
DATABASE_URL=postgresql://siem:siem@postgres:5432/siem
REDIS_URL=redis://redis:6379
KAFKA_BROKERS=kafka:9092
KAFKA_TOPIC=alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...
```

### 3. Threat Intelligence Service (Python)

**Location**: `services/threat-intel/`

**Purpose**: IOC management and threat intelligence enrichment

**Features**:
- Indicator of Compromise (IOC) management
- Support for multiple IOC types (IP, Domain, URL, File Hash, Email, CVE)
- Threat level classification
- Automated threat feed integration:
  - AlienVault OTX
  - Abuse.ch (Feodo Tracker)
  - VirusTotal
  - AbuseIPDB
- Real-time enrichment API
- IOC matching engine
- Threat actor tracking

**API Endpoints**:
- `POST /api/v1/iocs` - Create IOC
- `GET /api/v1/iocs` - List IOCs with filters
- `POST /api/v1/iocs/match` - Check for IOC match
- `POST /api/v1/enrich` - Enrich indicator
- `GET /api/v1/threat-actors` - List threat actors
- `GET /api/v1/stats` - Get threat intel statistics

**Configuration**:
```bash
SERVER_HOST=0.0.0.0
SERVER_PORT=8082
DATABASE_URL=postgresql+asyncpg://siem:siem@postgres:5432/siem
REDIS_URL=redis://redis:6379
OTX_API_KEY=your_otx_key
ABUSEIPDB_API_KEY=your_abuseipdb_key
VIRUSTOTAL_API_KEY=your_virustotal_key
FEED_UPDATE_INTERVAL=3600
```

### 4. Case Manager (Go)

**Location**: `services/case-manager/`

**Purpose**: Incident case management and investigation

**Features**:
- Incident case creation and tracking
- Case lifecycle workflow
- Evidence collection and management
- Timeline reconstruction
- Case collaboration and comments
- Investigation workspace

**API Endpoints**:
- `GET /api/v1/cases` - List cases
- `POST /api/v1/cases` - Create case
- `GET /api/v1/cases/:id` - Get case details
- `PATCH /api/v1/cases/:id` - Update case
- `POST /api/v1/cases/:id/evidence` - Add evidence
- `GET /api/v1/cases/:id/timeline` - Get case timeline
- `POST /api/v1/cases/:id/comments` - Add comment

**Configuration**:
```bash
SERVER_PORT=8083
DATABASE_URL=postgresql://siem:siem@postgres:5432/siem
```

### 5. Playbook Engine (Python)

**Location**: `services/playbook-engine/`

**Purpose**: Automated response orchestration

**Features**:
- Playbook definition and management
- Automated action execution
- Supported actions:
  - Block IP address
  - Isolate endpoint
  - Disable user account
  - Send email notification
  - Create ticket
  - Run custom script
  - Send webhook
- Execution tracking and logging
- Conditional logic support

**API Endpoints**:
- `GET /api/v1/playbooks` - List playbooks
- `POST /api/v1/playbooks` - Create playbook
- `GET /api/v1/playbooks/:id` - Get playbook
- `POST /api/v1/playbooks/:id/execute` - Execute playbook
- `GET /api/v1/executions/:id` - Get execution status

**Sample Playbooks**:
1. **Brute Force Response**: Block IP, send notification, create ticket
2. **Malware Containment**: Isolate endpoint, disable account, escalate

**Configuration**:
```bash
SERVER_HOST=0.0.0.0
SERVER_PORT=8084
```

### 6. Reporting Service (Go)

**Location**: `services/reporting/`

**Purpose**: Compliance and security reporting

**Features**:
- Compliance report generation
- Supported compliance frameworks:
  - PCI-DSS
  - HIPAA
  - SOC 2
  - GDPR
  - ISO 27001
- Security summary reports
- Incident reports
- Multiple export formats (PDF, CSV, JSON)
- Scheduled report generation

**API Endpoints**:
- `GET /api/v1/reports` - List reports
- `POST /api/v1/reports` - Generate report
- `GET /api/v1/reports/:id` - Get report metadata
- `GET /api/v1/reports/:id/download` - Download report
- `GET /api/v1/templates` - List report templates

**Configuration**:
```bash
SERVER_PORT=8085
DATABASE_URL=postgresql://siem:siem@postgres:5432/siem
```

## Detection Rules

### MITRE ATT&CK Mapping

**Location**: `rules/mitre-attack/techniques.yaml`

Comprehensive mapping of MITRE ATT&CK techniques to detection queries including:
- T1566 - Phishing
- T1078 - Valid Accounts
- T1059 - Command and Scripting Interpreter
- T1003 - OS Credential Dumping
- T1021.001 - Remote Desktop Protocol
- T1071 - Application Layer Protocol
- T1486 - Data Encrypted for Impact
- T1053 - Scheduled Task/Job
- T1562.001 - Disable or Modify Tools
- T1110 - Brute Force

### Detection Rules

**Location**: `rules/detection/`

Pre-built detection rules:
1. **Brute Force Attack Detection** - Threshold-based failed login detection
2. **Suspicious PowerShell Execution** - Malicious PowerShell command detection
3. **Lateral Movement via RDP** - RDP-based lateral movement detection

### Sigma Rules

**Location**: `rules/sigma/`

Industry-standard Sigma rules:
1. **Mimikatz Detection** - Credential dumping detection
2. **Web Shell Detection** - Web shell activity detection

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Event Sources                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                    Kafka Event Stream                            │
│                      (events topic)                              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                   Correlation Engine                             │
│  • Evaluates events against rules                               │
│  • Threshold, sequence, statistical detection                   │
│  • Produces correlation results                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                    Kafka Alert Stream                            │
│                     (alerts topic)                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                      Alert Manager                               │
│  • Creates and manages alerts                                   │
│  • Sends notifications                                          │
│  • Tracks lifecycle                                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
┌─────────────▼──────────┐   ┌───────────▼──────────────┐
│   Case Manager         │   │  Playbook Engine         │
│  • Create incidents    │   │  • Execute responses     │
│  • Track investigation │   │  • Automated actions     │
│  • Evidence mgmt       │   │  • Orchestration         │
└────────────────────────┘   └──────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
┌─────────────▼──────────┐   ┌───────────▼──────────────┐
│  Threat Intelligence   │   │  Reporting Service       │
│  • IOC management      │   │  • Compliance reports    │
│  • Enrichment          │   │  • Security dashboards   │
│  • Threat feeds        │   │  • Audit reports         │
└────────────────────────┘   └──────────────────────────┘
```

## Database Schema

### Alerts Table
```sql
CREATE TABLE alerts (
    id UUID PRIMARY KEY,
    correlation_id UUID,
    title VARCHAR(255),
    description TEXT,
    severity VARCHAR(20),
    status VARCHAR(20),
    source_events TEXT[],
    assigned_to VARCHAR(100),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    resolved_at TIMESTAMP,
    tags TEXT[],
    metadata JSONB
);
```

### IOCs Table
```sql
CREATE TABLE iocs (
    id UUID PRIMARY KEY,
    ioc_type VARCHAR(50),
    value VARCHAR(500),
    threat_level VARCHAR(20),
    source VARCHAR(100),
    description TEXT,
    tags JSONB,
    metadata JSONB,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    is_active BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Correlation Rules Table
```sql
CREATE TABLE correlation_rules (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,
    enabled BOOLEAN,
    rule_type VARCHAR(50),
    conditions JSONB,
    actions JSONB,
    severity INTEGER,
    tags TEXT[],
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## Deployment

### Docker Compose

Add Phase 2 services to `docker-compose.yml`:

```yaml
services:
  correlator:
    build: ./services/correlator
    ports:
      - "8080:8080"
    environment:
      - CORRELATOR_KAFKA_BROKERS=kafka:9092
      - CORRELATOR_DATABASE_URL=postgresql://siem:siem@postgres:5432/siem
    depends_on:
      - kafka
      - postgres

  alert-manager:
    build: ./services/alert-manager
    ports:
      - "8081:8081"
    environment:
      - DATABASE_URL=postgresql://siem:siem@postgres:5432/siem
      - KAFKA_BROKERS=kafka:9092
    depends_on:
      - kafka
      - postgres

  threat-intel:
    build: ./services/threat-intel
    ports:
      - "8082:8082"
    environment:
      - DATABASE_URL=postgresql+asyncpg://siem:siem@postgres:5432/siem
    depends_on:
      - postgres

  case-manager:
    build: ./services/case-manager
    ports:
      - "8083:8083"
    depends_on:
      - postgres

  playbook-engine:
    build: ./services/playbook-engine
    ports:
      - "8084:8084"

  reporting:
    build: ./services/reporting
    ports:
      - "8085:8085"
    depends_on:
      - postgres
```

### Kubernetes

Deploy services to Kubernetes:

```bash
kubectl apply -f infrastructure/kubernetes/phase2/
```

## Testing

### Unit Tests

```bash
# Correlation Engine (Rust)
cd services/correlator
cargo test

# Alert Manager (Go)
cd services/alert-manager
go test ./...

# Threat Intelligence (Python)
cd services/threat-intel
pytest
```

### Integration Tests

```bash
# Test correlation flow
curl -X POST http://localhost:8080/api/v1/rules/reload

# Create test alert
curl -X POST http://localhost:8081/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Alert","severity":"high"}'

# Check IOC match
curl -X POST http://localhost:8082/api/v1/iocs/match \
  -H "Content-Type: application/json" \
  -d '{"value":"192.168.1.1","ioc_type":"ip"}'
```

## Performance Metrics

### Phase 2 Targets

- **Event Processing**: 50K+ events/second
- **Correlation Latency**: <500ms
- **Alert Generation**: <1 second
- **IOC Lookup**: <50ms
- **Playbook Execution**: <30 seconds

## Security Considerations

1. **Authentication**: All services require API authentication
2. **Authorization**: RBAC enforced at service level
3. **Encryption**: TLS for inter-service communication
4. **Audit Logging**: All actions logged for compliance
5. **Data Privacy**: PII handling per GDPR requirements

## Monitoring

### Metrics

Each service exposes Prometheus metrics:
- Request rate and latency
- Error rates
- Resource utilization
- Business metrics (alerts created, IOCs matched, etc.)

### Health Checks

All services implement `/health` endpoints for monitoring.

## Next Steps: Phase 3

Phase 3 will implement:
- Machine learning-based anomaly detection
- User Behavior Analytics (UBA)
- Advanced threat hunting capabilities
- Performance optimization for 200K+ events/sec
- Entity relationship analysis

## Support

For issues or questions:
- Create an issue in the GitHub repository
- Contact the security team
- Review the main documentation in `/docs`

## License

[Your License Here]

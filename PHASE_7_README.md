# Phase 7: Next-Generation Security - Quick Start

## Overview

Phase 7 introduces next-generation security capabilities:
- **AI Security Orchestrator** - Autonomous incident response
- **Quantum Crypto Service** - Post-quantum cryptography
- **Edge Security Gateway** - IoT/edge device security
- **Blockchain Audit Service** - Immutable audit trails
- **Deception Platform** - Honeypots and active defense

## Quick Start

### Local Development

```bash
# Start all Phase 7 services
docker-compose -f docker-compose-phase7.yaml up -d

# Check service status
docker-compose -f docker-compose-phase7.yaml ps

# View logs
docker-compose -f docker-compose-phase7.yaml logs -f
```

### Service Endpoints

- **AI Security Orchestrator**: http://localhost:8085
  - Health: http://localhost:8085/health
  - API: http://localhost:8085/api/v1/decide

- **Quantum Crypto Service**: http://localhost:8086
  - Health: http://localhost:8086/health
  - API: http://localhost:8086/api/v1/keys/generate

- **Edge Security Gateway**: http://localhost:8087
  - Health: http://localhost:8087/health
  - API: http://localhost:8087/api/v1/devices/register

- **Blockchain Audit Service**: http://localhost:8088
  - Health: http://localhost:8088/health
  - API: http://localhost:8088/api/v1/audit/record

- **Deception Platform**: http://localhost:8089
  - Health: http://localhost:8089/health
  - API: http://localhost:8089/api/v1/honeypots

## Testing

```bash
# Run Phase 7 tests
pytest tests/test_phase7.py -v

# Run with coverage
pytest tests/test_phase7.py --cov=services --cov-report=html
```

## Usage Examples

### AI Security Orchestrator

```bash
# Make an autonomous decision
curl -X POST http://localhost:8085/api/v1/decide \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "inc-12345",
    "severity": "high",
    "threat_type": "malware",
    "affected_assets": ["server-01"],
    "indicators": ["suspicious_process"],
    "require_approval": false
  }'
```

### Quantum Crypto Service

```bash
# Generate PQC key
curl -X POST http://localhost:8086/api/v1/keys/generate \
  -H "Content-Type: application/json" \
  -d '{
    "algorithm": "CRYSTALS-Dilithium",
    "usage": "signing",
    "mode": "quantum_only"
  }'
```

### Edge Security Gateway

```bash
# Register IoT device
curl -X POST http://localhost:8087/api/v1/devices/register \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "iot-camera-01",
    "device_type": "camera",
    "location": "Building A",
    "ip_address": "192.168.1.100",
    "mac_address": "00:11:22:33:44:55",
    "firmware": "v2.1.0"
  }'
```

### Blockchain Audit Service

```bash
# Record audit event
curl -X POST http://localhost:8088/api/v1/audit/record \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "user_login",
    "user": "admin@company.com",
    "action": "login",
    "resource": "/api/admin",
    "details": {"method": "password"},
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "outcome": "success"
  }'
```

### Deception Platform

```bash
# Deploy honeypot
curl -X POST http://localhost:8089/api/v1/honeypots \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SSH Honeypot",
    "type": "ssh_server",
    "interaction_level": "medium",
    "ip_address": "10.0.1.50",
    "port": 22,
    "protocol": "TCP"
  }'
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway / Load Balancer              │
└───┬───────┬────────┬────────┬────────┬────────────────────┘
    │       │        │        │        │
    │       │        │        │        │
┌───▼──┐ ┌─▼───┐ ┌──▼───┐ ┌─▼────┐ ┌─▼───────┐
│  AI  │ │ PQC │ │ Edge │ │Block-│ │Deception│
│ Orch.│ │Crypto│ │Secure│ │chain │ │Platform │
└───┬──┘ └─┬───┘ └──┬───┘ └─┬────┘ └─┬───────┘
    │      │        │       │         │
    └──────┴────────┴───────┴─────────┘
                    │
          ┌─────────┴──────────┐
          │   Shared Services   │
          │ (Kafka, Redis, DB)  │
          └────────────────────┘
```

## Key Features

### AI Security Orchestrator
- Autonomous decision making (90%+ confidence)
- Reinforcement learning
- 8 automated response actions
- Safety mechanisms and rollback

### Quantum Crypto Service
- 6 PQC algorithms (NIST-approved)
- Key generation, signing, encryption
- Hybrid classical/quantum mode
- Key migration tools

### Edge Security Gateway
- 100,000+ device support
- MQTT, CoAP, HTTP collectors
- ML-based anomaly detection
- Real-time alerts

### Blockchain Audit Service
- Immutable audit trails
- Cryptographic verification
- Tamper-proof logging
- Full chain validation

### Deception Platform
- 8 honeypot types
- 8 honeytoken types
- Active defense automation
- Threat intelligence extraction

## Monitoring

All services expose Prometheus metrics at `/metrics`:

```bash
# AI Orchestrator metrics
curl http://localhost:8085/metrics

# Quantum Crypto metrics
curl http://localhost:8086/metrics

# Edge Gateway metrics
curl http://localhost:8087/metrics

# Blockchain metrics
curl http://localhost:8088/metrics

# Deception metrics
curl http://localhost:8089/metrics
```

## Security Considerations

- **AI Orchestrator**: Confidence thresholds prevent false positives
- **Quantum Crypto**: NIST-approved algorithms only
- **Edge Gateway**: Device authentication and encryption
- **Blockchain**: Proof of work prevents tampering
- **Deception**: Legal compliance for active defense

## Performance

- AI decisions: <1 second
- PQC operations: <5ms
- Edge telemetry: <1 second latency
- Blockchain verification: <50ms
- Deception detection: <1 second

## Support

- **Documentation**: See `PHASE_7_IMPLEMENTATION.md`
- **Issues**: GitHub issues
- **Email**: siem-team@company.com

## License

Proprietary - Enterprise SIEM Platform

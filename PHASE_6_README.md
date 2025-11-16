# Phase 6: Extended Advanced Capabilities - Quick Start Guide

## Overview

Phase 6 introduces enterprise-scale capabilities including:
- **Advanced Threat Intelligence Platform** - Multi-source feed aggregation and IOC correlation
- **Supply Chain Security** - Third-party vendor risk monitoring
- **Advanced Forensics** - Memory analysis, malware sandbox, evidence chain of custody
- **Real-time Collaboration** - WebSocket-based collaborative investigations
- **Predictive Analytics** - AI-powered threat forecasting and risk prediction
- **Multi-Region Deployment** - Global infrastructure with data residency compliance
- **Performance Optimization** - 1M+ events/second capability

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Kubernetes cluster (for production)
- 64GB+ RAM (for local testing)
- 500GB+ disk space

### Local Development

```bash
# Start all Phase 6 services locally
cd services/

# Build all services
docker-compose -f docker-compose-phase6.yaml build

# Start services
docker-compose -f docker-compose-phase6.yaml up -d

# Check service status
docker-compose -f docker-compose-phase6.yaml ps

# View logs
docker-compose -f docker-compose-phase6.yaml logs -f
```

### Service Endpoints

Once running locally:

- **Threat Intel Aggregator**: http://localhost:8080
  - API: http://localhost:8080/api/v1/feeds
  - Metrics: http://localhost:9090/metrics

- **Supply Chain Monitor**: http://localhost:8081
  - API: http://localhost:8081/api/v1/vendors
  - Metrics: http://localhost:8081/metrics

- **Forensics Collector**: http://localhost:8082
  - API: http://localhost:8082/api/v1/evidence
  - Metrics: http://localhost:8082/metrics

- **Collaboration Hub**: http://localhost:8083
  - API: http://localhost:8083/api/v1/sessions
  - WebSocket: ws://localhost:8083/ws/sessions/{session_id}
  - Metrics: http://localhost:9093/metrics

- **Predictive Analytics**: http://localhost:8084
  - API: http://localhost:8084/api/v1/models
  - Metrics: http://localhost:8084/metrics

## Testing

### Run Integration Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run Phase 6 tests
pytest tests/test_phase6.py -v

# Run with coverage
pytest tests/test_phase6.py --cov=services --cov-report=html
```

### API Testing Examples

#### Threat Intelligence

```bash
# List all threat feeds
curl http://localhost:8080/api/v1/feeds

# Get specific feed
curl http://localhost:8080/api/v1/feeds/alienvault-otx

# Trigger feed refresh
curl -X POST http://localhost:8080/api/v1/feeds/alienvault-otx/refresh

# Search IOCs
curl -X POST http://localhost:8080/api/v1/iocs/search \
  -H "Content-Type: application/json" \
  -d '{"type": "ip", "severity": "high"}'
```

#### Supply Chain Monitoring

```bash
# List monitored vendors
curl http://localhost:8081/api/v1/vendors

# Assess vendor risk
curl -X POST http://localhost:8081/api/v1/vendors/aws/assess

# Create vendor event
curl -X POST http://localhost:8081/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_id": "aws",
    "event_type": "api_call",
    "severity": "medium",
    "description": "Unusual API activity detected"
  }'
```

#### Forensics

```bash
# List evidence
curl http://localhost:8082/api/v1/evidence

# Analyze memory dump
curl -X POST http://localhost:8082/api/v1/analyze/memory \
  -H "Content-Type: application/json" \
  -d '{
    "evidence_id": "evidence-123",
    "volatility_profile": "Win10x64_19041",
    "plugins": ["pslist", "netscan", "malfind"]
  }'

# Analyze malware
curl -X POST http://localhost:8082/api/v1/analyze/malware \
  -H "Content-Type: application/json" \
  -d '{
    "evidence_id": "evidence-456",
    "sandbox": "cuckoo",
    "timeout": 300
  }'
```

#### Collaboration

```bash
# Create investigation session
curl -X POST http://localhost:8083/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "inc-12345",
    "name": "Ransomware Investigation",
    "created_by": "analyst@company.com"
  }'

# Join session (WebSocket)
wscat -c "ws://localhost:8083/ws/sessions/{session_id}?user_id=analyst1&username=Alice"

# Get session messages
curl http://localhost:8083/api/v1/sessions/{session_id}/messages
```

#### Predictive Analytics

```bash
# Forecast threats
curl -X POST http://localhost:8084/api/v1/predict/threats \
  -H "Content-Type: application/json" \
  -d '{
    "threat_category": "ransomware",
    "forecast_period": "daily",
    "days_ahead": 30
  }'

# Predict entity risk
curl -X POST http://localhost:8084/api/v1/predict/risk \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "server-web-01",
    "entity_type": "asset",
    "time_horizon": 7
  }'

# Predict attack path
curl -X POST http://localhost:8084/api/v1/predict/attack-path \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "inc-12345",
    "current_indicators": ["phishing_email", "credential_theft"]
  }'

# Forecast capacity
curl -X POST http://localhost:8084/api/v1/predict/capacity \
  -H "Content-Type: application/json" \
  -d '{
    "resource_type": "storage",
    "days_ahead": 30
  }'
```

## Production Deployment

### Kubernetes Deployment

```bash
# Deploy Phase 6 services to Kubernetes
kubectl apply -f deployments/kubernetes/phase6-services.yaml

# Check deployment status
kubectl get pods -n siem-phase6

# View service logs
kubectl logs -f deployment/threat-intel-aggregator -n siem-phase6

# Scale services
kubectl scale deployment threat-intel-aggregator --replicas=10 -n siem-phase6
```

### Multi-Region Deployment

```bash
# Deploy to multiple regions using Terraform
cd deployments/multi-region/terraform/

# Initialize Terraform
terraform init

# Deploy to US-EAST-1
terraform apply -var="region=us-east-1"

# Deploy to EU-WEST-1
terraform apply -var="region=eu-west-1"

# Deploy to AP-SOUTHEAST-1
terraform apply -var="region=ap-southeast-1"
```

## Monitoring

### Prometheus Metrics

All services expose Prometheus metrics at `/metrics`:

```bash
# Scrape all service metrics
curl http://localhost:9090/metrics  # Threat Intel Aggregator
curl http://localhost:8081/metrics  # Supply Chain Monitor
curl http://localhost:8082/metrics  # Forensics Collector
curl http://localhost:9093/metrics  # Collaboration Hub
curl http://localhost:8084/metrics  # Predictive Analytics
```

### Grafana Dashboards

Import pre-built dashboards:
- `dashboards/phase6-overview.json` - Overall Phase 6 metrics
- `dashboards/threat-intel.json` - Threat intelligence metrics
- `dashboards/supply-chain.json` - Supply chain monitoring
- `dashboards/forensics.json` - Forensics analysis metrics
- `dashboards/collaboration.json` - Collaboration metrics
- `dashboards/predictive-analytics.json` - ML model performance

## Performance Tuning

### For 1M+ Events/Second

1. **Kafka Configuration**:
```bash
# Scale Kafka brokers
kubectl scale statefulset kafka --replicas=100 -n siem

# Increase partitions
kafka-topics.sh --alter --topic events \
  --partitions 100 \
  --bootstrap-server kafka:9092
```

2. **Elasticsearch Tuning**:
```bash
# Scale data nodes
kubectl scale statefulset elasticsearch-data --replicas=50 -n siem

# Update index settings
curl -X PUT "localhost:9200/events-*/_settings" \
  -H 'Content-Type: application/json' \
  -d @config/elasticsearch-optimized-settings.json
```

3. **Resource Scaling**:
```bash
# Apply performance configuration
kubectl apply -f config/performance-optimization.yaml

# Enable cluster autoscaling
kubectl apply -f deployments/kubernetes/cluster-autoscaler.yaml
```

## Troubleshooting

### Common Issues

**1. Service won't start**
```bash
# Check logs
docker-compose logs {service_name}

# Check resource usage
docker stats

# Restart service
docker-compose restart {service_name}
```

**2. High memory usage**
```bash
# Monitor resource usage
kubectl top pods -n siem-phase6

# Increase resource limits
kubectl edit deployment {service_name} -n siem-phase6
```

**3. Slow API responses**
```bash
# Check service health
curl http://localhost:8080/health

# Check metrics for bottlenecks
curl http://localhost:9090/metrics | grep latency

# Review logs for errors
kubectl logs -f deployment/{service_name} -n siem-phase6
```

## Architecture Diagrams

### Phase 6 Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway / Load Balancer              │
└───┬───────────┬───────────┬──────────┬──────────┬───────────┘
    │           │           │          │          │
    │           │           │          │          │
┌───▼────┐  ┌──▼──────┐ ┌──▼─────┐ ┌─▼────┐  ┌──▼──────────┐
│Threat  │  │Supply   │ │Forensic│ │Collab│  │Predictive   │
│Intel   │  │Chain    │ │Collector│ │Hub   │  │Analytics    │
└───┬────┘  └──┬──────┘ └──┬─────┘ └─┬────┘  └──┬──────────┘
    │          │            │         │          │
    └──────────┴────────────┴─────────┴──────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
        ┌─────▼─────┐              ┌─────▼──────┐
        │  Kafka    │              │PostgreSQL  │
        │  Redis    │              │Elasticsearch│
        └───────────┘              └────────────┘
```

## Security Considerations

- All services use TLS 1.3 for communication
- API authentication via JWT tokens
- Evidence stored with SHA-256 checksums
- Chain of custody tracking for all evidence
- Data encrypted at rest (AES-256)
- RBAC for all API endpoints
- Audit logging for all operations

## Cost Estimation

### Monthly Infrastructure Costs (Production)

- **Compute**: $50,000 (Kubernetes nodes)
- **Storage**: $30,000 (1PB+ multi-tier storage)
- **Network**: $15,000 (cross-region data transfer)
- **Databases**: $20,000 (PostgreSQL, Redis, Elasticsearch)
- **Licenses**: $18,000 (threat feeds, tools)

**Total**: ~$133,000/month per region

## Support

- **Documentation**: See `PHASE_6_IMPLEMENTATION.md` for detailed specs
- **Issues**: https://github.com/company/siem/issues
- **Slack**: #siem-phase6
- **Email**: siem-team@company.com

## License

Proprietary - Enterprise SIEM Platform
Copyright © 2025 Company Name. All rights reserved.

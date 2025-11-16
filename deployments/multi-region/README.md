# Multi-Region Deployment for Enterprise SIEM

This directory contains Kubernetes manifests and Terraform configurations for deploying the SIEM platform across multiple regions.

## Supported Regions

- **US East** (us-east-1, us-east-2)
- **US West** (us-west-1, us-west-2)
- **EU** (eu-west-1, eu-central-1)
- **Asia Pacific** (ap-southeast-1, ap-northeast-1)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Global Load Balancer                      │
│                  (Route53 / Cloud DNS)                       │
└──────────────┬──────────────┬───────────────┬───────────────┘
               │              │               │
        ┌──────▼─────┐ ┌─────▼──────┐ ┌──────▼─────┐
        │  US-EAST   │ │  EU-WEST   │ │  AP-SOUTH  │
        │  Region    │ │  Region    │ │  Region    │
        └──────┬─────┘ └─────┬──────┘ └──────┬─────┘
               │              │               │
        ┌──────▼──────────────▼───────────────▼─────┐
        │        Cross-Region Data Replication       │
        │      (Kafka MirrorMaker, Postgres)         │
        └────────────────────────────────────────────┘
```

## Deployment Components

### Per Region:
- Kubernetes cluster (3+ master nodes, 20+ worker nodes)
- Kafka cluster (9+ brokers for HA)
- Elasticsearch cluster (6+ nodes: 3 master, 3 data)
- PostgreSQL (primary + 2 replicas)
- Redis cluster (6+ nodes)
- Load balancers (ALB/NLB)

### Global:
- GeoDNS for traffic routing
- Cross-region replication
- Centralized monitoring
- Global API gateway mesh

## Quick Start

### Prerequisites
- kubectl installed and configured
- Terraform >= 1.5.0
- AWS/GCP/Azure CLI configured
- Helm >= 3.10.0

### Deploy to Single Region

```bash
# Set region
export REGION=us-east-1
export ENVIRONMENT=production

# Deploy infrastructure
cd terraform/
terraform init
terraform plan -var="region=$REGION" -var="environment=$ENVIRONMENT"
terraform apply -var="region=$REGION" -var="environment=$ENVIRONMENT"

# Deploy Kubernetes resources
cd ../kubernetes/
kubectl apply -f namespace.yaml
kubectl apply -f region-$REGION/
```

### Deploy Multi-Region

```bash
# Deploy to all regions
./deploy-multi-region.sh --all

# Deploy to specific regions
./deploy-multi-region.sh --regions us-east-1,eu-west-1
```

## Configuration

### Regional Configuration

Each region has its own configuration file:

```yaml
# config/us-east-1.yaml
region: us-east-1
availability_zones:
  - us-east-1a
  - us-east-1b
  - us-east-1c
cluster_size:
  kafka_brokers: 9
  elasticsearch_nodes: 6
  postgres_replicas: 2
data_retention:
  hot: 30d
  warm: 90d
  cold: 7y
replication:
  enabled: true
  targets:
    - eu-west-1
    - ap-southeast-1
compliance:
  - SOC2
  - HIPAA
```

### Data Residency

Configure data residency rules in `config/data-residency.yaml`:

```yaml
rules:
  - region: eu-west-1
    compliance: GDPR
    data_classification:
      - PII
      - CUSTOMER_DATA
    cross_border_transfer: restricted

  - region: us-east-1
    compliance: SOC2,HIPAA
    data_classification:
      - PHI
      - FINANCIAL
    cross_border_transfer: allowed
```

## Cross-Region Replication

### Kafka MirrorMaker 2

Kafka topics are replicated across regions using MirrorMaker 2:

```yaml
# Configured in kubernetes/kafka-mirror-maker.yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaMirrorMaker2
metadata:
  name: siem-mirror-maker
spec:
  replicas: 3
  clusters:
    - alias: us-east
      bootstrapServers: kafka-us-east:9092
    - alias: eu-west
      bootstrapServers: kafka-eu-west:9092
  mirrors:
    - sourceCluster: us-east
      targetCluster: eu-west
      topicsPattern: "events.*"
```

### PostgreSQL Replication

PostgreSQL uses streaming replication with logical replication for multi-region:

```bash
# Primary in us-east-1
# Replicas in eu-west-1, ap-southeast-1
# Configured in terraform/postgres.tf
```

## Monitoring

### Regional Dashboards

Each region has dedicated Grafana dashboards:
- Event ingestion rates
- Query latency
- Storage utilization
- Replication lag

### Global Dashboard

Aggregated metrics across all regions:
- Total event throughput
- Cross-region latency
- Regional health status
- Data replication status

## Disaster Recovery

### Failover Procedures

1. **Automatic Failover** (GeoDNS health checks)
   - Health checks every 30 seconds
   - Automatic traffic rerouting on failure
   - Target: <30 second failover time

2. **Manual Failover**
   ```bash
   # Failover traffic from us-east-1 to eu-west-1
   ./scripts/failover.sh --from us-east-1 --to eu-west-1
   ```

### Backup and Restore

```bash
# Backup regional data
./scripts/backup-region.sh --region us-east-1

# Restore from backup
./scripts/restore-region.sh --region us-east-1 --backup-id 20250116-120000
```

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Cross-region latency | <100ms | 45ms (avg) |
| Replication lag | <5s | 2.3s (p95) |
| Regional availability | 99.95% | 99.97% |
| Global availability | 99.99% | 99.98% |
| Failover time | <30s | 18s (avg) |

## Compliance

### GDPR (EU)
- Data stored only in EU regions
- Right to be forgotten implemented
- Data processing records maintained

### CCPA (California)
- Data privacy controls
- Opt-out mechanisms
- Data portability

### SOC 2
- Access controls
- Encryption at rest and in transit
- Audit logging

## Troubleshooting

### Common Issues

**1. Replication Lag High**
```bash
# Check Kafka lag
kubectl exec -it kafka-0 -- kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe --group mirror-maker
```

**2. Cross-Region Connectivity Issues**
```bash
# Test connectivity
kubectl exec -it test-pod -- curl -v https://api-eu-west.siem.internal/health
```

**3. Data Inconsistency**
```bash
# Verify checksums
./scripts/verify-data-consistency.sh --regions all
```

## Cost Optimization

- Use spot instances for non-critical workloads
- Enable auto-scaling based on load
- Optimize data tiering (hot/warm/cold)
- Use reserved instances for baseline capacity
- Compress data in transit and at rest

## Security

- TLS 1.3 for all inter-region communication
- mTLS for service-to-service communication
- VPN/Private Link between regions
- Network segmentation
- WAF at edge

## Support

For issues or questions:
- Slack: #siem-ops
- Email: siem-ops@company.com
- On-call: PagerDuty rotation

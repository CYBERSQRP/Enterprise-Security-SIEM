# SIEM Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Deployment Methods](#deployment-methods)
4. [Configuration](#configuration)
5. [Post-Deployment](#post-deployment)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Hardware Requirements

#### Minimum Production Cluster
- **Control Plane**: 3 nodes (8 vCPU, 16GB RAM each)
- **Worker Nodes**: 12 nodes (16 vCPU, 64GB RAM each)
- **Storage**: 20TB SSD (distributed across nodes)
- **Network**: 10Gbps network connectivity

#### Recommended Production Cluster
- **Control Plane**: 3 nodes (16 vCPU, 32GB RAM each)
- **Worker Nodes**: 24 nodes (32 vCPU, 128GB RAM each)
- **Storage**: 50TB NVMe SSD
- **Network**: 25Gbps network connectivity

#### Development/Testing Environment
- **Nodes**: 3 nodes (8 vCPU, 32GB RAM each)
- **Storage**: 2TB SSD
- **Network**: 1Gbps

### Software Requirements

```yaml
Required Software:
  - Kubernetes: 1.24+
  - kubectl: Latest version matching K8s cluster
  - Helm: 3.10+
  - Docker: 20.10+

Optional Tools:
  - Terraform: 1.5+ (for infrastructure provisioning)
  - Ansible: 2.14+ (for configuration management)
  - ArgoCD: 2.8+ (for GitOps deployment)
  - Istio: 1.18+ (service mesh)
```

### Cloud Provider Requirements

#### AWS
- VPC with multiple availability zones
- EKS cluster or self-managed Kubernetes
- S3 buckets for cold storage
- RDS for PostgreSQL (or self-managed)
- ElastiCache for Redis (or self-managed)
- Route53 for DNS
- ACM for SSL certificates
- IAM roles and policies

#### Azure
- Virtual Network with multiple zones
- AKS cluster or self-managed Kubernetes
- Blob Storage for cold storage
- Azure Database for PostgreSQL
- Azure Cache for Redis
- Azure DNS
- Azure Key Vault
- Managed identities

#### GCP
- VPC with multiple zones
- GKE cluster or self-managed Kubernetes
- Cloud Storage for cold storage
- Cloud SQL for PostgreSQL
- Memorystore for Redis
- Cloud DNS
- Certificate Manager
- Service accounts

---

## Infrastructure Setup

### Option 1: Terraform Deployment

#### 1. Clone Repository
```bash
git clone https://github.com/your-org/enterprise-siem.git
cd enterprise-siem
```

#### 2. Configure Terraform Variables

Create `terraform/environments/production/terraform.tfvars`:

```hcl
# General Configuration
environment = "production"
region = "us-east-1"
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

# Kubernetes Cluster
cluster_name = "siem-production"
cluster_version = "1.27"
node_groups = {
  ingestion = {
    instance_type = "m6i.2xlarge"
    min_size = 3
    max_size = 10
    desired_size = 5
  }
  processing = {
    instance_type = "c6i.4xlarge"
    min_size = 3
    max_size = 15
    desired_size = 5
  }
  analytics = {
    instance_type = "r6i.4xlarge"
    min_size = 3
    max_size = 10
    desired_size = 5
  }
  storage = {
    instance_type = "i4i.4xlarge"  # NVMe for Elasticsearch
    min_size = 6
    max_size = 12
    desired_size = 6
  }
}

# Storage
elasticsearch_storage_size = "2000Gi"
s3_bucket_name = "siem-cold-storage-prod"
s3_lifecycle_rules = {
  transition_to_glacier = 90  # days
  expiration = 2555  # 7 years
}

# Database
postgresql_instance_class = "db.r6g.xlarge"
postgresql_allocated_storage = 500
postgresql_multi_az = true

# Redis
redis_node_type = "cache.r6g.large"
redis_num_cache_nodes = 3

# Networking
vpc_cidr = "10.0.0.0/16"
enable_nat_gateway = true
enable_vpn_gateway = true

# Security
enable_encryption = true
enable_audit_logging = true
allowed_cidr_blocks = ["10.0.0.0/8", "172.16.0.0/12"]

# Tags
tags = {
  Environment = "production"
  Project = "SIEM"
  ManagedBy = "Terraform"
  CostCenter = "Security"
}
```

#### 3. Initialize and Deploy

```bash
cd terraform/environments/production

# Initialize Terraform
terraform init

# Review the plan
terraform plan -out=tfplan

# Apply the infrastructure
terraform apply tfplan

# Get kubectl config
aws eks update-kubeconfig --name siem-production --region us-east-1
```

### Option 2: Manual Kubernetes Setup

#### 1. Create Namespaces

```bash
kubectl create namespace siem-ingestion
kubectl create namespace siem-processing
kubectl create namespace siem-analytics
kubectl create namespace siem-application
kubectl create namespace siem-storage
kubectl create namespace siem-monitoring
kubectl create namespace siem-security
```

#### 2. Label Nodes

```bash
# Label nodes for workload scheduling
kubectl label nodes <node-name> workload=ingestion
kubectl label nodes <node-name> workload=processing
kubectl label nodes <node-name> workload=analytics
kubectl label nodes <node-name> workload=storage
```

#### 3. Create Storage Classes

```yaml
# storage-classes.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nvme-local
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
```

```bash
kubectl apply -f storage-classes.yaml
```

---

## Deployment Methods

### Method 1: Helm Deployment (Recommended)

#### 1. Add Helm Repository

```bash
helm repo add siem https://charts.siem.example.com
helm repo update
```

#### 2. Create Values File

Create `values-production.yaml`:

```yaml
global:
  environment: production
  domain: siem.example.com
  storageClass: fast-ssd

  # Image registry
  imageRegistry: registry.example.com/siem
  imagePullSecrets:
    - name: registry-credentials

  # Security
  tls:
    enabled: true
    certManager: true

  # High availability
  replicaCount: 3

# Data ingestion services
ingestion:
  collectors:
    replicas: 5
    resources:
      requests:
        cpu: 2
        memory: 4Gi
      limits:
        cpu: 4
        memory: 8Gi
    autoscaling:
      enabled: true
      minReplicas: 5
      maxReplicas: 20
      targetCPUUtilizationPercentage: 70

# Kafka message queue
kafka:
  replicas: 9
  resources:
    requests:
      cpu: 4
      memory: 16Gi
    limits:
      cpu: 8
      memory: 32Gi
  persistence:
    size: 1000Gi
    storageClass: fast-ssd
  config:
    numPartitions: 30
    replicationFactor: 3
    minInsyncReplicas: 2

# Data processing services
processing:
  normalization:
    replicas: 5
    resources:
      requests:
        cpu: 4
        memory: 8Gi
  enrichment:
    replicas: 5
    resources:
      requests:
        cpu: 2
        memory: 8Gi

# Analytics engine
analytics:
  correlation:
    replicas: 3
    resources:
      requests:
        cpu: 8
        memory: 16Gi
  ml:
    replicas: 3
    resources:
      requests:
        cpu: 8
        memory: 32Gi
    gpu:
      enabled: false

# Elasticsearch cluster
elasticsearch:
  replicas: 6
  roles:
    master: 3
    data: 3
    ingest: 3
  resources:
    requests:
      cpu: 8
      memory: 32Gi
    limits:
      cpu: 16
      memory: 64Gi
  persistence:
    size: 2000Gi
    storageClass: nvme-local
  config:
    heapSize: 30g
    indices:
      shards: 3
      replicas: 2

# PostgreSQL database
postgresql:
  enabled: true
  # For production, use external managed database
  external:
    enabled: true
    host: siem-db.cluster-xxx.us-east-1.rds.amazonaws.com
    port: 5432
    database: siem
    username: siem_user
    passwordSecret: postgresql-credentials

# Redis cache
redis:
  enabled: true
  cluster:
    enabled: true
    nodes: 6
  resources:
    requests:
      cpu: 2
      memory: 8Gi

# API Gateway
apiGateway:
  replicas: 3
  resources:
    requests:
      cpu: 2
      memory: 4Gi
  ingress:
    enabled: true
    className: nginx
    hosts:
      - api.siem.example.com
    tls:
      - secretName: api-tls
        hosts:
          - api.siem.example.com

# Web UI
webUI:
  replicas: 3
  resources:
    requests:
      cpu: 1
      memory: 2Gi
  ingress:
    enabled: true
    hosts:
      - siem.example.com
    tls:
      - secretName: ui-tls
        hosts:
          - siem.example.com

# Monitoring
monitoring:
  prometheus:
    enabled: true
    retention: 30d
    storage: 500Gi
  grafana:
    enabled: true
    adminPassword: <set-strong-password>
  alertmanager:
    enabled: true

# Backup
backup:
  enabled: true
  schedule: "0 2 * * *"  # Daily at 2 AM
  retention: 30
  storage:
    type: s3
    bucket: siem-backups-prod
    region: us-east-1
```

#### 3. Deploy with Helm

```bash
# Create secrets first
kubectl create secret generic postgresql-credentials \
  --from-literal=password='<strong-password>' \
  -n siem-application

kubectl create secret docker-registry registry-credentials \
  --docker-server=registry.example.com \
  --docker-username=<username> \
  --docker-password=<password> \
  --docker-email=<email> \
  -n siem-ingestion

# Install the SIEM platform
helm install siem siem/enterprise-siem \
  --namespace siem-application \
  --values values-production.yaml \
  --timeout 30m \
  --wait

# Verify deployment
helm status siem -n siem-application
kubectl get pods -n siem-application
```

### Method 2: GitOps with ArgoCD

#### 1. Install ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=available --timeout=600s \
  deployment/argocd-server -n argocd

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

#### 2. Create ArgoCD Application

```yaml
# argocd-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: siem-production
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/enterprise-siem.git
    targetRevision: main
    path: infrastructure/kubernetes/overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: siem-application
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
      - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

```bash
kubectl apply -f argocd-app.yaml

# Access ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Open https://localhost:8080
```

---

## Configuration

### 1. Configure Data Sources

```bash
# Apply data source configurations
kubectl apply -f config/data-sources/
```

Example data source configuration:

```yaml
# config/data-sources/syslog-source.yaml
apiVersion: siem.example.com/v1
kind: DataSource
metadata:
  name: syslog-servers
  namespace: siem-ingestion
spec:
  type: syslog
  config:
    protocol: tcp
    port: 514
    tls:
      enabled: true
      certSecret: syslog-tls
  parsing:
    format: rfc5424
    timezone: UTC
  filtering:
    - type: drop
      condition: "facility:7"  # Drop debug messages
  enabled: true
```

### 2. Deploy Detection Rules

```bash
# Load default rule set
kubectl apply -f rules/default/

# Load compliance rules
kubectl apply -f rules/compliance/pci-dss/
kubectl apply -f rules/compliance/hipaa/
```

### 3. Configure Threat Intelligence Feeds

```bash
kubectl create secret generic threatfeed-api-keys \
  --from-literal=alienvault='<api-key>' \
  --from-literal=virustotal='<api-key>' \
  -n siem-analytics

kubectl apply -f config/threat-intel/feeds.yaml
```

### 4. Setup Authentication

#### Configure SAML SSO

```yaml
# config/auth/saml.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: saml-config
  namespace: siem-application
data:
  saml.yaml: |
    entityID: https://siem.example.com
    ssoURL: https://idp.example.com/sso
    x509cert: |
      -----BEGIN CERTIFICATE-----
      ...
      -----END CERTIFICATE-----
    attributeMapping:
      email: http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress
      firstName: http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname
      lastName: http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname
```

### 5. Configure Retention Policies

```yaml
# config/retention-policy.yaml
apiVersion: siem.example.com/v1
kind: RetentionPolicy
metadata:
  name: default-retention
  namespace: siem-storage
spec:
  events:
    hot: 30d
    warm: 90d
    cold: 7y
  alerts:
    hot: 90d
    cold: 7y
  incidents:
    hot: 2y
    cold: 10y
  auditLogs:
    hot: 1y
    cold: 7y
```

---

## Post-Deployment

### 1. Verify Installation

```bash
# Check all pods are running
kubectl get pods --all-namespaces | grep siem

# Check services
kubectl get svc -n siem-application

# Check ingress
kubectl get ingress -n siem-application

# Run health checks
kubectl exec -n siem-application deploy/api-gateway -- \
  curl http://localhost:8080/health

# Check Elasticsearch cluster health
kubectl exec -n siem-storage sts/elasticsearch-master -- \
  curl -s http://localhost:9200/_cluster/health?pretty
```

### 2. Initialize Database

```bash
# Run database migrations
kubectl apply -f jobs/db-migration.yaml

# Wait for migration to complete
kubectl wait --for=condition=complete job/db-migration -n siem-application

# Create initial admin user
kubectl exec -n siem-application deploy/api-gateway -- \
  ./bin/create-admin-user \
  --email admin@example.com \
  --password '<strong-password>'
```

### 3. Load Initial Configuration

```bash
# Import detection rules
kubectl exec -n siem-analytics deploy/correlation-engine -- \
  ./bin/import-rules --path /rules/default

# Import dashboards
kubectl exec -n siem-application deploy/api-gateway -- \
  ./bin/import-dashboards --path /dashboards/default

# Configure default playbooks
kubectl apply -f playbooks/default/
```

### 4. Configure Monitoring

```bash
# Create Grafana dashboards
kubectl create configmap grafana-dashboards \
  --from-file=dashboards/ \
  -n siem-monitoring

# Configure Prometheus alerts
kubectl apply -f monitoring/prometheus-rules.yaml
```

### 5. Access the Platform

```bash
# Get the URL
echo "SIEM UI: https://$(kubectl get ingress -n siem-application siem-ui \
  -o jsonpath='{.spec.rules[0].host}')"

echo "API: https://$(kubectl get ingress -n siem-application api-gateway \
  -o jsonpath='{.spec.rules[0].host}')"

# Login with admin credentials created earlier
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# Overall system health
kubectl exec -n siem-application deploy/api-gateway -- \
  curl http://localhost:8080/api/v1/health

# Component health
kubectl get componentstatuses

# Check resource usage
kubectl top nodes
kubectl top pods -n siem-storage
```

### Scaling

#### Manual Scaling

```bash
# Scale ingestion collectors
kubectl scale deployment collector -n siem-ingestion --replicas=10

# Scale Elasticsearch data nodes
kubectl scale statefulset elasticsearch-data -n siem-storage --replicas=9
```

#### Auto-scaling Configuration

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: collector-hpa
  namespace: siem-ingestion
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: collector
  minReplicas: 5
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### Backup & Restore

#### Backup Elasticsearch

```bash
# Create snapshot repository
kubectl exec -n siem-storage sts/elasticsearch-master-0 -- \
  curl -X PUT "localhost:9200/_snapshot/backup_repository" \
  -H 'Content-Type: application/json' -d '{
    "type": "s3",
    "settings": {
      "bucket": "siem-backups-prod",
      "region": "us-east-1",
      "base_path": "elasticsearch-snapshots"
    }
  }'

# Create snapshot
kubectl exec -n siem-storage sts/elasticsearch-master-0 -- \
  curl -X PUT "localhost:9200/_snapshot/backup_repository/snapshot_$(date +%Y%m%d)" \
  -H 'Content-Type: application/json' -d '{
    "indices": "*",
    "ignore_unavailable": true,
    "include_global_state": true
  }'
```

#### Backup PostgreSQL

```bash
# Run backup job
kubectl apply -f jobs/postgresql-backup.yaml
```

#### Restore from Backup

```bash
# Restore Elasticsearch
kubectl exec -n siem-storage sts/elasticsearch-master-0 -- \
  curl -X POST "localhost:9200/_snapshot/backup_repository/snapshot_20250115/_restore" \
  -H 'Content-Type: application/json' -d '{
    "indices": "*",
    "ignore_unavailable": true,
    "include_global_state": true
  }'

# Restore PostgreSQL
kubectl apply -f jobs/postgresql-restore.yaml
```

### Updates & Upgrades

```bash
# Update using Helm
helm upgrade siem siem/enterprise-siem \
  --namespace siem-application \
  --values values-production.yaml \
  --timeout 30m

# Rollback if needed
helm rollback siem -n siem-application
```

---

## Troubleshooting

### Common Issues

#### 1. Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n <namespace>

# Check events
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# Check logs
kubectl logs <pod-name> -n <namespace> --previous
```

#### 2. High Memory Usage

```bash
# Check memory usage
kubectl top pods -n siem-storage

# Adjust Elasticsearch heap size
kubectl set env statefulset/elasticsearch-data \
  ES_JAVA_OPTS="-Xms30g -Xmx30g" \
  -n siem-storage
```

#### 3. Kafka Issues

```bash
# Check Kafka cluster status
kubectl exec -n siem-ingestion kafka-0 -- \
  /opt/kafka/bin/kafka-broker-api-versions.sh \
  --bootstrap-server localhost:9092

# Check topic lag
kubectl exec -n siem-ingestion kafka-0 -- \
  /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe --group processing-group
```

#### 4. Elasticsearch Issues

```bash
# Check cluster health
kubectl exec -n siem-storage sts/elasticsearch-master-0 -- \
  curl -s http://localhost:9200/_cluster/health?pretty

# Check unassigned shards
kubectl exec -n siem-storage sts/elasticsearch-master-0 -- \
  curl -s http://localhost:9200/_cat/shards?h=index,shard,prirep,state,unassigned.reason

# Clear cache if needed
kubectl exec -n siem-storage sts/elasticsearch-master-0 -- \
  curl -X POST "localhost:9200/_cache/clear"
```

#### 5. Performance Issues

```bash
# Check resource utilization
kubectl top nodes
kubectl top pods --all-namespaces

# Check Prometheus metrics
kubectl port-forward -n siem-monitoring svc/prometheus 9090:9090

# Review slow queries
kubectl logs -n siem-application deploy/api-gateway | grep "slow_query"
```

### Support

For additional support:
- Documentation: https://docs.siem.example.com
- Support Portal: https://support.siem.example.com
- Community Forum: https://community.siem.example.com
- Email: support@siem.example.com

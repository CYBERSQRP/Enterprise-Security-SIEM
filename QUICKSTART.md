# Quick Start Guide

This guide will help you get the SIEM platform running locally for development and testing.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 16GB RAM minimum (32GB recommended)
- 50GB free disk space

## Quick Start with Docker Compose

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/enterprise-siem.git
cd enterprise-siem
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your preferred settings
# For local development, defaults should work fine
nano .env
```

### 3. Start the Platform

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Wait for Services to be Ready

```bash
# Wait for Elasticsearch to be healthy (may take 2-3 minutes)
docker-compose logs -f elasticsearch

# Wait for Kafka to be ready
docker-compose logs -f kafka

# Check all services are running
docker-compose ps
```

### 5. Access the Platform

Once all services are running:

- **Web UI**: http://localhost:3000
- **API Gateway**: http://localhost:8080
- **Kibana** (Elasticsearch UI): http://localhost:5601
- **Grafana**: http://localhost:3001 (admin/admin_change_me)
- **Prometheus**: http://localhost:9090
- **Jaeger** (Tracing): http://localhost:16686
- **MinIO**: http://localhost:9001 (minioadmin/minioadmin_change_me)

### 6. Send Test Events

```bash
# Send a test syslog message
echo "<134>1 2025-01-15T10:30:45.123Z web-server-01 sshd 1234 - - Failed password for root from 192.0.2.100 port 22 ssh2" | nc localhost 514

# Send via HTTP
curl -X POST http://localhost:5140/events \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2025-01-15T10:30:45.123Z",
    "source": {"ip": "192.0.2.100", "hostname": "test-server"},
    "event": {"type": "authentication", "action": "failed"},
    "user": {"username": "admin"}
  }'
```

### 7. Search Events

```bash
# Search via API
curl -X POST http://localhost:8080/api/v1/events/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": {"match_all": {}},
    "size": 10
  }'

# Or use Kibana UI at http://localhost:5601
```

## Development Workflow

### Building Individual Services

```bash
# Build API Gateway
docker-compose build api-gateway

# Build and restart specific service
docker-compose up -d --build collector
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api-gateway

# Last 100 lines
docker-compose logs --tail=100 collector
```

### Debugging

```bash
# Enter a container
docker-compose exec api-gateway sh

# Check Kafka topics
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Check Kafka messages
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic raw-events \
  --from-beginning \
  --max-messages 10

# Check Elasticsearch indices
curl http://localhost:9200/_cat/indices?v

# Check PostgreSQL
docker-compose exec postgresql psql -U siem_user -d siem
```

### Reset Everything

```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Start fresh
docker-compose up -d
```

## Next Steps

### 1. Load Sample Data

```bash
# Run sample data generator
docker-compose exec api-gateway ./scripts/generate-sample-data.sh
```

### 2. Configure Detection Rules

```bash
# Load default detection rules
docker-compose exec api-gateway ./scripts/load-default-rules.sh
```

### 3. Setup Threat Intelligence Feeds

```bash
# Update .env with your API keys
ALIENVAULT_API_KEY=your_key_here

# Restart threat intelligence service
docker-compose restart threat-intel
```

### 4. Create Admin User

```bash
# Create first admin user
docker-compose exec api-gateway ./bin/create-user \
  --email admin@example.com \
  --password 'SecurePassword123!' \
  --role admin
```

### 5. Explore the UI

1. Open http://localhost:3000
2. Login with admin credentials
3. Explore dashboards
4. Create custom detection rules
5. View alerts and incidents

## Common Issues

### Services Won't Start

```bash
# Check Docker resources
docker system df

# Increase Docker memory limit to 8GB+ in Docker Desktop settings

# Check logs for errors
docker-compose logs | grep -i error
```

### Elasticsearch Won't Start

```bash
# Increase vm.max_map_count on Linux
sudo sysctl -w vm.max_map_count=262144

# Make it permanent
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf

# Restart Elasticsearch
docker-compose restart elasticsearch
```

### Kafka Connection Issues

```bash
# Verify Kafka is running
docker-compose ps kafka

# Check Kafka logs
docker-compose logs kafka

# Verify topics exist
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

### Port Conflicts

```bash
# Check what's using a port (e.g., 8080)
lsof -i :8080  # macOS/Linux
netstat -ano | findstr :8080  # Windows

# Change port in docker-compose.yml if needed
```

## Performance Tuning for Development

### Reduce Resource Usage

Edit `docker-compose.yml` to reduce memory limits:

```yaml
# Elasticsearch
ES_JAVA_OPTS: "-Xms1g -Xmx1g"  # Instead of 2g

# Disable services you don't need
# Comment out: influxdb, jaeger, kibana
```

### Speed Up Startup

```bash
# Start only essential services
docker-compose up -d kafka elasticsearch postgresql redis

# Then start SIEM services
docker-compose up -d api-gateway collector normalizer enrichment indexer
```

## Production Deployment

For production deployment, see:
- [Deployment Guide](docs/deployment/DEPLOYMENT_GUIDE.md)
- [Kubernetes Manifests](infrastructure/kubernetes/)
- [Terraform Configs](infrastructure/terraform/)

## Getting Help

- **Documentation**: See `/docs` directory
- **Issues**: https://github.com/your-org/enterprise-siem/issues
- **Slack**: #siem-development

## Architecture Overview

```
┌─────────────┐
│  Data       │
│  Sources    │
└──────┬──────┘
       │
       ▼
┌─────────────┐    ┌──────────┐
│  Collector  │───▶│  Kafka   │
└─────────────┘    └────┬─────┘
                        │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
┌────────────┐   ┌────────────┐   ┌────────────┐
│ Normalizer │   │ Enrichment │   │  Indexer   │
└─────┬──────┘   └─────┬──────┘   └─────┬──────┘
      │                │                │
      └────────────────┼────────────────┘
                       ▼
              ┌────────────────┐
              │ Elasticsearch  │
              └────────┬───────┘
                       │
              ┌────────▼───────┐
              │  API Gateway   │
              └────────┬───────┘
                       │
              ┌────────▼───────┐
              │    Web UI      │
              └────────────────┘
```

## Monitoring

Access monitoring dashboards:

- **Grafana**: http://localhost:3001
  - Username: admin
  - Password: admin_change_me
  - Pre-loaded dashboards for SIEM metrics

- **Prometheus**: http://localhost:9090
  - Query metrics
  - View targets

- **Jaeger**: http://localhost:16686
  - Distributed tracing
  - Service dependencies

## Development Resources

- **API Documentation**: http://localhost:8080/api/docs
- **GraphQL Playground**: http://localhost:8080/graphql
- **Swagger UI**: http://localhost:8080/swagger

Happy hacking! 🚀

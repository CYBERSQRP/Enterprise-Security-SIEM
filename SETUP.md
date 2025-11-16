# Enterprise SIEM Setup Guide

This guide provides detailed instructions for setting up and running the Enterprise SIEM platform.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the Platform](#running-the-platform)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements (Development)

- **CPU**: 4 cores
- **RAM**: 8GB
- **Disk**: 50GB free space
- **OS**: Linux, macOS, or Windows with WSL2

### Recommended Requirements (Development)

- **CPU**: 8+ cores
- **RAM**: 16GB
- **Disk**: 100GB SSD
- **OS**: Linux or macOS

### Production Requirements

See [DEPLOYMENT_GUIDE.md](docs/deployment/DEPLOYMENT_GUIDE.md) for production requirements.

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Git
- (Optional) Go 1.21+ for local development
- (Optional) Node.js 18+ for frontend development

## Installation

### 1. System Preparation

#### Linux

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Configure system for Elasticsearch
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```

#### macOS

```bash
# Install Docker Desktop from https://www.docker.com/products/docker-desktop

# Or use Homebrew
brew install --cask docker

# Increase Docker resources in Docker Desktop:
# - Memory: 8GB minimum
# - CPUs: 4 minimum
# - Disk: 50GB minimum
```

#### Windows (WSL2)

```powershell
# Install WSL2
wsl --install

# Install Docker Desktop for Windows
# Download from https://www.docker.com/products/docker-desktop

# Enable WSL2 backend in Docker Desktop settings
```

### 2. Get the Code

```bash
cd Enterprise-Security-SIEM
```

### 3. Verify Directory Structure

```bash
# You should see this structure:
tree -L 2
```

Expected output:
```
.
├── docker-compose.yml
├── go.mod
├── services/
│   ├── api-gateway/
│   ├── collector/
│   └── processor/
├── shared/
│   └── models/
├── web-ui/
│   ├── src/
│   └── public/
├── rules/
│   └── correlation/
├── docs/
└── README.md
```

## Configuration

### 1. Environment Variables

The services use environment variables for configuration. Default values are set in the docker-compose.yml file, but you can override them:

```bash
# Create .env file (optional)
cat > .env << EOF
# Kafka Configuration
KAFKA_BROKERS=kafka:9092

# Elasticsearch Configuration
ELASTICSEARCH_URL=http://elasticsearch:9200

# Database Configuration
POSTGRES_USER=siem
POSTGRES_PASSWORD=siem_password
POSTGRES_DB=siem

# Service Ports
API_GATEWAY_PORT=8080
WEB_UI_PORT=3000
EOF
```

### 2. Elasticsearch Configuration

For production, you may want to configure Elasticsearch with proper settings:

```bash
# Create custom elasticsearch.yml
mkdir -p config/elasticsearch
cat > config/elasticsearch/elasticsearch.yml << EOF
cluster.name: siem-cluster
node.name: siem-node-1
network.host: 0.0.0.0
discovery.type: single-node
xpack.security.enabled: false
EOF
```

## Running the Platform

### 1. Start Infrastructure Services

Start the foundational services first:

```bash
# Start Zookeeper and Kafka
docker-compose up -d zookeeper kafka

# Wait for Kafka to be ready (about 30 seconds)
docker-compose logs -f kafka

# Start Elasticsearch
docker-compose up -d elasticsearch

# Wait for Elasticsearch to be healthy (1-2 minutes)
docker-compose logs -f elasticsearch

# Start PostgreSQL and Redis
docker-compose up -d postgres redis
```

### 2. Verify Infrastructure

```bash
# Check Elasticsearch
curl http://localhost:9200

# Check Kafka topics
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Check PostgreSQL
docker-compose exec postgres psql -U siem -d siem -c "SELECT version();"

# Check Redis
docker-compose exec redis redis-cli ping
```

### 3. Start SIEM Services

```bash
# Start API Gateway
docker-compose up -d api-gateway

# Check API Gateway health
curl http://localhost:8080/health

# Start Web UI
docker-compose up -d web-ui

# View all running services
docker-compose ps
```

### 4. Monitor Startup

```bash
# Watch all logs
docker-compose logs -f

# Watch specific service
docker-compose logs -f api-gateway

# Check for errors
docker-compose logs | grep -i error
```

## Testing

### 1. API Health Check

```bash
# Check API Gateway
curl http://localhost:8080/health

# Expected response:
# {"status":"healthy","elasticsearch":true}
```

### 2. Access Web UI

Open your browser and navigate to:

```
http://localhost:3000
```

You should see the Enterprise SIEM dashboard.

### 3. Test Event Search

```bash
# Search for events
curl -X POST http://localhost:8080/api/v1/events/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": {"match_all": {}},
    "size": 10
  }'
```

### 4. Test Alert API

```bash
# List alerts
curl http://localhost:8080/api/v1/alerts

# Create a test alert
curl -X POST http://localhost:8080/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Alert",
    "description": "This is a test alert",
    "severity": "medium",
    "entities": {
      "source_ips": ["192.0.2.1"]
    }
  }'
```

### 5. Verify Data Flow

```bash
# Check Elasticsearch indices
curl http://localhost:9200/_cat/indices?v

# Check Kafka topics
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Check event count in Elasticsearch
curl -X GET "http://localhost:9200/events-*/_count"
```

## Troubleshooting

### Common Issues

#### 1. Elasticsearch Won't Start

**Symptom**: Elasticsearch container keeps restarting

**Solution**:
```bash
# Increase vm.max_map_count (Linux)
sudo sysctl -w vm.max_map_count=262144

# For Docker Desktop (macOS/Windows), increase resources:
# Settings → Resources → Advanced
# - Memory: 8GB minimum
# - CPUs: 4 minimum
```

#### 2. Out of Memory Errors

**Symptom**: Services crashing with OOM errors

**Solution**:
```bash
# Reduce Elasticsearch memory in docker-compose.yml
ES_JAVA_OPTS: "-Xms512m -Xmx512m"

# Stop unused services
docker-compose stop collector processor
```

#### 3. Port Already in Use

**Symptom**: Cannot start service, port is already allocated

**Solution**:
```bash
# Find what's using the port
lsof -i :8080  # macOS/Linux
netstat -ano | findstr :8080  # Windows

# Either stop the conflicting service or change ports in docker-compose.yml
```

#### 4. API Gateway Can't Connect to Elasticsearch

**Symptom**: API returns 503 errors

**Solution**:
```bash
# Check Elasticsearch is running
docker-compose ps elasticsearch

# Check Elasticsearch health
curl http://localhost:9200/_cluster/health

# Restart API Gateway
docker-compose restart api-gateway
```

#### 5. Web UI Shows Blank Page

**Symptom**: Web UI loads but shows nothing

**Solution**:
```bash
# Check browser console for errors
# Check API Gateway is accessible
curl http://localhost:8080/health

# Rebuild web UI
docker-compose up -d --build web-ui

# Check nginx logs
docker-compose logs web-ui
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api-gateway

# Last 100 lines
docker-compose logs --tail=100 api-gateway

# Search for errors
docker-compose logs | grep -i error
```

### Resetting the System

```bash
# Stop all services
docker-compose down

# Remove all data (WARNING: This deletes everything!)
docker-compose down -v

# Remove Docker images
docker-compose down --rmi all

# Start fresh
docker-compose up -d
```

### Performance Monitoring

```bash
# Check Docker resource usage
docker stats

# Check container logs size
docker-compose ps -q | xargs docker inspect --format='{{.Name}} {{.LogPath}}' | xargs ls -lh

# Clean up Docker
docker system prune -a --volumes
```

## Next Steps

After successful installation:

1. **Configure Data Sources**: Set up log collectors and integrations
2. **Load Detection Rules**: Import pre-built detection rules
3. **Configure Alerts**: Set up notification channels
4. **Create Users**: Set up authentication and user accounts
5. **Explore UI**: Familiarize yourself with the dashboards

## Additional Resources

- [API Documentation](docs/api/API_SPECIFICATION.md)
- [Architecture Overview](docs/architecture/DESIGN.md)
- [Data Model](docs/architecture/DATA_MODEL.md)
- [Deployment Guide](docs/deployment/DEPLOYMENT_GUIDE.md)
- [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md)

## Getting Help

- Check the [FAQ](docs/FAQ.md)
- Review [Common Issues](docs/TROUBLESHOOTING.md)
- Search [GitHub Issues](https://github.com/your-org/enterprise-siem/issues)

## Support

For issues or questions:
- Create an issue on GitHub
- Contact the development team
- Check the documentation

Happy hunting! 🛡️🔍

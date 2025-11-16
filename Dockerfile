# Enterprise Security SIEM - Multi-Stage Dockerfile
# This Dockerfile supports building the entire SIEM platform or individual components
# Usage:
#   - Full platform: docker build -t siem-platform .
#   - Specific service: docker build --target <service> -t siem-<service> .
#   - Development: docker build --target development -t siem-dev .

# =============================================================================
# Base Images
# =============================================================================

# Base image for Go services
FROM golang:1.21-alpine AS go-base
RUN apk add --no-cache git gcc musl-dev ca-certificates
WORKDIR /workspace

# Base image for Python services
FROM python:3.11-slim AS python-base
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace

# Base image for Node.js services
FROM node:20-alpine AS node-base
RUN apk add --no-cache git python3 make g++
WORKDIR /workspace

# =============================================================================
# Development Environment
# =============================================================================
FROM python:3.11-slim AS development

# Install system dependencies for all languages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    git \
    wget \
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Go
ENV GO_VERSION=1.21.5
RUN wget https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz \
    && tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz \
    && rm go${GO_VERSION}.linux-amd64.tar.gz
ENV PATH="/usr/local/go/bin:${PATH}"

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest

WORKDIR /workspace

# Copy all source code
COPY . .

# Install Python dependencies for all Python services
RUN find services -name "requirements.txt" -exec pip install --no-cache-dir -r {} \;
RUN find ml-models -name "requirements.txt" -exec pip install --no-cache-dir -r {} \; || true

# Install Node.js dependencies
RUN cd web-portal && npm ci || true
RUN cd services/visualization-engine && npm ci || true

# Install Go dependencies
RUN for dir in services/*/go.mod; do \
        if [ -f "$dir" ]; then \
            (cd "$(dirname "$dir")" && go mod download); \
        fi \
    done

EXPOSE 3000 8080 8087 8088 8089 8090 8091 8092 8093 8094 8095

CMD ["/bin/bash"]

# =============================================================================
# Python Services Builder
# =============================================================================
FROM python-base AS python-services-builder

# Install common Python dependencies
COPY services/ai-analyst/requirements.txt /tmp/ai-analyst-requirements.txt
COPY services/alert-prioritization/requirements.txt /tmp/alert-prioritization-requirements.txt
COPY services/forensics/requirements.txt /tmp/forensics-requirements.txt
COPY services/predictive-analytics/requirements.txt /tmp/predictive-analytics-requirements.txt
COPY services/blockchain-audit-service/requirements.txt /tmp/blockchain-requirements.txt
COPY services/deception-platform/requirements.txt /tmp/deception-requirements.txt
COPY services/performance-optimizer/requirements.txt /tmp/performance-requirements.txt
COPY services/quantum-crypto-service/requirements.txt /tmp/quantum-requirements.txt
COPY services/supply-chain-monitor/requirements.txt /tmp/supply-chain-requirements.txt
COPY services/forensics-collector/requirements.txt /tmp/forensics-collector-requirements.txt

RUN pip install --no-cache-dir \
    -r /tmp/ai-analyst-requirements.txt \
    -r /tmp/alert-prioritization-requirements.txt \
    -r /tmp/forensics-requirements.txt \
    -r /tmp/predictive-analytics-requirements.txt \
    -r /tmp/blockchain-requirements.txt \
    -r /tmp/deception-requirements.txt \
    -r /tmp/performance-requirements.txt \
    -r /tmp/quantum-requirements.txt \
    -r /tmp/supply-chain-requirements.txt \
    -r /tmp/forensics-collector-requirements.txt

# =============================================================================
# Go Services Builder
# =============================================================================
FROM go-base AS go-services-builder

# Copy all Go service source code
COPY services/edge-security-gateway /workspace/edge-security-gateway
COPY services/ai-security-orchestrator /workspace/ai-security-orchestrator
COPY services/threat-intel-aggregator /workspace/threat-intel-aggregator
COPY services/collaboration-hub /workspace/collaboration-hub

# Build all Go services
RUN cd /workspace/edge-security-gateway && \
    go mod download && \
    CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -ldflags="-w -s" -o /bin/edge-security-gateway .

RUN cd /workspace/ai-security-orchestrator && \
    go mod download && \
    CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -ldflags="-w -s" -o /bin/ai-security-orchestrator .

RUN cd /workspace/threat-intel-aggregator && \
    go mod download && \
    CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -ldflags="-w -s" -o /bin/threat-intel-aggregator .

RUN cd /workspace/collaboration-hub && \
    go mod download && \
    CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -ldflags="-w -s" -o /bin/collaboration-hub .

# =============================================================================
# Web Portal Builder
# =============================================================================
FROM node-base AS web-portal-builder

WORKDIR /app

# Copy package files
COPY web-portal/package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY web-portal/ ./

# Build the application
RUN npm run build

# =============================================================================
# Visualization Engine Builder
# =============================================================================
FROM node-base AS visualization-engine-builder

WORKDIR /app

# Copy package files
COPY services/visualization-engine/package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY services/visualization-engine/ ./

# Build the application
RUN npm run build || echo "No build script found"

# =============================================================================
# AI Analyst Service
# =============================================================================
FROM python:3.11-slim AS ai-analyst

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY services/ai-analyst/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/ai-analyst/ .

EXPOSE 8091

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8091/health')" || exit 1

CMD ["python", "main.py"]

# =============================================================================
# Alert Prioritization Service
# =============================================================================
FROM python:3.11-slim AS alert-prioritization

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY services/alert-prioritization/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/alert-prioritization/ .

EXPOSE 8090

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8090/health')" || exit 1

CMD ["python", "main.py"]

# =============================================================================
# Edge Security Gateway Service
# =============================================================================
FROM alpine:latest AS edge-security-gateway

RUN apk --no-cache add ca-certificates tzdata

WORKDIR /app

COPY --from=go-services-builder /bin/edge-security-gateway /app/edge-security-gateway

EXPOSE 8087

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:8087/health || exit 1

CMD ["./edge-security-gateway"]

# =============================================================================
# AI Security Orchestrator Service
# =============================================================================
FROM alpine:latest AS ai-security-orchestrator

RUN apk --no-cache add ca-certificates tzdata

WORKDIR /app

COPY --from=go-services-builder /bin/ai-security-orchestrator /app/ai-security-orchestrator

EXPOSE 8088

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:8088/health || exit 1

CMD ["./ai-security-orchestrator"]

# =============================================================================
# Threat Intel Aggregator Service
# =============================================================================
FROM alpine:latest AS threat-intel-aggregator

RUN apk --no-cache add ca-certificates tzdata

WORKDIR /app

COPY --from=go-services-builder /bin/threat-intel-aggregator /app/threat-intel-aggregator

EXPOSE 8089

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:8089/health || exit 1

CMD ["./threat-intel-aggregator"]

# =============================================================================
# Collaboration Hub Service
# =============================================================================
FROM alpine:latest AS collaboration-hub

RUN apk --no-cache add ca-certificates tzdata

WORKDIR /app

COPY --from=go-services-builder /bin/collaboration-hub /app/collaboration-hub

EXPOSE 8095

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:8095/health || exit 1

CMD ["./collaboration-hub"]

# =============================================================================
# Web Portal Production
# =============================================================================
FROM nginx:alpine AS web-portal

# Copy built assets from builder
COPY --from=web-portal-builder /app/dist /usr/share/nginx/html

# Create nginx configuration
RUN echo 'server { \n\
    listen 80; \n\
    server_name _; \n\
    root /usr/share/nginx/html; \n\
    index index.html; \n\
    \n\
    location / { \n\
        try_files $uri $uri/ /index.html; \n\
    } \n\
    \n\
    location /api { \n\
        proxy_pass http://api-gateway:8080; \n\
        proxy_http_version 1.1; \n\
        proxy_set_header Upgrade $http_upgrade; \n\
        proxy_set_header Connection "upgrade"; \n\
        proxy_set_header Host $host; \n\
        proxy_set_header X-Real-IP $remote_addr; \n\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \n\
    } \n\
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]

# =============================================================================
# Default Production Image - Web Portal
# =============================================================================
FROM web-portal AS default

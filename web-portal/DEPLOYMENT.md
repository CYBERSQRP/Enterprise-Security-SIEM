# Web Portal Deployment Guide

This guide covers deploying the Enterprise SIEM Web Portal in various environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Production Deployment](#production-deployment)
- [Monitoring and Maintenance](#monitoring-and-maintenance)

## Prerequisites

### Required

- Node.js 20.x or higher
- npm 9.x or higher (or yarn 1.22.x+)
- Docker 24.x+ (for containerized deployment)
- Kubernetes 1.28+ (for K8s deployment)
- Access to backend services:
  - API Gateway (port 8080)
  - Collaboration Hub (port 8083)
  - Other microservices as needed

### Recommended

- Nginx or similar reverse proxy
- SSL/TLS certificates (Let's Encrypt, etc.)
- CDN for static assets (CloudFlare, CloudFront, etc.)
- Monitoring tools (Prometheus, Grafana, etc.)

## Local Development

### Setup

```bash
# Navigate to web portal directory
cd web-portal

# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### Configuration

Edit `.env`:

```env
VITE_API_URL=http://localhost:8080
VITE_WS_URL=ws://localhost:8083
VITE_ENV=development
```

### Run Development Server

```bash
# Start dev server with hot reload
npm run dev

# Access at http://localhost:3000
```

### Build for Testing

```bash
# Create production build
npm run build

# Preview production build
npm run preview
```

## Docker Deployment

### Development Container

```bash
# Build and run development container
docker-compose --profile dev up -d web-portal-dev

# View logs
docker-compose logs -f web-portal-dev

# Stop
docker-compose --profile dev down
```

Features:
- Hot reload enabled
- Source code mounted as volume
- Port 3000 exposed

### Production Container

```bash
# Build production image
docker build -t enterprise-siem/web-portal:latest .

# Run production container
docker-compose up -d web-portal

# Check status
docker-compose ps

# View logs
docker-compose logs -f web-portal
```

Features:
- Multi-stage build (Node + Nginx)
- Optimized image size (~50MB)
- Health checks enabled
- Nginx serves static files
- API/WebSocket proxying

### Custom Docker Build

```bash
# Build with custom tag
docker build -t my-registry.com/web-portal:v1.0.0 .

# Push to registry
docker push my-registry.com/web-portal:v1.0.0

# Run with custom configuration
docker run -d \
  -p 3000:80 \
  -e VITE_API_URL=https://api.example.com \
  --name siem-portal \
  my-registry.com/web-portal:v1.0.0
```

## Kubernetes Deployment

### Prerequisites

```bash
# Create namespace
kubectl create namespace enterprise-siem

# Create secrets (if needed)
kubectl create secret generic web-portal-secrets \
  --from-literal=api-url=https://api.example.com \
  -n enterprise-siem
```

### Deploy

```bash
# Apply Kubernetes manifests
kubectl apply -f deploy/kubernetes.yaml

# Check deployment status
kubectl get deployments -n enterprise-siem
kubectl get pods -n enterprise-siem -l app=web-portal

# Check services
kubectl get svc -n enterprise-siem

# Check ingress
kubectl get ingress -n enterprise-siem
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment web-portal \
  --replicas=5 \
  -n enterprise-siem

# Check HPA status
kubectl get hpa web-portal-hpa -n enterprise-siem

# HPA will automatically scale between 3-10 replicas
# based on CPU (70%) and memory (80%) utilization
```

### Updates and Rollouts

```bash
# Update image
kubectl set image deployment/web-portal \
  web-portal=enterprise-siem/web-portal:v1.1.0 \
  -n enterprise-siem

# Check rollout status
kubectl rollout status deployment/web-portal -n enterprise-siem

# Rollback if needed
kubectl rollout undo deployment/web-portal -n enterprise-siem

# View rollout history
kubectl rollout history deployment/web-portal -n enterprise-siem
```

### Configuration Updates

```bash
# Update ConfigMap
kubectl edit configmap web-portal-config -n enterprise-siem

# Restart pods to pick up changes
kubectl rollout restart deployment/web-portal -n enterprise-siem
```

## Production Deployment

### Build Production Artifacts

```bash
# Install dependencies (production only)
npm ci --production=false

# Run type checking
npm run type-check

# Run linter
npm run lint

# Run tests
npm run test

# Create optimized production build
npm run build

# Verify build
ls -lh dist/
```

### Nginx Configuration

Example production Nginx config:

```nginx
server {
    listen 443 ssl http2;
    server_name siem.example.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    root /var/www/siem-portal;
    index index.html;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # API proxy
    location /api {
        proxy_pass https://api-backend.internal:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket proxy
    location /ws {
        proxy_pass https://collab-backend.internal:8083;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name siem.example.com;
    return 301 https://$server_name$request_uri;
}
```

### Environment Variables for Production

```env
VITE_API_URL=https://api.siem.example.com
VITE_WS_URL=wss://api.siem.example.com/ws
VITE_ENV=production
VITE_ENABLE_COLLABORATION=true
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_FORENSICS=true
```

### Deployment Checklist

- [ ] Update environment variables
- [ ] Build production artifacts
- [ ] Run tests and linting
- [ ] Verify SSL/TLS certificates
- [ ] Configure reverse proxy (Nginx/Apache)
- [ ] Set up CDN (optional)
- [ ] Configure monitoring and logging
- [ ] Test API connectivity
- [ ] Test WebSocket connections
- [ ] Verify authentication flow
- [ ] Test all major features
- [ ] Set up backup and recovery
- [ ] Document rollback procedure
- [ ] Notify stakeholders
- [ ] Monitor post-deployment

## Monitoring and Maintenance

### Health Checks

The application includes health check endpoints:

```bash
# Check web portal health
curl https://siem.example.com/

# Check Kubernetes pod health
kubectl get pods -n enterprise-siem -l app=web-portal

# Check container health
docker ps --filter name=siem-web-portal
```

### Logging

#### Docker Logs

```bash
# View logs
docker-compose logs -f web-portal

# Last 100 lines
docker-compose logs --tail=100 web-portal

# Save logs to file
docker-compose logs web-portal > portal-logs.txt
```

#### Kubernetes Logs

```bash
# View pod logs
kubectl logs -f deployment/web-portal -n enterprise-siem

# View logs from all pods
kubectl logs -f -l app=web-portal -n enterprise-siem

# Previous container logs (if crashed)
kubectl logs --previous <pod-name> -n enterprise-siem
```

### Metrics

Monitor these key metrics:

- **Response Time**: < 200ms for static assets, < 500ms for API calls
- **Error Rate**: < 0.1%
- **Uptime**: > 99.9%
- **CPU Usage**: < 70% average
- **Memory Usage**: < 80% average
- **Active Users**: Real-time concurrent users
- **API Call Volume**: Requests per second
- **WebSocket Connections**: Active connections

### Backup and Recovery

#### Backup Configuration

```bash
# Backup Kubernetes configs
kubectl get all -n enterprise-siem -o yaml > backup-$(date +%Y%m%d).yaml

# Backup ConfigMaps and Secrets
kubectl get configmaps,secrets -n enterprise-siem -o yaml > configs-backup-$(date +%Y%m%d).yaml
```

#### Recovery

```bash
# Restore from backup
kubectl apply -f backup-20250101.yaml

# Verify restoration
kubectl get pods -n enterprise-siem
```

### Updates and Maintenance

#### Rolling Updates

```bash
# Build new version
docker build -t enterprise-siem/web-portal:v1.1.0 .

# Update Kubernetes deployment
kubectl set image deployment/web-portal \
  web-portal=enterprise-siem/web-portal:v1.1.0 \
  -n enterprise-siem

# Monitor rollout
kubectl rollout status deployment/web-portal -n enterprise-siem
```

#### Maintenance Windows

For major updates:

1. Notify users in advance
2. Enable maintenance mode (if available)
3. Create backup
4. Deploy updates
5. Run smoke tests
6. Monitor for issues
7. Disable maintenance mode
8. Send completion notification

### Troubleshooting

#### Common Issues

**1. 502 Bad Gateway**
- Check backend services are running
- Verify proxy configuration
- Check network connectivity

**2. WebSocket Connection Failed**
- Verify WebSocket service is running
- Check firewall rules
- Verify Nginx WebSocket configuration

**3. Static Assets Not Loading**
- Check Nginx configuration
- Verify file permissions
- Check CDN configuration (if used)

**4. High Memory Usage**
- Check for memory leaks
- Review component mounting/unmounting
- Consider increasing resource limits

**5. Slow Performance**
- Enable caching
- Optimize bundle size
- Use CDN for static assets
- Review API response times

## Security Considerations

### SSL/TLS

- Use TLS 1.2 or higher
- Strong cipher suites only
- Regular certificate renewal
- HSTS enabled

### Headers

Required security headers:
- Content-Security-Policy
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Strict-Transport-Security

### Access Control

- IP whitelisting (if applicable)
- WAF (Web Application Firewall)
- Rate limiting
- DDoS protection

### Secrets Management

- Never commit secrets to git
- Use Kubernetes Secrets or vault
- Rotate credentials regularly
- Use environment variables

## Performance Optimization

### CDN Setup

```nginx
# Example CloudFlare cache rules
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header X-Cache-Status $upstream_cache_status;
}
```

### Compression

```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_comp_level 6;
gzip_types
    text/plain
    text/css
    text/xml
    text/javascript
    application/json
    application/javascript
    application/xml+rss
    application/x-font-ttf
    font/opentype
    image/svg+xml;
```

### Caching Strategy

- Static assets: 1 year
- API responses: As appropriate per endpoint
- HTML: No cache (for SPA routing)

## Conclusion

This deployment guide covers the essential steps for deploying the Enterprise SIEM Web Portal. For additional help, refer to:

- Main README.md
- API Documentation
- Backend service documentation
- Kubernetes documentation

For issues or questions, contact the infrastructure team.

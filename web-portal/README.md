# Enterprise SIEM Web Portal

A modern, comprehensive web portal for the Enterprise Security Information and Event Management (SIEM) platform. Built with React, TypeScript, and Tailwind CSS, this portal provides unified access to all SIEM modules and features.

## Features

### Core Capabilities

- **Real-time Event Monitoring** - Live streaming of security events with advanced filtering and search
- **Alert Management** - Comprehensive alert lifecycle management with multi-status workflows
- **Incident Response** - Complete incident tracking with timeline, evidence, and playbook support
- **Threat Intelligence** - IOC lookup, feed management, and threat correlation
- **Forensics Evidence** - Chain of custody tracking, evidence collection, and malware analysis
- **Collaboration Hub** - Real-time multi-user investigation sessions with chat and annotations
- **Supply Chain Security** - Vendor risk assessment and vulnerability tracking
- **Predictive Analytics** - ML-powered threat forecasting and anomaly detection
- **Configuration Management** - Rule creation, data source management, and system settings

### Technical Features

- **Modern Stack** - React 18, TypeScript, Vite, Tailwind CSS
- **Real-time Communication** - WebSocket integration for live updates
- **State Management** - Zustand for global state, React Query for server state
- **Responsive Design** - Mobile-first, adaptive layouts
- **Dark Mode** - Full dark mode support
- **Visualization** - Recharts for charts, D3.js for advanced visualizations
- **Performance** - Code splitting, lazy loading, optimized bundles
- **Security** - JWT authentication, CSRF protection, secure headers

## Quick Start

### Prerequisites

- Node.js 20+ and npm
- Access to Enterprise SIEM backend services
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

```bash
# Clone the repository
cd web-portal

# Install dependencies
npm install

# Copy environment configuration
cp .env.example .env

# Update .env with your backend URLs
# VITE_API_URL=http://localhost:8080
# VITE_WS_URL=ws://localhost:8083

# Start development server
npm run dev
```

The portal will be available at `http://localhost:3000`

### Default Credentials

For demo/development environments:
- Username: `admin`
- Password: `admin`

## Development

### Project Structure

```
web-portal/
├── src/
│   ├── components/      # Reusable UI components
│   │   └── ui/         # Base UI components
│   ├── layouts/        # Layout components
│   ├── pages/          # Page components
│   ├── services/       # API service clients
│   ├── store/          # State management
│   ├── lib/            # Utilities and helpers
│   ├── types/          # TypeScript types
│   ├── App.tsx         # Main application component
│   ├── main.tsx        # Application entry point
│   └── index.css       # Global styles
├── public/             # Static assets
├── deploy/             # Deployment configurations
├── Dockerfile          # Production Docker image
├── Dockerfile.dev      # Development Docker image
├── docker-compose.yml  # Docker Compose configuration
├── nginx.conf          # Nginx configuration
└── package.json        # Dependencies and scripts
```

### Available Scripts

```bash
# Development
npm run dev              # Start dev server (port 3000)
npm run build            # Build for production
npm run preview          # Preview production build
npm run type-check       # Run TypeScript type checking

# Code Quality
npm run lint             # Run ESLint
npm run test             # Run tests
npm run test:ui          # Run tests with UI
```

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# API Configuration
VITE_API_URL=http://localhost:8080
VITE_WS_URL=ws://localhost:8083

# Feature Flags
VITE_ENABLE_COLLABORATION=true
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_FORENSICS=true

# Environment
VITE_ENV=development
```

## Module Integrations

### 1. Event Monitoring (`/events`)

- Real-time event streaming via WebSocket
- Advanced search with Elasticsearch
- Export to CSV/JSON
- Customizable filters (severity, source, category, time range)

**API Endpoints:**
- `GET /api/v1/events/search` - Search events
- `GET /api/v1/events/:id` - Get event details
- `GET /api/v1/events/stats` - Get event statistics
- `GET /api/v1/events/export` - Export events

### 2. Alert Management (`/alerts`)

- Alert lifecycle: new → acknowledged → investigating → resolved
- Bulk operations
- Assignment and escalation
- False positive marking

**API Endpoints:**
- `GET /api/v1/alerts` - List alerts
- `POST /api/v1/alerts/:id/acknowledge` - Acknowledge alert
- `POST /api/v1/alerts/:id/assign` - Assign alert
- `PATCH /api/v1/alerts/:id` - Update alert status

### 3. Incident Response (`/incidents`)

- Complete incident lifecycle management
- Evidence attachment
- Timeline tracking
- Automated playbook execution
- Multi-alert correlation

**API Endpoints:**
- `GET /api/v1/incidents` - List incidents
- `POST /api/v1/incidents` - Create incident
- `POST /api/v1/incidents/:id/timeline` - Add timeline event
- `POST /api/v1/incidents/:id/evidence` - Attach evidence
- `POST /api/v1/incidents/:id/playbook` - Execute playbook

### 4. Threat Intelligence (`/threat-intel`)

- Multi-source IOC feeds (MISP, OTX, custom)
- Real-time IOC lookup
- Threat correlation
- Custom IOC management

**API Endpoints:**
- `GET /api/v1/feeds` - List threat feeds (port 8080)
- `POST /api/v1/feeds/:id/sync` - Sync feed
- `GET /api/v1/iocs/lookup` - Lookup IOC
- `POST /api/v1/iocs` - Add custom IOC

### 5. Forensics Evidence (`/forensics`)

- Evidence collection and storage
- Chain of custody with cryptographic signatures
- Memory dump analysis
- Malware analysis integration
- Evidence verification

**API Endpoints:**
- `GET /api/v1/evidence` - List evidence (port 8082)
- `POST /api/v1/evidence/collect` - Collect evidence
- `POST /api/v1/evidence/:id/analyze` - Analyze evidence
- `GET /api/v1/evidence/:id/verify` - Verify chain of custody

### 6. Collaboration Hub (`/collaboration`)

- Real-time investigation sessions
- Multi-user chat
- Shared annotations
- Cursor tracking
- Video call integration (future)

**WebSocket Events:**
- `join_session` - Join collaboration session
- `message` - Send/receive chat messages
- `annotation` - Add/receive annotations
- `cursor` - Cursor position updates

### 7. Supply Chain Security (`/supply-chain`)

- Vendor risk assessment
- Vulnerability tracking (CVE integration)
- Compliance monitoring
- Risk trend analysis

**API Endpoints:**
- `GET /api/v1/vendors` - List vendors (port 8081)
- `POST /api/v1/vendors/:id/assess` - Assess vendor risk
- `GET /api/v1/vendors/:id/vulnerabilities` - Get vulnerabilities
- `GET /api/v1/vendors/risk-trends` - Get risk trends

### 8. Predictive Analytics (`/analytics`)

- Threat forecasting
- Anomaly detection
- Risk scoring
- ML model management and training

**API Endpoints:**
- `GET /api/v1/models` - List ML models (port 8084)
- `POST /api/v1/models/:id/train` - Train model
- `GET /api/v1/models/:id/predictions` - Get predictions
- `POST /api/v1/analytics/anomalies` - Detect anomalies
- `GET /api/v1/analytics/insights` - Get AI insights

### 9. Configuration (`/config`)

- Detection rule management
- Data source configuration
- User and permission management
- System settings
- Retention policies

**API Endpoints:**
- `GET /api/v1/rules` - List rules
- `POST /api/v1/rules` - Create rule
- `GET /api/v1/config/data-sources` - List data sources
- `GET /api/v1/users` - List users

## Deployment

### Docker (Recommended)

#### Production

```bash
# Build production image
docker build -t enterprise-siem/web-portal:latest .

# Run with docker-compose
docker-compose up -d web-portal

# Access at http://localhost:3000
```

#### Development

```bash
# Run development container with hot reload
docker-compose --profile dev up web-portal-dev
```

### Kubernetes

Deploy to Kubernetes using the provided manifests:

```bash
# Apply Kubernetes configuration
kubectl apply -f deploy/kubernetes.yaml

# Check deployment status
kubectl get pods -n enterprise-siem -l app=web-portal

# Get service URL
kubectl get svc web-portal -n enterprise-siem
```

Features:
- 3 replica minimum (auto-scaling to 10)
- Health checks (liveness and readiness probes)
- Resource limits and requests
- Ingress with TLS/SSL support
- Horizontal Pod Autoscaler (HPA)

### Manual Build

```bash
# Install dependencies
npm ci

# Build for production
npm run build

# Serve with your web server
# Built files are in ./dist directory
```

### Nginx Configuration

The portal includes a production-ready Nginx configuration with:

- Gzip compression
- Security headers (CSP, XSS, Frame Options)
- API reverse proxy to backend services
- WebSocket proxy for real-time features
- Static asset caching
- SPA routing support

## Architecture

### Component Structure

```
┌─────────────────────────────────────────┐
│          Web Portal (React)             │
├─────────────────────────────────────────┤
│  Authentication Layer (JWT)             │
├─────────────────────────────────────────┤
│  API Client Layer                       │
│  ├── REST API (Axios)                   │
│  ├── WebSocket (Socket.io)              │
│  └── GraphQL (Apollo - future)          │
├─────────────────────────────────────────┤
│  State Management                       │
│  ├── Zustand (Global State)             │
│  └── React Query (Server State)         │
├─────────────────────────────────────────┤
│  UI Components                          │
│  ├── Pages                              │
│  ├── Layouts                            │
│  └── Reusable Components                │
└─────────────────────────────────────────┘
         │                    │
         ▼                    ▼
   REST API (8080)    WebSocket (8083)
```

### Data Flow

1. **Authentication**: JWT tokens stored in localStorage, auto-refresh on expiry
2. **API Requests**: Axios interceptors add auth headers, handle errors
3. **Real-time Updates**: Socket.io for events, alerts, and collaboration
4. **State Management**: React Query caches server data, Zustand for UI state
5. **Rendering**: React renders components based on state changes

## Security

### Implemented Security Features

- **Authentication**: JWT-based authentication with token refresh
- **Authorization**: Role-based access control (RBAC)
- **HTTPS**: TLS/SSL encryption (production)
- **CSP**: Content Security Policy headers
- **XSS Protection**: Input sanitization and output encoding
- **CSRF**: CSRF token validation
- **Secure Headers**: X-Frame-Options, X-Content-Type-Options, etc.
- **Session Management**: Automatic logout on token expiry
- **API Security**: All API calls require valid JWT

### Best Practices

- Never commit `.env` files
- Rotate JWT secrets regularly
- Use HTTPS in production
- Implement rate limiting
- Regular dependency updates
- Security audit logging

## Performance Optimization

### Implemented Optimizations

- **Code Splitting**: Route-based lazy loading
- **Bundle Optimization**: Vendor chunking for better caching
- **Image Optimization**: Lazy loading, WebP format
- **API Optimization**: Request deduplication, caching
- **Virtual Scrolling**: For large lists
- **Memoization**: React.memo, useMemo, useCallback
- **Compression**: Gzip for static assets

### Performance Metrics

- First Contentful Paint (FCP): < 1.5s
- Time to Interactive (TTI): < 3.5s
- Bundle size: ~500KB (gzipped)
- Lighthouse score: 90+

## Browser Support

- Chrome/Edge: Last 2 versions
- Firefox: Last 2 versions
- Safari: Last 2 versions
- Mobile browsers: iOS Safari 13+, Chrome Android

## Troubleshooting

### Common Issues

**1. Cannot connect to backend services**
```bash
# Check backend is running
curl http://localhost:8080/api/v1/health

# Verify VITE_API_URL in .env
cat .env | grep VITE_API_URL
```

**2. WebSocket connection fails**
```bash
# Check collaboration service
curl http://localhost:8083/health

# Verify firewall allows WebSocket connections
# Check browser console for connection errors
```

**3. Build fails**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 20+
```

**4. Authentication issues**
```bash
# Clear browser storage
# Open DevTools -> Application -> Clear storage

# Check JWT token validity
# DevTools -> Application -> Local Storage -> auth-storage
```

## Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and test thoroughly
3. Run linter: `npm run lint`
4. Run type check: `npm run type-check`
5. Commit changes: `git commit -m "feat: add my feature"`
6. Push and create PR

## License

Proprietary - Enterprise Security SIEM Platform

## Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/your-org/enterprise-siem/issues)
- Documentation: See `/docs` directory
- Email: security-team@example.com

## Changelog

### Version 1.0.0 (2025)

- Initial release with all 10 module integrations
- Real-time event monitoring and alerting
- Complete incident response workflow
- Threat intelligence integration
- Forensics evidence management
- Real-time collaboration features
- Supply chain risk monitoring
- Predictive analytics and ML insights
- Comprehensive configuration management
- Production-ready deployment configurations

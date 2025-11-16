/**
 * Visualization Engine Server
 *
 * Serves visualization components and provides data endpoints
 */

const express = require('express');
const cors = require('cors');
const promClient = require('prom-client');

const app = express();
const PORT = process.env.PORT || 8094;

// Middleware
app.use(cors());
app.use(express.json());

// Prometheus metrics
const register = new promClient.Registry();
promClient.collectDefaultMetrics({ register });

const httpRequestDuration = new promClient.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code'],
  registers: [register]
});

const visualizationRequests = new promClient.Counter({
  name: 'visualization_requests_total',
  help: 'Total number of visualization requests',
  labelNames: ['visualization_type'],
  registers: [register]
});

// Middleware to measure request duration
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    httpRequestDuration.labels(req.method, req.path, res.statusCode).observe(duration);
  });
  next();
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'visualization-engine',
    version: '1.0.0',
    timestamp: new Date().toISOString()
  });
});

// Metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});

// Visualization endpoints
app.get('/api/v1/visualizations/attack-flow', (req, res) => {
  visualizationRequests.labels('attack_flow').inc();

  // Sample attack flow data
  res.json({
    nodes: [
      {
        id: 'node1',
        type: 'initial_access',
        technique: 'T1566 - Phishing',
        timestamp: new Date(),
        severity: 'high',
        description: 'Phishing email detected'
      },
      {
        id: 'node2',
        type: 'execution',
        technique: 'T1059 - Command Execution',
        timestamp: new Date(),
        severity: 'critical',
        description: 'Malicious command executed'
      }
    ],
    edges: [
      {
        source: 'node1',
        target: 'node2',
        confidence: 0.95
      }
    ]
  });
});

app.get('/api/v1/visualizations/network-topology', (req, res) => {
  visualizationRequests.labels('network_topology').inc();

  // Sample network topology data
  res.json({
    nodes: [
      {
        id: 'host1',
        type: 'server',
        ip: '192.168.1.10',
        hostname: 'web-server-01',
        risk_score: 0.3,
        connections: 45
      },
      {
        id: 'host2',
        type: 'workstation',
        ip: '192.168.1.50',
        hostname: 'ws-marketing-05',
        risk_score: 0.7,
        connections: 12
      }
    ],
    connections: [
      {
        source: 'host1',
        target: 'host2',
        protocol: 'HTTPS',
        bytes_transferred: 1048576,
        suspicious: false
      }
    ]
  });
});

app.get('/api/v1/visualizations/threat-map', (req, res) => {
  visualizationRequests.labels('threat_map').inc();

  // Sample threat map data
  res.json({
    threats: [
      {
        source_country: 'CN',
        source_coords: [116.4074, 39.9042],
        target_country: 'US',
        target_coords: [-77.0369, 38.9072],
        threat_type: 'brute_force',
        severity: 'high',
        count: 1250
      }
    ]
  });
});

app.get('/api/v1/visualizations/timeline', (req, res) => {
  visualizationRequests.labels('timeline').inc();

  // Sample timeline data
  const events = [];
  const now = new Date();
  for (let i = 0; i < 50; i++) {
    events.push({
      timestamp: new Date(now.getTime() - i * 3600000),
      event_type: ['login', 'file_access', 'network_connection', 'alert'][Math.floor(Math.random() * 4)],
      severity: ['low', 'medium', 'high'][Math.floor(Math.random() * 3)],
      count: Math.floor(Math.random() * 100) + 1
    });
  }

  res.json({ events });
});

app.get('/api/v1/visualizations/incident-graph', (req, res) => {
  visualizationRequests.labels('incident_graph').inc();

  // Sample incident graph data
  res.json({
    incident_id: 'INC-2024-001',
    root_cause: {
      id: 'alert1',
      type: 'malware_detection',
      timestamp: new Date(),
      description: 'Malware detected on workstation'
    },
    related_events: [
      {
        id: 'evt1',
        type: 'file_download',
        timestamp: new Date(),
        description: 'Suspicious file downloaded'
      },
      {
        id: 'evt2',
        type: 'process_execution',
        timestamp: new Date(),
        description: 'Unknown process started'
      }
    ],
    relationships: [
      { source: 'alert1', target: 'evt1', type: 'caused_by' },
      { source: 'evt1', target: 'evt2', type: 'led_to' }
    ]
  });
});

app.get('/api/v1/stats', (req, res) => {
  res.json({
    service: 'visualization-engine',
    uptime: process.uptime(),
    visualizations_available: [
      'attack-flow',
      'network-topology',
      'threat-map',
      'timeline',
      'incident-graph'
    ]
  });
});

// Error handling
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    error: 'Internal Server Error',
    message: err.message
  });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Visualization Engine Server listening on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`Metrics: http://localhost:${PORT}/metrics`);
});

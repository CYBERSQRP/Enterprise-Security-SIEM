# Visualization Engine Service

Advanced visualization service providing interactive D3.js and Three.js visualizations for security data including attack flows, network topology, threat maps, and incident graphs.

## Features

- **Attack Flow Visualization**: MITRE ATT&CK chain visualization with D3.js force-directed graphs
- **3D Network Topology**: Interactive 3D network visualization using Three.js
- **Real-time Threat Map**: Geographic threat visualization on world map
- **Timeline Visualization**: Interactive event timeline with filtering
- **Incident Investigation Graphs**: Relationship graphs for incident investigation
- **Zoom & Pan**: All visualizations support zoom and pan interactions
- **Real-time Updates**: WebSocket support for live data updates

## Visualizations

### 1. Attack Flow Visualization
Visualizes attack chains according to MITRE ATT&CK framework.

**Features:**
- Force-directed graph layout
- Color-coded by severity
- Click to see technique details
- Shows attack progression

### 2. Network Topology (3D)
Interactive 3D visualization of network infrastructure.

**Features:**
- 3D network graph
- Node size based on connections
- Color-coded by risk score
- Rotation and zoom controls

### 3. Threat Map
Geographic visualization of threat origins and targets.

**Features:**
- World map projection
- Arc visualization for threat flows
- Heat map for threat density
- Country-level aggregation

### 4. Timeline Visualization
Chronological event visualization.

**Features:**
- Time-series chart
- Event grouping
- Severity filtering
- Brush selection for zooming

### 5. Incident Investigation Graph
Relationship graph for incident investigation.

**Features:**
- Node-link diagram
- Event correlation
- Root cause highlighting
- Interactive exploration

## API Endpoints

### Health Check
```bash
GET /health
```

### Attack Flow Data
```bash
GET /api/v1/visualizations/attack-flow
```

Response:
```json
{
  "nodes": [
    {
      "id": "node1",
      "type": "initial_access",
      "technique": "T1566 - Phishing",
      "timestamp": "2024-01-15T10:30:00.000Z",
      "severity": "high",
      "description": "Phishing email detected"
    }
  ],
  "edges": [
    {
      "source": "node1",
      "target": "node2",
      "confidence": 0.95
    }
  ]
}
```

### Network Topology Data
```bash
GET /api/v1/visualizations/network-topology
```

Response:
```json
{
  "nodes": [
    {
      "id": "host1",
      "type": "server",
      "ip": "192.168.1.10",
      "hostname": "web-server-01",
      "risk_score": 0.3,
      "connections": 45
    }
  ],
  "connections": [
    {
      "source": "host1",
      "target": "host2",
      "protocol": "HTTPS",
      "bytes_transferred": 1048576,
      "suspicious": false
    }
  ]
}
```

### Threat Map Data
```bash
GET /api/v1/visualizations/threat-map
```

Response:
```json
{
  "threats": [
    {
      "source_country": "CN",
      "source_coords": [116.4074, 39.9042],
      "target_country": "US",
      "target_coords": [-77.0369, 38.9072],
      "threat_type": "brute_force",
      "severity": "high",
      "count": 1250
    }
  ]
}
```

### Timeline Data
```bash
GET /api/v1/visualizations/timeline
```

### Incident Graph Data
```bash
GET /api/v1/visualizations/incident-graph
```

### Statistics
```bash
GET /api/v1/stats
```

### Metrics
```bash
GET /metrics
```

## React Components

### AttackFlowVisualization
```tsx
import { AttackFlowVisualization } from './visualizer';

<AttackFlowVisualization
  nodes={attackNodes}
  edges={attackEdges}
  onNodeClick={(node) => console.log(node)}
/>
```

### NetworkTopology3D
```tsx
import { NetworkTopology3D } from './visualizer';

<NetworkTopology3D
  nodes={networkNodes}
  connections={connections}
  onNodeClick={(node) => console.log(node)}
/>
```

### ThreatMap
```tsx
import { ThreatMap } from './visualizer';

<ThreatMap
  threats={threatData}
  onThreatClick={(threat) => console.log(threat)}
/>
```

### TimelineVisualization
```tsx
import { TimelineVisualization } from './visualizer';

<TimelineVisualization
  events={timelineEvents}
  timeRange={{ start: new Date('2024-01-01'), end: new Date() }}
  onEventClick={(event) => console.log(event)}
/>
```

### IncidentInvestigationGraph
```tsx
import { IncidentInvestigationGraph } from './visualizer';

<IncidentInvestigationGraph
  incident={incidentData}
  onNodeClick={(node) => console.log(node)}
/>
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Service port | 8094 |
| `NODE_ENV` | Environment (development/production) | production |

## Running Locally

### With Docker
```bash
docker build -t visualization-engine .
docker run -p 8094:8094 visualization-engine
```

### With Node.js
```bash
npm install
npm start
```

### Development Mode
```bash
npm run dev
```

## Integration Examples

### Fetch Visualization Data
```javascript
// Fetch attack flow data
const response = await fetch('http://localhost:8094/api/v1/visualizations/attack-flow');
const data = await response.json();

// Render visualization
const viz = new AttackFlowVisualization(data.nodes, data.edges);
viz.render('#attack-flow-container');
```

### Python Client
```python
import requests

# Get threat map data
response = requests.get('http://localhost:8094/api/v1/visualizations/threat-map')
threats = response.json()

print(f"Found {len(threats['threats'])} threats")
```

### cURL
```bash
# Get network topology
curl http://localhost:8094/api/v1/visualizations/network-topology

# Get timeline data
curl http://localhost:8094/api/v1/visualizations/timeline

# Get incident graph
curl http://localhost:8094/api/v1/visualizations/incident-graph
```

## Customization

### Color Schemes
Modify severity colors in visualizations:
```javascript
const severityColors = {
  low: '#4CAF50',
  medium: '#FFC107',
  high: '#FF9800',
  critical: '#F44336'
};
```

### Graph Layouts
Customize force-directed graph parameters:
```javascript
const simulation = d3.forceSimulation()
  .force('link', d3.forceLink().distance(150))
  .force('charge', d3.forceManyBody().strength(-300))
  .force('center', d3.forceCenter())
  .force('collision', d3.forceCollide().radius(40));
```

## Dependencies

- **React**: UI components
- **D3.js**: 2D visualizations
- **Three.js**: 3D visualizations
- **Express**: Web server
- **prom-client**: Prometheus metrics

## Monitoring

The service exposes Prometheus metrics at `/metrics`:

- `http_request_duration_seconds` - Request duration histogram
- `visualization_requests_total` - Total visualization requests by type

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

- Handles up to 10,000 nodes in network topology
- Supports real-time updates (60 FPS)
- WebGL acceleration for 3D visualizations
- Canvas fallback for older browsers

## Development

### Adding New Visualizations
1. Create component in `visualizer.tsx`
2. Add data endpoint in `server.js`
3. Export component
4. Document usage

### Testing
```bash
npm test
```

### Building
```bash
npm run build
```

## License

Copyright © 2024 Enterprise Security SIEM

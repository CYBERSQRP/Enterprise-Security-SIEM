# Edge Security Gateway

IoT and edge device security monitoring with edge-based anomaly detection and response.

## Overview

Provides security monitoring and threat detection for edge computing and IoT devices:
- **Device Registration** - Manage edge and IoT devices
- **Telemetry Collection** - Real-time metrics from devices
- **Anomaly Detection** - ML-based behavior analysis
- **Edge Rules** - Security rules executed at the edge
- **Multi-Protocol Support** - MQTT, CoAP, HTTP collectors

## Features

### Device Management
- Device registration and inventory
- Firmware tracking
- Security scoring
- Capability management

### Data Collection
- MQTT collector (port 1883)
- CoAP collector (port 5683)
- HTTP collector (port 8087)
- Real-time telemetry processing

### Anomaly Detection
- CPU usage anomalies
- Memory usage anomalies
- Network behavior anomalies
- Baseline learning
- ML model deployment

### Edge Rules
- Suspicious network activity detection
- Firmware version validation
- Resource usage monitoring
- Custom rule engine

## API Endpoints

### Device Management
- `POST /api/v1/devices/register` - Register device
- `GET /api/v1/devices` - List devices
- `GET /api/v1/devices/:id` - Get device details
- `DELETE /api/v1/devices/:id` - Deregister device

### Telemetry
- `POST /api/v1/telemetry` - Send telemetry data
- `GET /api/v1/telemetry/:device_id` - Get device telemetry

### Alerts
- `GET /api/v1/alerts` - List all alerts
- `GET /api/v1/alerts/:device_id` - Get device alerts

### Edge Rules
- `GET /api/v1/rules` - List rules
- `POST /api/v1/rules` - Create rule
- `PUT /api/v1/rules/:id` - Update rule
- `DELETE /api/v1/rules/:id` - Delete rule

### Anomalies
- `GET /api/v1/anomalies` - List anomalies
- `GET /api/v1/baselines/:device_id` - Get device baseline

### ML Models
- `GET /api/v1/models` - List detection models
- `POST /api/v1/models/:id/deploy` - Deploy model

## Usage Examples

```bash
# Register an IoT device
curl -X POST http://localhost:8087/api/v1/devices/register \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "iot-camera-01",
    "device_type": "camera",
    "location": "Building A - Entrance",
    "ip_address": "192.168.1.100",
    "mac_address": "00:11:22:33:44:55",
    "firmware": "v2.1.0",
    "capabilities": ["motion_detection", "night_vision"]
  }'

# Send telemetry data
curl -X POST http://localhost:8087/api/v1/telemetry \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "iot-camera-01",
    "timestamp": "2025-11-16T12:00:00Z",
    "metrics": {
      "cpu_usage": 45.2,
      "memory_usage": 62.5,
      "network_traffic": 2048,
      "temperature": 42.5
    }
  }'

# Get device alerts
curl http://localhost:8087/api/v1/alerts/iot-camera-01
```

## Supported Device Types

- **IoT Sensors** - Temperature, humidity, motion
- **IP Cameras** - Security cameras, video surveillance
- **Edge Servers** - Edge computing nodes
- **Industrial Controllers** - SCADA, PLC devices
- **Smart Meters** - Energy, water meters
- **Gateways** - Protocol converters, aggregators

## Edge ML Models

1. **Network Anomaly Detection** (LSTM, 92% accuracy)
   - Detects unusual network patterns
   - Real-time threat identification

2. **Device Behavior Analysis** (Isolation Forest, 89% accuracy)
   - Learns normal device behavior
   - Flags deviations from baseline

## Security Features

- TLS encryption for device communication
- Device authentication
- Firmware validation
- Automatic device isolation on compromise
- Zero-trust architecture
- Minimal attack surface

## Performance

- Supports 100,000+ concurrent devices
- Sub-second telemetry processing
- Edge-based processing reduces latency
- Bandwidth optimization for constrained devices

## License

Proprietary - Enterprise SIEM Platform

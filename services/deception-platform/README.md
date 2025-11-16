# Deception Platform

Advanced deception technology with honeypots, honeytokens, and active defense to detect and mislead attackers.

## Overview

Provides comprehensive deception capabilities:
- **Honeypots** - Decoy systems that attract attackers
- **Honeytokens** - Decoy credentials and assets
- **Active Defense** - Automated response to attacker actions
- **Threat Intelligence** - IOC collection from attackers

## Features

### Honeypots
- SSH servers
- Web servers
- Databases
- File servers
- Email servers
- RDP servers
- API endpoints
- IoT devices

Interaction levels:
- **Low** - Limited interaction, basic logging
- **Medium** - Moderate interaction, emulated services
- **High** - Full interaction, real vulnerable services

### Honeytokens
- Fake credentials
- API keys
- AWS keys
- Database records
- Files
- URLs
- Cookies
- Email addresses

### Active Defense
- **Tarpit** - Slow down attackers
- **IP Blocking** - Temporary IP bans
- **Enhanced Monitoring** - Increased logging
- **Honeypot Redirection** - Route to more sophisticated traps
- **Counter-intelligence** - Feed false information

### Threat Intelligence
- Malicious IP collection
- Attack pattern identification
- Attacker fingerprinting
- IOC extraction
- TTP documentation

## API Endpoints

### Honeypot Management
- `POST /api/v1/honeypots` - Deploy honeypot
- `GET /api/v1/honeypots` - List honeypots
- `GET /api/v1/honeypots/:id` - Get honeypot details
- `DELETE /api/v1/honeypots/:id` - Remove honeypot

### Honeytoken Management
- `POST /api/v1/honeytokens` - Create honeytoken
- `GET /api/v1/honeytokens` - List honeytokens
- `GET /api/v1/honeytokens/:id` - Get honeytoken details
- `DELETE /api/v1/honeytokens/:id` - Remove honeytoken

### Interactions
- `POST /api/v1/interactions` - Report interaction
- `GET /api/v1/interactions` - List interactions
- `GET /api/v1/interactions/:id` - Get interaction details

### Active Defense
- `GET /api/v1/active-defense` - List defense actions

### Intelligence
- `GET /api/v1/threat-intel` - Get threat intelligence
- `GET /api/v1/stats` - Get statistics

## Usage Examples

```bash
# Deploy an SSH honeypot
curl -X POST http://localhost:8089/api/v1/honeypots \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SSH Honeypot - DMZ",
    "type": "ssh_server",
    "interaction_level": "medium",
    "ip_address": "10.0.1.50",
    "port": 22,
    "protocol": "TCP",
    "services": ["ssh"],
    "decoy_data": {"banner": "Ubuntu SSH Server"}
  }'

# Create a honeytoken (fake AWS key)
curl -X POST http://localhost:8089/api/v1/honeytokens \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Fake AWS Key - Production",
    "type": "aws_key",
    "location": "/home/user/.aws/credentials",
    "auto_generate": true
  }'

# Report an interaction
curl -X POST http://localhost:8089/api/v1/interactions \
  -H "Content-Type: application/json" \
  -d '{
    "asset_id": "hp-abc123",
    "asset_type": "honeypot",
    "source_ip": "192.168.1.100",
    "source_port": 54321,
    "destination_port": 22,
    "protocol": "TCP",
    "payload": "admin:password123"
  }'

# Get threat intelligence
curl http://localhost:8089/api/v1/threat-intel
```

## Attack Detection

Automatically detects:
- SQL injection attempts
- XSS attacks
- Directory traversal
- Code injection
- SSH brute force
- RDP brute force
- Credential stuffing
- Reconnaissance scans

## Active Defense Actions

1. **Tarpit** - Slows down attacker connections
   - Triggered by: SQL injection, code injection
   - Duration: Connection-based

2. **IP Blocking** - Temporary IP bans
   - Triggered by: Brute force attacks
   - Duration: 24 hours

3. **Enhanced Monitoring** - Increased logging
   - Triggered by: Reconnaissance
   - Duration: Until threat subsides

4. **Honeypot Redirection** - Route to high-interaction honeypot
   - Triggered by: Advanced attacks
   - Duration: Session-based

## Deployment Strategy

1. **Network Placement**
   - DMZ honeypots for external threats
   - Internal honeypots for insider threats
   - Distributed across network segments

2. **Honeytoken Placement**
   - Configuration files
   - Database tables
   - Code repositories
   - Documentation
   - Network shares

3. **Monitoring**
   - Real-time interaction alerts
   - Automated threat intelligence extraction
   - Integration with SIEM

## Legal Considerations

- Ensure compliance with local laws
- Obtain legal approval for active defense
- Document all deception assets
- Implement proper access controls
- Maintain audit trails

## Performance

- Supports 1000+ concurrent honeypots
- Sub-second interaction detection
- Real-time active defense triggers
- Minimal resource footprint

## Integration

- SIEM integration for alerts
- Threat intelligence platform feeds
- Firewall integration for IP blocking
- Incident response automation

## License

Proprietary - Enterprise SIEM Platform

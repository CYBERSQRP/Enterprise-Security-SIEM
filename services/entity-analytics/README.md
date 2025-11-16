# Entity Analytics Service

Advanced entity relationship analysis using graph databases to detect lateral movement, attack chains, and complex attack patterns.

## Overview

This service leverages Neo4j graph database to model and analyze relationships between entities (users, hosts, processes, files, networks) to identify sophisticated attack patterns.

## Features

### 1. Entity Relationship Mapping
- **Multi-entity tracking**: Users, hosts, processes, files, IP addresses
- **Relationship modeling**: Authentication, process execution, file access, network connections
- **Temporal tracking**: Time-based relationship evolution
- **Bi-directional relationships**: Parent-child, source-destination relationships

### 2. Attack Chain Reconstruction
- **Kill chain mapping**: Map events to MITRE ATT&CK framework
- **Attack path identification**: Identify sequences of related malicious activities
- **Pivoting detection**: Detect attackers moving between systems
- **Root cause analysis**: Trace back to initial compromise

### 3. Lateral Movement Detection
- **Cross-host activity**: Detect unusual lateral movement patterns
- **Credential reuse**: Identify suspicious credential usage across hosts
- **Remote execution**: Detect remote command execution patterns
- **Administrative activity**: Track privileged account usage across systems

### 4. Graph-based Analytics
- **Centrality analysis**: Identify critical nodes in the network
- **Community detection**: Find clusters of related entities
- **Anomalous paths**: Detect unusual connection patterns
- **Shortest path analysis**: Find attack paths between entities

## Architecture

```
┌──────────────────┐
│  Event Streams   │
│  (Kafka)         │
└────────┬─────────┘
         │
┌────────▼─────────┐
│ Entity Extractor │
│  - Parse events  │
│  - Extract       │
│    entities      │
└────────┬─────────┘
         │
┌────────▼─────────┐
│  Graph Builder   │
│  - Create nodes  │
│  - Create edges  │
│  - Update props  │
└────────┬─────────┘
         │
┌────────▼─────────┐
│   Neo4j Graph    │
│    Database      │
└────────┬─────────┘
         │
┌────────▼─────────┐
│ Graph Analytics  │
│  - Path finding  │
│  - Pattern match │
│  - Centrality    │
└────────┬─────────┘
         │
┌────────▼─────────┐
│  Detection API   │
│  - Lateral move  │
│  - Attack chains │
│  - Anomalies     │
└──────────────────┘
```

## Graph Data Model

### Node Types

```cypher
// User node
CREATE (u:User {
  id: 'user123',
  username: 'john.doe',
  department: 'sales',
  risk_score: 45
})

// Host node
CREATE (h:Host {
  id: 'host456',
  hostname: 'WORKSTATION-01',
  ip_address: '192.168.1.100',
  os: 'Windows 10'
})

// Process node
CREATE (p:Process {
  id: 'proc789',
  name: 'powershell.exe',
  pid: 1234,
  command_line: 'powershell.exe -enc ...'
})

// File node
CREATE (f:File {
  id: 'file012',
  path: 'C:\\Users\\john\\documents\\data.xlsx',
  hash: 'abc123...'
})
```

### Relationship Types

```cypher
// Authentication
(u:User)-[:AUTHENTICATED_TO {timestamp, success}]->(h:Host)

// Process execution
(u:User)-[:EXECUTED {timestamp}]->(p:Process)-[:ON_HOST]->(h:Host)

// File access
(p:Process)-[:ACCESSED {timestamp, action}]->(f:File)

// Network connection
(p:Process)-[:CONNECTED_TO {timestamp, port}]->(ip:IPAddress)

// Parent-child process
(parent:Process)-[:SPAWNED {timestamp}]->(child:Process)
```

## API Endpoints

### Lateral Movement Detection

```http
POST /api/v1/entity-analytics/detect-lateral-movement
{
  "user_id": "user123",
  "time_window": "24h"
}
```

### Attack Chain Reconstruction

```http
GET /api/v1/entity-analytics/attack-chain/{alert_id}
```

### Entity Relationships

```http
GET /api/v1/entity-analytics/entities/{entity_id}/relationships?depth=3
```

### Path Finding

```http
POST /api/v1/entity-analytics/find-path
{
  "source_entity": "user123",
  "target_entity": "host456",
  "max_depth": 5
}
```

## Cypher Query Examples

### Detect Lateral Movement

```cypher
// Find users authenticating to multiple hosts in short time window
MATCH (u:User)-[auth:AUTHENTICATED_TO]->(h:Host)
WHERE auth.timestamp > datetime() - duration('PT1H')
WITH u, COUNT(DISTINCT h) as host_count
WHERE host_count > 5
RETURN u.username, host_count
ORDER BY host_count DESC
```

### Find Process Execution Chain

```cypher
// Find process execution chain from initial access
MATCH path = (root:Process)-[:SPAWNED*1..5]->(leaf:Process)
WHERE NOT (root)<-[:SPAWNED]-()
RETURN path
```

### Detect Pass-the-Hash

```cypher
// Detect same credential used on multiple hosts
MATCH (u:User)-[a1:AUTHENTICATED_TO]->(h1:Host)
MATCH (u:User)-[a2:AUTHENTICATED_TO]->(h2:Host)
WHERE h1 <> h2
  AND a1.auth_method = 'NTLM'
  AND a2.auth_method = 'NTLM'
  AND a2.timestamp - a1.timestamp < duration('PT5M')
RETURN u.username, h1.hostname, h2.hostname,
       a1.timestamp, a2.timestamp
```

### Identify Critical Assets

```cypher
// Find hosts with highest connectivity (potential targets)
MATCH (h:Host)
OPTIONAL MATCH (h)<-[r]-()
WITH h, COUNT(r) as connection_count
RETURN h.hostname, h.ip_address, connection_count
ORDER BY connection_count DESC
LIMIT 20
```

## Configuration

```yaml
# config/entity-analytics.yaml

neo4j:
  uri: bolt://neo4j:7687
  username: neo4j
  password: ${NEO4J_PASSWORD}
  database: siem

entity_extraction:
  user_id_fields: [user, username, user_id]
  host_id_fields: [hostname, host, ip_address]
  process_id_fields: [process_name, pid]

detection:
  lateral_movement:
    min_hosts_threshold: 3
    time_window_minutes: 60

  attack_chain:
    max_depth: 10
    min_confidence: 0.7

graph_maintenance:
  node_retention_days: 90
  relationship_retention_days: 365
  cleanup_schedule: "0 2 * * *"  # Daily at 2 AM
```

## Technology Stack

- **Graph Database**: Neo4j 5.x
- **Language**: Python 3.11+
- **Neo4j Driver**: neo4j-python-driver
- **Framework**: FastAPI
- **Graph Algorithms**: NetworkX, neo4j-graph-algorithms

## Running the Service

```bash
# Start Neo4j
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.12

# Run entity analytics service
cd services/entity-analytics
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8006
```

## Example Use Cases

### 1. Ransomware Attack Chain
Reconstruct the full attack chain from initial phishing email to ransomware execution:

```
Email (Phishing) →
  User Opens Attachment →
    Word.exe spawns PowerShell →
      PowerShell downloads payload →
        Malware executes →
          Lateral movement to file server →
            Ransomware encryption
```

### 2. Insider Threat Detection
Identify employee accessing unusual number of sensitive files before resignation:

```
User behavior change →
  Access to HR systems →
    Download employee database →
      Access to source code repository →
        Large data transfer to personal cloud
```

### 3. APT Detection
Identify sophisticated multi-stage attacks:

```
Initial compromise →
  Establish persistence →
    Credential harvesting →
      Lateral movement →
        Data staging →
          Exfiltration
```

## Performance Optimization

- **Indexing**: Create indexes on frequently queried properties
- **Query optimization**: Use query profiling and optimization
- **Partitioning**: Partition graph by time periods
- **Caching**: Cache frequently accessed subgraphs
- **Batch operations**: Batch node/relationship creation

## Monitoring

Metrics exposed:
- `entity_analytics_nodes_total`
- `entity_analytics_relationships_total`
- `entity_analytics_queries_total`
- `entity_analytics_lateral_movement_detected_total`
- `entity_analytics_attack_chains_reconstructed_total`

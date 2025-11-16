# Threat Hunting Service

Hypothesis-driven threat hunting platform with investigation tools, hunting notebooks, and query libraries.

## Overview

The Threat Hunting Service provides security analysts with tools to proactively search for threats, conduct investigations, and develop hunting hypotheses based on threat intelligence and behavioral analytics.

## Features

### 1. Hypothesis-Driven Hunting
- **Hypothesis management**: Create, track, and validate hunting hypotheses
- **Hypothesis templates**: Pre-built hypothesis templates based on MITRE ATT&CK
- **Hypothesis testing**: Structured approach to test and validate hypotheses
- **Results tracking**: Document findings and outcomes

### 2. Hunting Query Library
- **Pre-built queries**: 200+ hunting queries for common threats
- **MITRE ATT&CK mapped**: Queries mapped to ATT&CK techniques
- **Custom queries**: Create and share custom hunting queries
- **Query templates**: Parameterized query templates
- **Query validation**: Syntax checking and performance validation

### 3. Hunting Notebooks
- **Interactive analysis**: Jupyter-style notebooks for investigation
- **Data exploration**: Interactive data exploration and visualization
- **Code execution**: Execute Python, KQL, and Cypher queries
- **Collaboration**: Share notebooks with team members
- **Export results**: Export findings to reports

### 4. Investigation Workspace
- **Case management**: Create investigation cases from hunting findings
- **Evidence collection**: Collect and organize evidence
- **Timeline analysis**: Build attack timelines
- **Pivot analysis**: Pivot between related entities and events
- **Annotation**: Add notes and context to findings

### 5. Hunting Dashboards
- **Real-time monitoring**: Monitor hunting activities
- **Metrics tracking**: Track hunting effectiveness
- **Threat landscape**: Visualize threat landscape
- **Hunt campaigns**: Track ongoing hunt campaigns

## Architecture

```
┌──────────────────┐
│  Hunting UI      │
│  - Notebooks     │
│  - Query Builder │
│  - Dashboards    │
└────────┬─────────┘
         │
┌────────▼─────────┐
│  Hunting API     │
│  - Hypothesis    │
│  - Queries       │
│  - Results       │
└────────┬─────────┘
         │
┌────────▼─────────┐
│ Query Engine     │
│  - Elasticsearch │
│  - Neo4j         │
│  - PostgreSQL    │
└────────┬─────────┘
         │
┌────────▼─────────┐
│  Results Store   │
│  (PostgreSQL)    │
└──────────────────┘
```

## Hunting Hypothesis Framework

### Hypothesis Structure

```json
{
  "hypothesis_id": "HYPO-2024-001",
  "name": "Detect Kerberoasting Activity",
  "description": "Hunt for potential Kerberoasting attacks targeting service accounts",
  "mitre_technique": "T1558.003",
  "severity": "high",
  "status": "active",
  "created_by": "analyst@company.com",
  "created_at": "2024-01-15T10:00:00Z",
  "indicators": [
    "Unusual Kerberos TGS requests",
    "Requests for RC4 encrypted tickets",
    "Multiple SPN requests in short time"
  ],
  "queries": [
    {
      "name": "Find TGS requests",
      "query": "event.code:4769 AND service_ticket_encryption:0x17",
      "data_source": "windows_events"
    }
  ],
  "expected_findings": "Service accounts with unusual TGS request patterns",
  "validation_criteria": [
    "Multiple TGS requests from single user",
    "RC4 encryption requested",
    "Service account targeted"
  ]
}
```

## Hunting Query Library

### Query Categories

1. **Initial Access** (T1078, T1190, T1133)
   - Brute force detection
   - VPN anomalies
   - Web application exploitation

2. **Execution** (T1059, T1053, T1047)
   - PowerShell abuse
   - Scheduled task creation
   - WMI execution

3. **Persistence** (T1053, T1543, T1547)
   - Registry modifications
   - Service installation
   - Startup items

4. **Privilege Escalation** (T1068, T1134, T1548)
   - Token manipulation
   - Exploit usage
   - UAC bypass

5. **Defense Evasion** (T1070, T1218, T1497)
   - Log deletion
   - LOLBin abuse
   - Process injection

6. **Credential Access** (T1003, T1558, T1110)
   - LSASS access
   - Kerberoasting
   - Password spraying

7. **Discovery** (T1087, T1018, T1083)
   - Account enumeration
   - Network scanning
   - File discovery

8. **Lateral Movement** (T1021, T1210)
   - RDP usage
   - SMB exploitation
   - Remote services

9. **Collection** (T1005, T1039, T1056)
   - Data staging
   - Archive creation
   - Clipboard capture

10. **Exfiltration** (T1041, T1048, T1567)
    - Unusual uploads
    - DNS tunneling
    - Cloud storage usage

### Example Hunting Queries

#### 1. Hunt for Kerberoasting

```python
# Elasticsearch query
query = {
    "query": {
        "bool": {
            "must": [
                {"term": {"event.code": "4769"}},
                {"term": {"service_ticket_encryption": "0x17"}},
                {"range": {"@timestamp": {"gte": "now-24h"}}}
            ]
        }
    },
    "aggs": {
        "by_user": {
            "terms": {"field": "user.name", "size": 100},
            "aggs": {
                "unique_spns": {
                    "cardinality": {"field": "service_name"}
                }
            }
        }
    }
}
```

#### 2. Hunt for PowerShell Obfuscation

```python
# Hunt for base64 encoded PowerShell
query = """
event.category:process AND
process.name:powershell.exe AND
process.command_line:(*-enc* OR *-encodedcommand* OR
                      *FromBase64String* OR *ToBase64String*)
"""
```

#### 3. Hunt for Credential Dumping

```python
# Hunt for LSASS access
query = """
event.category:process AND
(process.name:procdump*.exe OR process.name:mimikatz.exe OR
 process.name:pwdump*.exe) OR
(target.process.name:lsass.exe AND
 event.action:open_process)
"""
```

#### 4. Hunt for Lateral Movement via WMI

```cypher
// Neo4j query for WMI lateral movement
MATCH (source:Host)<-[:EXECUTED_ON]-(proc:Process {name: "wmiprvse.exe"})
MATCH (proc)-[:SPAWNED]->(child:Process)
MATCH (child)-[:ACCESSED]->(target:Host)
WHERE source <> target
  AND proc.timestamp > datetime() - duration('P1D')
RETURN source.hostname, target.hostname, child.name,
       proc.timestamp
ORDER BY proc.timestamp DESC
```

## API Endpoints

### Hypothesis Management

```http
POST /api/v1/hunting/hypotheses
GET /api/v1/hunting/hypotheses
GET /api/v1/hunting/hypotheses/{hypothesis_id}
PUT /api/v1/hunting/hypotheses/{hypothesis_id}
DELETE /api/v1/hunting/hypotheses/{hypothesis_id}
```

### Query Library

```http
GET /api/v1/hunting/queries?category=credential_access&mitre_technique=T1003
GET /api/v1/hunting/queries/{query_id}
POST /api/v1/hunting/queries/{query_id}/execute
```

### Hunting Notebooks

```http
GET /api/v1/hunting/notebooks
POST /api/v1/hunting/notebooks
GET /api/v1/hunting/notebooks/{notebook_id}
PUT /api/v1/hunting/notebooks/{notebook_id}
```

### Hunt Results

```http
GET /api/v1/hunting/results?hypothesis_id={id}
POST /api/v1/hunting/results
```

## Hunting Methodology

### 1. Hypothesis Development
```
Intelligence Gathering →
  Threat Modeling →
    Hypothesis Creation →
      Query Development →
        Testing
```

### 2. Hunt Execution
```
Prepare Environment →
  Execute Queries →
    Analyze Results →
      Identify Anomalies →
        Validate Findings →
          Document Results
```

### 3. Continuous Improvement
```
Track Metrics →
  Analyze Effectiveness →
    Update Hypotheses →
      Refine Queries →
        Share Knowledge
```

## Hunting Notebook Example

```python
# Threat Hunting Notebook: Detect Kerberoasting
# Hypothesis: HYPO-2024-001
# Author: threat.hunter@company.com
# Date: 2024-01-15

# Import libraries
import pandas as pd
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta

# Initialize connection
es = Elasticsearch(['http://elasticsearch:9200'])

# Step 1: Query for TGS-REQ events
query = {
    "query": {
        "bool": {
            "must": [
                {"term": {"event.code": "4769"}},
                {"range": {"@timestamp": {"gte": "now-24h"}}}
            ]
        }
    },
    "size": 10000
}

results = es.search(index="windows-*", body=query)
df = pd.DataFrame([hit['_source'] for hit in results['hits']['hits']])

# Step 2: Analyze TGS request patterns
tgs_by_user = df.groupby('user.name').agg({
    'service_name': 'nunique',
    '@timestamp': 'count'
}).rename(columns={'service_name': 'unique_spns', '@timestamp': 'request_count'})

# Step 3: Identify suspicious patterns
suspicious = tgs_by_user[
    (tgs_by_user['unique_spns'] > 5) &
    (tgs_by_user['request_count'] > 10)
]

print(f"Found {len(suspicious)} potentially suspicious users")
print(suspicious)

# Step 4: Deep dive into top suspect
if len(suspicious) > 0:
    top_suspect = suspicious.index[0]
    suspect_events = df[df['user.name'] == top_suspect]
    print(f"\nAnalyzing user: {top_suspect}")
    print(f"SPNs requested: {suspect_events['service_name'].unique()}")

# Step 5: Cross-reference with authentication logs
# ... additional analysis ...

# Step 6: Document findings
# ... create case if threat confirmed ...
```

## Configuration

```yaml
# config/hunting.yaml

hunting:
  query_timeout_seconds: 300
  max_results: 100000
  notebook_session_timeout_minutes: 120

query_library:
  auto_update: true
  update_source: "https://hunting-queries.example.com"

hypothesis:
  auto_expire_days: 90
  require_validation: true

data_sources:
  elasticsearch:
    - hosts: ["elasticsearch:9200"]
  neo4j:
    uri: "bolt://neo4j:7687"
  postgres:
    uri: "postgresql://postgres:5432/siem"
```

## Technology Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Notebooks**: JupyterHub, Jupyter Lab
- **Query Engines**: Elasticsearch, Neo4j
- **Visualization**: Plotly, Matplotlib
- **Database**: PostgreSQL

## Running the Service

```bash
cd services/hunting-service
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8007
```

## Metrics

- `hunting_hypotheses_total`
- `hunting_queries_executed_total`
- `hunting_queries_duration_seconds`
- `hunting_findings_total`
- `hunting_notebooks_created_total`

# Digital Forensics Investigation Service

Advanced digital forensics service providing evidence collection, preservation, timeline analysis, and investigation management with chain of custody tracking.

## Features

- **Evidence Collection**: Automated collection of multiple evidence types
  - Memory dumps (RAM)
  - Disk images (forensically sound)
  - Network traffic captures (PCAP)
  - Log files with time-based filtering
- **Chain of Custody**: Complete audit trail for all evidence
- **Cryptographic Hashing**: MD5 and SHA-256 verification of evidence integrity
- **Timeline Analysis**: Automated event timeline reconstruction
- **Artifact Analysis**: Support for Windows and Linux forensic artifacts
- **Case Management**: Comprehensive investigation case tracking
- **Forensic Reporting**: Detailed investigation reports

## Evidence Types Supported

| Type | Description | Tools Used |
|------|-------------|------------|
| Memory Dump | Live memory capture | WinPmem, LiME |
| Disk Image | Forensic disk imaging | dd, FTK Imager |
| Network PCAP | Network traffic capture | tcpdump, Wireshark |
| Log Files | System and application logs | Direct collection |
| Registry Hives | Windows registry files | Registry parsers |
| Browser Artifacts | Browser history, cookies | Browser forensics |

## API Endpoints

### Health Check
```bash
GET /health
```

### Create Forensic Case
```bash
POST /api/v1/cases
Content-Type: application/json

{
  "case_name": "Incident 2024-001 Investigation",
  "incident_id": "INC-2024-001",
  "investigator": "John Smith"
}
```

Response:
```json
{
  "case_id": "CASE-20240115103000",
  "case_name": "Incident 2024-001 Investigation",
  "incident_id": "INC-2024-001",
  "investigator": "John Smith",
  "created_at": "2024-01-15T10:30:00.000000",
  "state": "initial",
  "evidence_count": 0,
  "findings_count": 0
}
```

### Get Case Details
```bash
GET /api/v1/cases/{case_id}
```

### Collect Evidence
```bash
POST /api/v1/evidence/collect
Content-Type: application/json

{
  "case_id": "CASE-20240115103000",
  "evidence_type": "memory_dump",
  "target_system": "workstation-42.example.com",
  "collector": "John Smith",
  "parameters": {}
}
```

Evidence types:
- `memory_dump` - Collect RAM dump
- `disk_image` - Forensic disk image (parameters: `drive`)
- `network_pcap` - Network capture (parameters: `duration_seconds`, `filter`)
- `log_file` - Log collection (parameters: `log_paths`)

Response:
```json
{
  "evidence_id": "MEM-CASE-20240115103000-20240115103015",
  "evidence_type": "memory_dump",
  "description": "Memory dump from workstation-42.example.com",
  "source_system": "workstation-42.example.com",
  "collection_timestamp": "2024-01-15T10:30:15.000000",
  "collector": "John Smith",
  "hash_sha256": null,
  "chain_of_custody_entries": 1
}
```

### Conduct Investigation
```bash
POST /api/v1/investigations/conduct
Content-Type: application/json

{
  "case_id": "CASE-20240115103000",
  "target_systems": [
    "workstation-42.example.com",
    "server-db-01.example.com"
  ]
}
```

Response:
```json
{
  "case_id": "CASE-20240115103000",
  "evidence_count": 4,
  "timeline_events": 12,
  "findings_count": 2,
  "recommendations": [
    "Isolate affected systems immediately",
    "Run antimalware scan on all systems",
    "Reset credentials for affected users"
  ]
}
```

### Get Forensic Timeline
```bash
GET /api/v1/cases/{case_id}/timeline
```

### Generate Report
```bash
GET /api/v1/cases/{case_id}/report
```

Returns comprehensive JSON report including:
- Case information
- Evidence summary with hashes
- Timeline summary
- Findings
- Recommendations

### Statistics
```bash
GET /api/v1/stats
```

### Metrics
```bash
GET /metrics
```

## Investigation Workflow

### 1. Create Case
```python
import requests

# Create forensic case
response = requests.post(
    "http://localhost:8092/api/v1/cases",
    json={
        "case_name": "Ransomware Investigation",
        "incident_id": "INC-2024-042",
        "investigator": "Jane Doe"
    }
)
case = response.json()
case_id = case['case_id']
```

### 2. Collect Evidence
```python
# Collect memory dump
requests.post(
    "http://localhost:8092/api/v1/evidence/collect",
    json={
        "case_id": case_id,
        "evidence_type": "memory_dump",
        "target_system": "server-web-01",
        "collector": "Jane Doe"
    }
)

# Collect disk image
requests.post(
    "http://localhost:8092/api/v1/evidence/collect",
    json={
        "case_id": case_id,
        "evidence_type": "disk_image",
        "target_system": "server-web-01",
        "collector": "Jane Doe",
        "parameters": {"drive": "C:"}
    }
)

# Collect network capture
requests.post(
    "http://localhost:8092/api/v1/evidence/collect",
    json={
        "case_id": case_id,
        "evidence_type": "network_pcap",
        "target_system": "eth0",
        "collector": "Jane Doe",
        "parameters": {
            "duration_seconds": 300,
            "filter": "tcp port 443"
        }
    }
)
```

### 3. Conduct Investigation
```python
# Run full investigation
response = requests.post(
    "http://localhost:8092/api/v1/investigations/conduct",
    json={
        "case_id": case_id,
        "target_systems": ["server-web-01", "server-db-01"]
    }
)
results = response.json()
print(f"Found {results['findings_count']} findings")
```

### 4. Generate Report
```python
# Get full forensic report
response = requests.get(f"http://localhost:8092/api/v1/cases/{case_id}/report")
report = response.json()
print(report)
```

## Chain of Custody

Every evidence item maintains a complete chain of custody:

```json
{
  "evidence_id": "MEM-CASE-20240115103000-20240115103015",
  "chain_of_custody": [
    {
      "timestamp": "2024-01-15T10:30:15.000000",
      "action": "collected",
      "performer": "John Smith",
      "notes": "Memory dump collected from workstation-42.example.com"
    },
    {
      "timestamp": "2024-01-15T10:30:20.000000",
      "action": "preserved",
      "performer": "system",
      "notes": "Evidence preserved at /forensics/evidence/MEM-..."
    }
  ]
}
```

## Forensic States

Cases progress through defined states:

1. **INITIAL** - Case created
2. **COLLECTION** - Collecting evidence
3. **PRESERVATION** - Preserving and hashing evidence
4. **ANALYSIS** - Analyzing artifacts and building timeline
5. **REPORTING** - Generating findings and recommendations
6. **CLOSED** - Investigation complete

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Service port | 8092 |
| `ENV` | Environment (development/production) | production |
| `EVIDENCE_STORAGE_PATH` | Path to store evidence | /forensics/evidence |

## Running Locally

### With Docker
```bash
docker build -t forensics-investigation .
docker run -p 8092:8092 -v /data/forensics:/forensics/evidence forensics-investigation
```

### With Python
```bash
pip install -r requirements.txt
python main.py
```

## Integration Examples

### cURL
```bash
# Create case
CASE_ID=$(curl -X POST http://localhost:8092/api/v1/cases \
  -H "Content-Type: application/json" \
  -d '{
    "case_name": "Test Investigation",
    "incident_id": "INC-TEST-001",
    "investigator": "Test User"
  }' | jq -r '.case_id')

# Collect evidence
curl -X POST http://localhost:8092/api/v1/evidence/collect \
  -H "Content-Type: application/json" \
  -d "{
    \"case_id\": \"$CASE_ID\",
    \"evidence_type\": \"memory_dump\",
    \"target_system\": \"test-host\",
    \"collector\": \"Test User\"
  }"

# Get report
curl http://localhost:8092/api/v1/cases/$CASE_ID/report
```

## Monitoring

The service exposes Prometheus metrics at `/metrics`:

- `forensics_investigation_requests_total` - Total investigation requests by case state
- `forensics_evidence_collection_total` - Total evidence collections by type
- `forensics_investigation_duration_seconds` - Investigation duration

## Development

### Adding New Evidence Types
1. Add to `EvidenceType` enum in `investigator.py`
2. Create collection method in `EvidenceCollector`
3. Add to `collect_evidence` endpoint in `main.py`

### Extending Artifact Analysis
1. Add analysis methods to `ArtifactAnalyzer`
2. Update `_generate_findings()` to use new analysis
3. Document new artifact types

## Best Practices

1. **Evidence Integrity**: Always verify hashes before analysis
2. **Chain of Custody**: Document every evidence transfer
3. **Write Protection**: Never modify original evidence
4. **Secure Storage**: Encrypt evidence at rest
5. **Access Control**: Limit evidence access to authorized personnel
6. **Documentation**: Maintain detailed investigation notes
7. **Legal Compliance**: Follow applicable laws and regulations

## License

Copyright © 2024 Enterprise Security SIEM

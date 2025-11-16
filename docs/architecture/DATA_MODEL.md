# SIEM Data Model

## Overview

This document defines the comprehensive data models used across the SIEM platform.

## Event Schema

### Common Event Format (CEF)

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_version": "1.0",
  "timestamp": "2025-01-15T10:30:45.123Z",
  "ingestion_time": "2025-01-15T10:30:46.456Z",
  "tenant_id": "org_12345",

  "source": {
    "type": "server|network|application|cloud|endpoint|iot",
    "category": "authentication|network|file|process|registry|email|web",
    "product": "windows|linux|aws|azure|firewall|ids|av",
    "vendor": "microsoft|cisco|palo_alto|crowdstrike",
    "hostname": "web-server-01",
    "ip": "10.0.1.100",
    "mac": "00:1B:44:11:3A:B7",
    "fqdn": "web-server-01.example.com",
    "zone": "dmz|internal|external",
    "location": {
      "datacenter": "us-east-1",
      "rack": "A-12",
      "geo": {
        "country": "US",
        "city": "New York",
        "lat": 40.7128,
        "lon": -74.0060
      }
    }
  },

  "event": {
    "type": "authentication|access|change|alert|audit",
    "action": "login|logout|create|delete|modify|block|allow",
    "outcome": "success|failure|unknown",
    "severity": "critical|high|medium|low|info",
    "category": "security|operational|compliance",
    "name": "User login attempt",
    "description": "User authentication via SSH",
    "risk_score": 75,
    "confidence": 0.95
  },

  "user": {
    "id": "uid_67890",
    "username": "john.doe",
    "email": "john.doe@example.com",
    "domain": "CORPORATE",
    "full_name": "John Doe",
    "department": "Engineering",
    "title": "Senior Engineer",
    "manager": "jane.smith",
    "roles": ["developer", "admin"],
    "groups": ["engineering", "privileged_users"],
    "risk_score": 45
  },

  "destination": {
    "ip": "192.168.1.50",
    "port": 22,
    "hostname": "db-server-01",
    "fqdn": "db-server-01.internal",
    "service": "ssh",
    "zone": "internal"
  },

  "network": {
    "protocol": "tcp|udp|icmp",
    "direction": "inbound|outbound|internal",
    "bytes_sent": 1024,
    "bytes_received": 2048,
    "packets_sent": 10,
    "packets_received": 15,
    "session_id": "sess_abc123",
    "vlan_id": 100,
    "application": "ssh|http|dns|smtp"
  },

  "file": {
    "path": "/etc/passwd",
    "name": "passwd",
    "extension": "",
    "size": 2048,
    "hash": {
      "md5": "5d41402abc4b2a76b9719d911017c592",
      "sha1": "aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d",
      "sha256": "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae"
    },
    "owner": "root",
    "permissions": "644",
    "created": "2025-01-01T00:00:00Z",
    "modified": "2025-01-15T10:00:00Z",
    "accessed": "2025-01-15T10:30:00Z"
  },

  "process": {
    "pid": 1234,
    "name": "sshd",
    "path": "/usr/sbin/sshd",
    "command_line": "/usr/sbin/sshd -D",
    "user": "root",
    "parent_pid": 1,
    "parent_name": "systemd",
    "hash": {
      "sha256": "abc123..."
    },
    "signature_status": "signed|unsigned|invalid"
  },

  "threat": {
    "framework": "MITRE_ATT&CK",
    "tactic": ["TA0001"],
    "technique": ["T1078", "T1110"],
    "indicator_type": "ip|domain|hash|email|url",
    "indicator_value": "malicious.com",
    "malware_family": "emotet|ransomware|trojan",
    "threat_actor": "APT28|APT29",
    "confidence": 0.85,
    "severity": "high",
    "first_seen": "2025-01-01T00:00:00Z",
    "last_seen": "2025-01-15T10:30:45Z",
    "source": "crowdstrike|virustotal|alienvault"
  },

  "enrichment": {
    "geo_ip": {
      "country": "US",
      "city": "New York",
      "asn": "AS15169",
      "org": "Google LLC",
      "is_vpn": false,
      "is_proxy": false,
      "is_tor": false,
      "is_hosting": false
    },
    "asset": {
      "criticality": "critical|high|medium|low",
      "owner": "john.doe",
      "cost_center": "CC-1234",
      "compliance_scope": ["pci", "hipaa"],
      "tags": ["production", "web-server"]
    },
    "user_context": {
      "normal_login_hours": "09:00-17:00",
      "normal_locations": ["New York", "Boston"],
      "normal_devices": ["device_001"],
      "avg_login_frequency": 5,
      "last_password_change": "2025-01-01T00:00:00Z"
    }
  },

  "metadata": {
    "correlation_id": "corr_xyz789",
    "parent_event_id": "parent_uuid",
    "related_events": ["event_uuid1", "event_uuid2"],
    "tags": ["brute_force", "suspicious"],
    "notes": "Investigated by SOC analyst",
    "pipeline_version": "2.1.0",
    "retention_days": 365
  },

  "raw": {
    "message": "Original log message here",
    "format": "syslog|json|xml|cef"
  }
}
```

## Alert Schema

```json
{
  "alert_id": "alert_550e8400",
  "timestamp": "2025-01-15T10:30:45.123Z",
  "tenant_id": "org_12345",

  "rule": {
    "id": "rule_001",
    "name": "SSH Brute Force Detection",
    "version": "1.2",
    "type": "correlation|ml|threshold|signature",
    "category": "authentication|malware|data_exfiltration|lateral_movement",
    "framework": "MITRE_ATT&CK",
    "tactics": ["TA0001 - Initial Access"],
    "techniques": ["T1110 - Brute Force"]
  },

  "severity": "critical|high|medium|low|info",
  "priority": 1-10,
  "risk_score": 85,
  "confidence": 0.92,

  "status": "new|acknowledged|investigating|false_positive|resolved",
  "disposition": "true_positive|false_positive|benign|unknown",

  "title": "SSH Brute Force Attack Detected",
  "description": "Multiple failed SSH login attempts from 203.0.113.50",

  "entities": {
    "source_ips": ["203.0.113.50"],
    "destination_ips": ["10.0.1.100"],
    "users": ["root", "admin", "backup"],
    "hosts": ["web-server-01"],
    "files": [],
    "processes": ["sshd"]
  },

  "events": {
    "count": 15,
    "event_ids": ["event_1", "event_2", "..."],
    "first_event_time": "2025-01-15T10:25:00Z",
    "last_event_time": "2025-01-15T10:30:45Z",
    "timeframe": "5m"
  },

  "enrichment": {
    "threat_intel": {
      "is_malicious": true,
      "reputation_score": 15,
      "categories": ["scanner", "malware_c2"],
      "sources": ["alienvault", "emergingthreats"]
    },
    "asset_impact": {
      "criticality": "high",
      "affected_services": ["customer_portal"],
      "potential_exposure": "customer_data"
    }
  },

  "response": {
    "auto_actions": ["block_ip", "notify_soc"],
    "playbook_id": "playbook_brute_force",
    "playbook_status": "running|completed|failed",
    "blocked_ips": ["203.0.113.50"]
  },

  "assignment": {
    "assigned_to": "analyst_jane",
    "assigned_at": "2025-01-15T10:31:00Z",
    "team": "soc_team_1"
  },

  "sla": {
    "acknowledge_by": "2025-01-15T10:45:00Z",
    "resolve_by": "2025-01-15T12:30:00Z",
    "sla_breached": false
  },

  "investigation": {
    "notes": "Confirmed brute force from known scanner IP",
    "evidence": ["screenshot_1", "pcap_1"],
    "timeline": [
      {
        "timestamp": "2025-01-15T10:31:00Z",
        "action": "acknowledged",
        "user": "analyst_jane"
      }
    ]
  },

  "related_alerts": ["alert_550e8401", "alert_550e8402"],
  "incident_id": "incident_123",

  "notifications": {
    "channels": ["email", "slack"],
    "sent_to": ["soc@example.com", "#security-alerts"],
    "sent_at": "2025-01-15T10:30:46Z"
  },

  "metadata": {
    "tags": ["automated", "high_priority"],
    "custom_fields": {
      "ticket_id": "JIRA-1234"
    }
  }
}
```

## Incident Schema

```json
{
  "incident_id": "incident_12345",
  "tenant_id": "org_12345",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T12:00:00Z",

  "status": "new|triaged|investigating|contained|remediated|closed",
  "severity": "critical|high|medium|low",
  "priority": 1-5,

  "title": "Ransomware Infection on Finance Network",
  "description": "Multiple hosts infected with ransomware variant",

  "category": "malware|data_breach|insider_threat|dos|unauthorized_access",
  "type": "security|privacy|availability|integrity",

  "timeline": {
    "detected_at": "2025-01-15T10:30:00Z",
    "reported_at": "2025-01-15T10:35:00Z",
    "triaged_at": "2025-01-15T10:40:00Z",
    "contained_at": "2025-01-15T11:00:00Z",
    "remediated_at": "2025-01-15T11:30:00Z",
    "closed_at": "2025-01-15T12:00:00Z"
  },

  "metrics": {
    "mttd": 300,  // Mean Time to Detect (seconds)
    "mtta": 600,  // Mean Time to Acknowledge
    "mttc": 1800, // Mean Time to Contain
    "mttr": 3600  // Mean Time to Remediate
  },

  "alerts": {
    "count": 25,
    "alert_ids": ["alert_1", "alert_2", "..."],
    "critical": 5,
    "high": 15,
    "medium": 5
  },

  "affected_assets": {
    "hosts": ["finance-ws-01", "finance-ws-02", "finance-server-01"],
    "users": ["user1", "user2"],
    "count": 3
  },

  "impact": {
    "scope": "limited|moderate|widespread|critical",
    "confidentiality": "none|low|medium|high",
    "integrity": "none|low|medium|high",
    "availability": "none|low|medium|high",
    "financial_impact": 50000,
    "affected_customers": 0,
    "data_compromised": "none|suspected|confirmed"
  },

  "root_cause": {
    "vector": "phishing|vulnerability|misconfiguration|credential_theft",
    "description": "User clicked phishing email attachment",
    "vulnerability_id": "CVE-2023-12345",
    "initial_access": "2025-01-15T09:00:00Z"
  },

  "attack_chain": {
    "framework": "MITRE_ATT&CK",
    "tactics": [
      "TA0001 - Initial Access",
      "TA0002 - Execution",
      "TA0003 - Persistence",
      "TA0040 - Impact"
    ],
    "techniques": [
      "T1566.001 - Spearphishing Attachment",
      "T1204.002 - User Execution: Malicious File",
      "T1486 - Data Encrypted for Impact"
    ]
  },

  "threat": {
    "malware_family": "lockbit",
    "threat_actor": "unknown",
    "iocs": {
      "ips": ["198.51.100.50", "198.51.100.51"],
      "domains": ["malicious-c2.example"],
      "hashes": ["sha256:abc123...", "sha256:def456..."],
      "urls": ["http://malicious.example/payload"]
    }
  },

  "assignment": {
    "lead": "incident_manager_john",
    "team": ["analyst_jane", "analyst_bob", "forensics_alice"],
    "escalated_to": "ciso@example.com"
  },

  "response": {
    "containment_actions": [
      "Isolated infected hosts",
      "Blocked C2 domains",
      "Disabled compromised accounts"
    ],
    "remediation_actions": [
      "Restored from backup",
      "Patched vulnerability",
      "Reset all user passwords"
    ],
    "playbooks_executed": ["playbook_ransomware", "playbook_isolation"]
  },

  "evidence": {
    "logs": ["event_log_1", "event_log_2"],
    "files": ["malware_sample.exe", "ransom_note.txt"],
    "memory_dumps": ["host1.dmp"],
    "network_captures": ["traffic.pcap"],
    "screenshots": ["screenshot1.png"],
    "storage_location": "s3://evidence-bucket/incident-12345/"
  },

  "communication": {
    "internal_notifications": ["executive_team", "legal", "pr"],
    "external_notifications": [],
    "regulatory_reporting": {
      "required": true,
      "authorities": ["sec", "gdpr_authority"],
      "reported_at": "2025-01-16T10:00:00Z"
    }
  },

  "lessons_learned": {
    "what_worked": ["Backup recovery was successful", "Quick isolation prevented spread"],
    "what_failed": ["Phishing email bypassed filters"],
    "improvements": ["Implement email sandbox", "Additional user training"]
  },

  "notes": [
    {
      "timestamp": "2025-01-15T10:35:00Z",
      "user": "analyst_jane",
      "note": "Initial investigation notes..."
    }
  ],

  "related_incidents": ["incident_12344"],

  "metadata": {
    "tags": ["ransomware", "finance"],
    "ticket_id": "JIRA-5678",
    "cost": 75000,
    "documented": true
  }
}
```

## Asset Schema

```json
{
  "asset_id": "asset_12345",
  "tenant_id": "org_12345",

  "identification": {
    "hostname": "web-server-01",
    "fqdn": "web-server-01.example.com",
    "ip_addresses": ["10.0.1.100", "192.168.1.100"],
    "mac_addresses": ["00:1B:44:11:3A:B7"],
    "serial_number": "SN123456",
    "asset_tag": "TAG-001"
  },

  "type": "server|workstation|network_device|mobile|iot|cloud_resource",
  "category": "physical|virtual|cloud",

  "hardware": {
    "manufacturer": "Dell",
    "model": "PowerEdge R740",
    "cpu": "Intel Xeon 16-core",
    "memory": "64GB",
    "storage": "2TB SSD"
  },

  "software": {
    "os": "Ubuntu 22.04 LTS",
    "os_version": "22.04.1",
    "kernel": "5.15.0-56-generic",
    "installed_applications": [
      {
        "name": "nginx",
        "version": "1.22.0",
        "vendor": "Nginx Inc"
      }
    ],
    "patches": {
      "last_patched": "2025-01-10T00:00:00Z",
      "missing_patches": ["KB12345", "KB67890"]
    }
  },

  "network": {
    "zone": "dmz",
    "vlan": 100,
    "subnet": "10.0.1.0/24",
    "gateway": "10.0.1.1",
    "dns_servers": ["10.0.0.10", "10.0.0.11"],
    "listening_ports": [22, 80, 443]
  },

  "location": {
    "datacenter": "us-east-1",
    "building": "Building A",
    "floor": "3",
    "rack": "A-12",
    "position": "U15-U17"
  },

  "ownership": {
    "owner": "john.doe",
    "department": "Engineering",
    "cost_center": "CC-1234",
    "business_unit": "Product Development"
  },

  "criticality": {
    "level": "critical|high|medium|low",
    "business_impact": "high",
    "data_classification": "confidential|internal|public",
    "compliance_scope": ["pci", "soc2"],
    "rpo": 60,  // Recovery Point Objective (minutes)
    "rto": 30   // Recovery Time Objective (minutes)
  },

  "security": {
    "security_controls": {
      "antivirus": {
        "installed": true,
        "vendor": "CrowdStrike",
        "version": "7.04",
        "last_scan": "2025-01-15T08:00:00Z"
      },
      "edr": {
        "installed": true,
        "vendor": "SentinelOne"
      },
      "firewall": {
        "enabled": true,
        "rules_count": 25
      },
      "encryption": {
        "disk": true,
        "network": true
      }
    },
    "vulnerabilities": [
      {
        "cve": "CVE-2023-12345",
        "severity": "high",
        "cvss": 8.5,
        "discovered": "2025-01-10T00:00:00Z",
        "status": "open|remediated|accepted"
      }
    ],
    "risk_score": 65,
    "last_scan": "2025-01-14T00:00:00Z"
  },

  "services": [
    {
      "name": "Web Server",
      "port": 443,
      "protocol": "https",
      "description": "Customer portal"
    }
  ],

  "relationships": {
    "depends_on": ["db-server-01", "auth-server-01"],
    "supports": ["customer-portal"],
    "peers": ["web-server-02", "web-server-03"]
  },

  "lifecycle": {
    "purchased": "2023-01-15",
    "deployed": "2023-02-01",
    "warranty_expires": "2026-01-15",
    "eol_date": "2028-01-15",
    "status": "active|inactive|decommissioned"
  },

  "monitoring": {
    "monitored": true,
    "monitoring_tools": ["prometheus", "nagios"],
    "uptime_percentage": 99.95,
    "last_seen": "2025-01-15T12:00:00Z"
  },

  "metadata": {
    "tags": ["production", "web", "customer-facing"],
    "notes": "Primary web server for customer portal",
    "created_at": "2023-02-01T00:00:00Z",
    "updated_at": "2025-01-15T12:00:00Z"
  }
}
```

## User Schema

```json
{
  "user_id": "user_12345",
  "tenant_id": "org_12345",

  "identity": {
    "username": "john.doe",
    "email": "john.doe@example.com",
    "employee_id": "EMP-001",
    "full_name": "John Doe",
    "display_name": "John D.",
    "aliases": ["jdoe", "johnd"]
  },

  "authentication": {
    "primary_method": "sso|password|certificate",
    "mfa_enabled": true,
    "mfa_methods": ["totp", "sms"],
    "last_password_change": "2025-01-01T00:00:00Z",
    "password_expires": "2025-04-01T00:00:00Z",
    "failed_login_attempts": 0,
    "last_failed_login": null,
    "account_locked": false
  },

  "organization": {
    "department": "Engineering",
    "title": "Senior Software Engineer",
    "manager": "jane.smith",
    "cost_center": "CC-1234",
    "business_unit": "Product Development",
    "location": "New York Office",
    "employment_type": "full_time|contractor|vendor",
    "start_date": "2020-01-15",
    "end_date": null
  },

  "authorization": {
    "roles": ["developer", "ssh_access", "database_readonly"],
    "groups": ["engineering", "developers", "oncall"],
    "privileges": ["sudo_web_servers"],
    "access_level": "standard|privileged|admin"
  },

  "security": {
    "risk_score": 35,
    "risk_factors": ["privileged_access", "external_travel"],
    "clearance_level": "public|internal|confidential|secret",
    "background_check": "completed",
    "security_training": {
      "completed": true,
      "last_completed": "2025-01-10T00:00:00Z",
      "next_due": "2026-01-10T00:00:00Z"
    }
  },

  "behavior_baseline": {
    "normal_login_hours": "08:00-18:00",
    "normal_login_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
    "normal_locations": ["New York", "Boston"],
    "normal_devices": ["device_001", "device_002"],
    "avg_sessions_per_day": 5,
    "typical_resources_accessed": ["gitlab", "jira", "confluence"]
  },

  "activity": {
    "last_login": "2025-01-15T09:00:00Z",
    "last_activity": "2025-01-15T11:00:00Z",
    "total_logins": 1250,
    "active_sessions": 2,
    "devices": [
      {
        "device_id": "device_001",
        "type": "laptop",
        "os": "macOS",
        "last_seen": "2025-01-15T11:00:00Z",
        "trusted": true
      }
    ]
  },

  "compliance": {
    "requires_monitoring": true,
    "regulatory_scope": ["sox", "pci"],
    "data_access_level": "high",
    "privileged_user": true
  },

  "contacts": {
    "phone": "+1-555-0100",
    "mobile": "+1-555-0101",
    "emergency_contact": "Jane Doe: +1-555-0102"
  },

  "status": "active|suspended|disabled|terminated",

  "metadata": {
    "tags": ["developer", "oncall"],
    "notes": "Primary developer for authentication service",
    "created_at": "2020-01-15T00:00:00Z",
    "updated_at": "2025-01-15T00:00:00Z"
  }
}
```

## Detection Rule Schema

```json
{
  "rule_id": "rule_001",
  "tenant_id": "org_12345",
  "version": "1.2.0",

  "metadata": {
    "name": "SSH Brute Force Detection",
    "description": "Detects brute force SSH login attempts",
    "author": "security_team",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2025-01-15T00:00:00Z",
    "tags": ["authentication", "brute_force", "ssh"]
  },

  "type": "correlation|threshold|statistical|ml|signature",
  "category": "authentication|malware|exfiltration|lateral_movement",

  "severity": "critical|high|medium|low|info",
  "confidence": 0.85,

  "mitre_attack": {
    "tactics": ["TA0001"],
    "techniques": ["T1110", "T1110.001"],
    "sub_techniques": []
  },

  "logic": {
    "type": "correlation|threshold|statistical",
    "query": "event_type:authentication AND action:failed AND protocol:ssh",
    "conditions": [
      {
        "field": "event.action",
        "operator": "equals",
        "value": "failed"
      },
      {
        "field": "destination.port",
        "operator": "equals",
        "value": 22
      }
    ],
    "threshold": {
      "count": 5,
      "timeframe": "5m",
      "group_by": ["source.ip", "user.username"]
    },
    "followed_by": {
      "query": "event_type:authentication AND action:success AND protocol:ssh",
      "within": "10m",
      "same_fields": ["source.ip", "user.username"]
    }
  },

  "filters": {
    "whitelist": {
      "source_ips": ["10.0.0.0/8"],
      "users": ["monitoring_service"]
    }
  },

  "actions": {
    "create_alert": true,
    "alert_severity": "high",
    "notify": ["soc_team"],
    "execute_playbook": "playbook_brute_force",
    "auto_response": ["block_ip", "disable_account"]
  },

  "enabled": true,
  "testing_mode": false,

  "performance": {
    "avg_execution_time_ms": 150,
    "triggers_per_day": 25,
    "false_positive_rate": 0.05
  }
}
```

## Data Retention Policy

```yaml
data_types:
  raw_events:
    hot_storage: 30 days
    warm_storage: 90 days
    cold_storage: 7 years

  alerts:
    hot_storage: 90 days
    warm_storage: 1 year
    cold_storage: 7 years

  incidents:
    hot_storage: 2 years
    cold_storage: 10 years

  audit_logs:
    hot_storage: 1 year
    cold_storage: 7 years

  compliance_logs:
    retention: based on regulatory requirements
    pci_dss: 1 year
    hipaa: 6 years
    sox: 7 years
```

## Index Naming Conventions

```
events-{tenant}-{YYYY.MM.DD}
alerts-{tenant}-{YYYY.MM}
incidents-{tenant}-{YYYY.MM}
audit-{tenant}-{YYYY.MM}
metrics-{YYYY.MM.DD}
```

## Field Naming Standards

- Use lowercase with underscores
- Use hierarchical naming (e.g., `source.ip`, not `source_ip`)
- Use consistent naming across all schemas
- Follow Elastic Common Schema (ECS) where applicable
- Use ISO 8601 for timestamps
- Use UUID v4 for unique identifiers

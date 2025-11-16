#!/usr/bin/env python3
"""
Deception Platform

Advanced deception technology with honeypots, honeytokens, and active defense.
Detects and misleads attackers while gathering threat intelligence.
"""

import os
import time
import secrets
import hashlib
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import uvicorn
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app


class HoneypotType(str, Enum):
    """Types of honeypots"""
    SSH_SERVER = "ssh_server"
    WEB_SERVER = "web_server"
    DATABASE = "database"
    FILE_SERVER = "file_server"
    EMAIL_SERVER = "email_server"
    RDP_SERVER = "rdp_server"
    API_ENDPOINT = "api_endpoint"
    IOT_DEVICE = "iot_device"


class HoneytokenType(str, Enum):
    """Types of honeytokens"""
    CREDENTIAL = "credential"
    API_KEY = "api_key"
    DATABASE_RECORD = "database_record"
    FILE = "file"
    EMAIL = "email"
    URL = "url"
    AWS_KEY = "aws_key"
    COOKIE = "cookie"


class InteractionLevel(str, Enum):
    """Honeypot interaction levels"""
    LOW = "low"  # Limited interaction
    MEDIUM = "medium"  # Moderate interaction
    HIGH = "high"  # Full interaction


@dataclass
class Honeypot:
    """Honeypot configuration"""
    honeypot_id: str
    name: str
    type: HoneypotType
    interaction_level: InteractionLevel
    ip_address: str
    port: int
    protocol: str
    services: List[str]
    decoy_data: Dict
    created_at: datetime
    last_interaction: Optional[datetime] = None
    interactions_count: int = 0
    is_active: bool = True
    detected_attacks: List[str] = field(default_factory=list)


@dataclass
class Honeytoken:
    """Honeytoken (decoy credential/asset)"""
    token_id: str
    name: str
    type: HoneytokenType
    value: str
    location: str
    created_at: datetime
    accessed_at: Optional[datetime] = None
    accessed_by: Optional[str] = None
    access_count: int = 0
    is_active: bool = True
    alert_triggered: bool = False


@dataclass
class DeceptionInteraction:
    """Interaction with deception asset"""
    interaction_id: str
    timestamp: datetime
    asset_type: str  # "honeypot" or "honeytoken"
    asset_id: str
    source_ip: str
    source_port: int
    destination_port: int
    protocol: str
    payload: str
    attack_type: Optional[str] = None
    severity: str = "medium"
    attacker_fingerprint: Optional[str] = None


@dataclass
class ActiveDefense:
    """Active defense action"""
    action_id: str
    timestamp: datetime
    action_type: str
    target: str
    description: str
    success: bool
    details: Dict


# Pydantic models
class HoneypotCreate(BaseModel):
    name: str
    type: HoneypotType
    interaction_level: InteractionLevel
    ip_address: str
    port: int
    protocol: str = "TCP"
    services: List[str] = []
    decoy_data: Dict = {}


class HoneytokenCreate(BaseModel):
    name: str
    type: HoneytokenType
    location: str
    auto_generate: bool = True
    custom_value: Optional[str] = None


class InteractionReport(BaseModel):
    asset_id: str
    asset_type: str
    source_ip: str
    source_port: int
    destination_port: int
    protocol: str
    payload: str


# Prometheus metrics
honeypots_deployed = Gauge(
    'deception_honeypots_deployed',
    'Number of active honeypots',
    ['type']
)

honeytokens_deployed = Gauge(
    'deception_honeytokens_deployed',
    'Number of active honeytokens',
    ['type']
)

interactions_total = Counter(
    'deception_interactions_total',
    'Total deception asset interactions',
    ['asset_type', 'attack_type']
)

attacks_detected = Counter(
    'deception_attacks_detected_total',
    'Total attacks detected by deception assets',
    ['severity']
)

active_defense_actions = Counter(
    'deception_active_defense_actions_total',
    'Total active defense actions executed',
    ['action_type', 'success']
)


class DeceptionPlatform:
    """Advanced Deception Platform"""

    def __init__(self):
        self.app = FastAPI(
            title="Deception Platform",
            description="Advanced deception with honeypots, honeytokens, and active defense",
            version="1.0.0"
        )

        self.honeypots: Dict[str, Honeypot] = {}
        self.honeytokens: Dict[str, Honeytoken] = {}
        self.interactions: List[DeceptionInteraction] = []
        self.active_defenses: List[ActiveDefense] = []

        # Initialize default honeypots
        self.deploy_default_honeypots()

        self.setup_routes()

    def deploy_default_honeypots(self):
        """Deploy initial set of honeypots"""
        default_honeypots = [
            {
                "name": "SSH Honeypot - Server01",
                "type": HoneypotType.SSH_SERVER,
                "interaction_level": InteractionLevel.MEDIUM,
                "ip_address": "10.0.1.100",
                "port": 22,
                "protocol": "TCP",
                "services": ["ssh"],
                "decoy_data": {"banner": "Ubuntu 20.04 SSH Server", "version": "OpenSSH_8.2"}
            },
            {
                "name": "Web Server Honeypot",
                "type": HoneypotType.WEB_SERVER,
                "interaction_level": InteractionLevel.HIGH,
                "ip_address": "10.0.1.101",
                "port": 80,
                "protocol": "TCP",
                "services": ["http", "https"],
                "decoy_data": {"server": "Apache/2.4.41", "pages": ["/admin", "/login", "/api"]}
            },
            {
                "name": "Database Honeypot",
                "type": HoneypotType.DATABASE,
                "interaction_level": InteractionLevel.MEDIUM,
                "ip_address": "10.0.1.102",
                "port": 3306,
                "protocol": "TCP",
                "services": ["mysql"],
                "decoy_data": {"version": "MySQL 8.0", "databases": ["customers", "transactions"]}
            }
        ]

        for hp_config in default_honeypots:
            honeypot_id = f"hp-{secrets.token_hex(8)}"
            honeypot = Honeypot(
                honeypot_id=honeypot_id,
                name=hp_config["name"],
                type=hp_config["type"],
                interaction_level=hp_config["interaction_level"],
                ip_address=hp_config["ip_address"],
                port=hp_config["port"],
                protocol=hp_config["protocol"],
                services=hp_config["services"],
                decoy_data=hp_config["decoy_data"],
                created_at=datetime.utcnow()
            )
            self.honeypots[honeypot_id] = honeypot
            honeypots_deployed.labels(type=honeypot.type).inc()

    def setup_routes(self):
        """Setup API routes"""

        @self.app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "service": "deception-platform",
                "timestamp": datetime.utcnow().isoformat(),
                "honeypots": len(self.honeypots),
                "honeytokens": len(self.honeytokens),
                "interactions": len(self.interactions)
            }

        # Honeypot management
        @self.app.post("/api/v1/honeypots")
        async def create_honeypot(req: HoneypotCreate):
            """Deploy a new honeypot"""
            honeypot_id = f"hp-{secrets.token_hex(8)}"

            honeypot = Honeypot(
                honeypot_id=honeypot_id,
                name=req.name,
                type=req.type,
                interaction_level=req.interaction_level,
                ip_address=req.ip_address,
                port=req.port,
                protocol=req.protocol,
                services=req.services,
                decoy_data=req.decoy_data,
                created_at=datetime.utcnow()
            )

            self.honeypots[honeypot_id] = honeypot
            honeypots_deployed.labels(type=honeypot.type).inc()

            return {
                "status": "deployed",
                "honeypot": asdict(honeypot)
            }

        @self.app.get("/api/v1/honeypots")
        async def list_honeypots(type: Optional[HoneypotType] = None):
            """List all honeypots"""
            honeypots = list(self.honeypots.values())

            if type:
                honeypots = [hp for hp in honeypots if hp.type == type]

            return {
                "honeypots": [asdict(hp) for hp in honeypots],
                "count": len(honeypots)
            }

        @self.app.get("/api/v1/honeypots/{honeypot_id}")
        async def get_honeypot(honeypot_id: str):
            """Get honeypot details"""
            if honeypot_id not in self.honeypots:
                raise HTTPException(status_code=404, detail="Honeypot not found")

            return asdict(self.honeypots[honeypot_id])

        @self.app.delete("/api/v1/honeypots/{honeypot_id}")
        async def delete_honeypot(honeypot_id: str):
            """Remove a honeypot"""
            if honeypot_id not in self.honeypots:
                raise HTTPException(status_code=404, detail="Honeypot not found")

            honeypot = self.honeypots[honeypot_id]
            honeypots_deployed.labels(type=honeypot.type).dec()
            del self.honeypots[honeypot_id]

            return {"status": "removed", "honeypot_id": honeypot_id}

        # Honeytoken management
        @self.app.post("/api/v1/honeytokens")
        async def create_honeytoken(req: HoneytokenCreate):
            """Create a new honeytoken"""
            token_id = f"ht-{secrets.token_hex(8)}"

            # Generate token value
            if req.auto_generate:
                token_value = self.generate_honeytoken(req.type)
            else:
                token_value = req.custom_value or ""

            honeytoken = Honeytoken(
                token_id=token_id,
                name=req.name,
                type=req.type,
                value=token_value,
                location=req.location,
                created_at=datetime.utcnow()
            )

            self.honeytokens[token_id] = honeytoken
            honeytokens_deployed.labels(type=honeytoken.type).inc()

            return {
                "status": "created",
                "honeytoken": asdict(honeytoken)
            }

        @self.app.get("/api/v1/honeytokens")
        async def list_honeytokens(type: Optional[HoneytokenType] = None):
            """List all honeytokens"""
            honeytokens = list(self.honeytokens.values())

            if type:
                honeytokens = [ht for ht in honeytokens if ht.type == type]

            return {
                "honeytokens": [asdict(ht) for ht in honeytokens],
                "count": len(honeytokens)
            }

        @self.app.get("/api/v1/honeytokens/{token_id}")
        async def get_honeytoken(token_id: str):
            """Get honeytoken details"""
            if token_id not in self.honeytokens:
                raise HTTPException(status_code=404, detail="Honeytoken not found")

            return asdict(self.honeytokens[token_id])

        @self.app.delete("/api/v1/honeytokens/{token_id}")
        async def delete_honeytoken(token_id: str):
            """Remove a honeytoken"""
            if token_id not in self.honeytokens:
                raise HTTPException(status_code=404, detail="Honeytoken not found")

            honeytoken = self.honeytokens[token_id]
            honeytokens_deployed.labels(type=honeytoken.type).dec()
            del self.honeytokens[token_id]

            return {"status": "removed", "token_id": token_id}

        # Interaction reporting
        @self.app.post("/api/v1/interactions")
        async def report_interaction(req: InteractionReport):
            """Report an interaction with a deception asset"""
            interaction_id = f"int-{int(time.time() * 1000)}-{secrets.token_hex(4)}"

            # Classify attack type
            attack_type = self.classify_attack(req.payload, req.destination_port)
            severity = self.calculate_severity(attack_type)

            interaction = DeceptionInteraction(
                interaction_id=interaction_id,
                timestamp=datetime.utcnow(),
                asset_type=req.asset_type,
                asset_id=req.asset_id,
                source_ip=req.source_ip,
                source_port=req.source_port,
                destination_port=req.destination_port,
                protocol=req.protocol,
                payload=req.payload,
                attack_type=attack_type,
                severity=severity,
                attacker_fingerprint=hashlib.sha256(f"{req.source_ip}{req.payload}".encode()).hexdigest()[:16]
            )

            self.interactions.append(interaction)

            # Update asset
            if req.asset_type == "honeypot" and req.asset_id in self.honeypots:
                honeypot = self.honeypots[req.asset_id]
                honeypot.last_interaction = interaction.timestamp
                honeypot.interactions_count += 1
                honeypot.detected_attacks.append(attack_type)

            elif req.asset_type == "honeytoken" and req.asset_id in self.honeytokens:
                honeytoken = self.honeytokens[req.asset_id]
                honeytoken.accessed_at = interaction.timestamp
                honeytoken.accessed_by = req.source_ip
                honeytoken.access_count += 1
                honeytoken.alert_triggered = True

            # Update metrics
            interactions_total.labels(
                asset_type=req.asset_type,
                attack_type=attack_type
            ).inc()
            attacks_detected.labels(severity=severity).inc()

            # Trigger active defense
            if severity in ["high", "critical"]:
                defense_action = self.execute_active_defense(interaction)
                return {
                    "status": "recorded",
                    "interaction": asdict(interaction),
                    "active_defense": asdict(defense_action) if defense_action else None
                }

            return {
                "status": "recorded",
                "interaction": asdict(interaction)
            }

        @self.app.get("/api/v1/interactions")
        async def list_interactions(
            asset_type: Optional[str] = None,
            severity: Optional[str] = None,
            limit: int = 100
        ):
            """List deception interactions"""
            interactions = self.interactions[-limit:]

            if asset_type:
                interactions = [i for i in interactions if i.asset_type == asset_type]
            if severity:
                interactions = [i for i in interactions if i.severity == severity]

            return {
                "interactions": [asdict(i) for i in interactions],
                "count": len(interactions)
            }

        @self.app.get("/api/v1/interactions/{interaction_id}")
        async def get_interaction(interaction_id: str):
            """Get specific interaction"""
            for interaction in self.interactions:
                if interaction.interaction_id == interaction_id:
                    return asdict(interaction)

            raise HTTPException(status_code=404, detail="Interaction not found")

        # Active defense
        @self.app.get("/api/v1/active-defense")
        async def list_active_defenses():
            """List active defense actions"""
            return {
                "actions": [asdict(ad) for ad in self.active_defenses],
                "count": len(self.active_defenses)
            }

        # Statistics
        @self.app.get("/api/v1/stats")
        async def get_stats():
            """Get deception platform statistics"""
            # Calculate attack type distribution
            attack_types = {}
            for interaction in self.interactions:
                attack_type = interaction.attack_type or "unknown"
                attack_types[attack_type] = attack_types.get(attack_type, 0) + 1

            # Calculate top attackers
            attackers = {}
            for interaction in self.interactions:
                attackers[interaction.source_ip] = attackers.get(interaction.source_ip, 0) + 1

            top_attackers = sorted(attackers.items(), key=lambda x: x[1], reverse=True)[:10]

            return {
                "total_honeypots": len(self.honeypots),
                "total_honeytokens": len(self.honeytokens),
                "total_interactions": len(self.interactions),
                "total_active_defenses": len(self.active_defenses),
                "attack_type_distribution": attack_types,
                "top_attackers": [{"ip": ip, "count": count} for ip, count in top_attackers],
                "honeypot_type_distribution": self.get_honeypot_distribution(),
                "honeytoken_type_distribution": self.get_honeytoken_distribution()
            }

        # Threat intelligence
        @self.app.get("/api/v1/threat-intel")
        async def get_threat_intel():
            """Get threat intelligence from deception assets"""
            # Extract IOCs
            malicious_ips = list(set(i.source_ip for i in self.interactions))
            attack_patterns = list(set(i.attack_type for i in self.interactions if i.attack_type))
            attacker_fingerprints = list(set(i.attacker_fingerprint for i in self.interactions if i.attacker_fingerprint))

            return {
                "malicious_ips": malicious_ips,
                "attack_patterns": attack_patterns,
                "attacker_fingerprints": attacker_fingerprints,
                "total_unique_attackers": len(malicious_ips),
                "collection_period": "last_7_days"
            }

        # Add Prometheus metrics endpoint
        metrics_app = make_asgi_app()
        self.app.mount("/metrics", metrics_app)

    def generate_honeytoken(self, token_type: HoneytokenType) -> str:
        """Generate a honeytoken value based on type"""
        if token_type == HoneytokenType.CREDENTIAL:
            return f"admin:{secrets.token_hex(16)}"
        elif token_type == HoneytokenType.API_KEY:
            return f"sk-{secrets.token_hex(32)}"
        elif token_type == HoneytokenType.AWS_KEY:
            return f"AKIA{secrets.token_hex(16).upper()}"
        elif token_type == HoneytokenType.DATABASE_RECORD:
            return f"user_id_{secrets.randbelow(10000)}"
        elif token_type == HoneytokenType.FILE:
            return f"/sensitive/data/{secrets.token_hex(8)}.txt"
        elif token_type == HoneytokenType.URL:
            return f"https://internal.company.com/secret/{secrets.token_hex(16)}"
        elif token_type == HoneytokenType.COOKIE:
            return f"session_{secrets.token_hex(32)}"
        else:
            return secrets.token_hex(32)

    def classify_attack(self, payload: str, port: int) -> str:
        """Classify attack type based on payload and port"""
        payload_lower = payload.lower()

        if "' or 1=1" in payload_lower or "union select" in payload_lower:
            return "sql_injection"
        elif "<script>" in payload_lower or "javascript:" in payload_lower:
            return "xss"
        elif "../" in payload or "..\\"\\ in payload:
            return "directory_traversal"
        elif "eval(" in payload_lower or "exec(" in payload_lower:
            return "code_injection"
        elif port == 22:
            return "ssh_brute_force"
        elif port == 3389:
            return "rdp_brute_force"
        elif "password" in payload_lower and port == 80:
            return "credential_stuffing"
        else:
            return "reconnaissance"

    def calculate_severity(self, attack_type: str) -> str:
        """Calculate severity based on attack type"""
        high_severity = ["sql_injection", "code_injection", "command_injection"]
        medium_severity = ["xss", "directory_traversal", "credential_stuffing"]

        if attack_type in high_severity:
            return "high"
        elif attack_type in medium_severity:
            return "medium"
        else:
            return "low"

    def execute_active_defense(self, interaction: DeceptionInteraction) -> Optional[ActiveDefense]:
        """Execute active defense action"""
        action_id = f"ad-{int(time.time() * 1000)}"

        # Choose defense action based on attack type
        if interaction.attack_type in ["sql_injection", "code_injection"]:
            action_type = "tarpit"
            description = f"Slow down attacker {interaction.source_ip} with tarpit"
        elif interaction.attack_type in ["ssh_brute_force", "rdp_brute_force"]:
            action_type = "block_ip"
            description = f"Block IP {interaction.source_ip} for 24 hours"
        else:
            action_type = "monitor"
            description = f"Enhanced monitoring of {interaction.source_ip}"

        defense = ActiveDefense(
            action_id=action_id,
            timestamp=datetime.utcnow(),
            action_type=action_type,
            target=interaction.source_ip,
            description=description,
            success=True,
            details={
                "interaction_id": interaction.interaction_id,
                "attack_type": interaction.attack_type,
                "severity": interaction.severity
            }
        )

        self.active_defenses.append(defense)
        active_defense_actions.labels(
            action_type=action_type,
            success=str(defense.success).lower()
        ).inc()

        return defense

    def get_honeypot_distribution(self) -> Dict[str, int]:
        """Get honeypot type distribution"""
        distribution = {}
        for hp in self.honeypots.values():
            distribution[hp.type] = distribution.get(hp.type, 0) + 1
        return distribution

    def get_honeytoken_distribution(self) -> Dict[str, int]:
        """Get honeytoken type distribution"""
        distribution = {}
        for ht in self.honeytokens.values():
            distribution[ht.type] = distribution.get(ht.type, 0) + 1
        return distribution

    def run(self, host: str = "0.0.0.0", port: int = 8089):
        """Run the service"""
        uvicorn.run(self.app, host=host, port=port)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8089"))
    service = DeceptionPlatform()
    service.run(port=port)
